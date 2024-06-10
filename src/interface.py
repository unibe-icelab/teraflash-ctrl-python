import time
from queue import Queue, Empty
import threading

import numpy as np
import platform
from scipy.fft import rfft, rfftfreq
import socket
import subprocess
import logging

from math_utils import get_fft, toptica_window


class DataContainer:

    def __init__(self, n=1000):
        """
            Data container that stores the data sent by the instrument
        Args:
            n: length of dataset (depends on the selected range)
        """
        self.time = np.zeros(n)
        self.freq = np.zeros(n)

        self.signal_1 = np.zeros(n)
        self.fft_1_amp = np.zeros(n)
        self.fft_1_phase = np.zeros(n)

        self.signal_2 = np.zeros(n)
        self.fft_2_amp = np.zeros(n)
        self.fft_2_phase = np.zeros(n)


# global variables for thread communication
data = DataContainer()
status = ""


class TopticaSocket:
    def __init__(self,
                 ip: str,
                 running: threading.Event,
                 connected: threading.Event,
                 cmd_ack: threading.Event,
                 buffer_emptied: threading.Event,
                 range_changed: threading.Event,
                 acq_running: threading.Event):
        """
            TCP Socket struct, used for the communication between the server (Computer) and the client (instrument)
            with two TCP connections (one for configuration and one for data transmission)
        Args:
            ip: ip address
            running: threading event that signals if the application is running
            connected: threading event that signals if a client is connected
            cmd_ack: threading event that signals when a command is acknowledged
            range_changed: threading event that signals when the range has been changed in the configuration
        """
        self.send_header = b'\xcd\xef\x124x\x9a\xfe\xdc\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00'
        self.r_stat_header = b'\xcd\xef\x124x\x9a\xfe\xdc\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x02'
        self.r_dat_header = b'\xcd\xef\x124x\x9a\xfe\xdc\x00\x00\x00\x01\x00\t\x1a\xe6\x03\xe8\x00\x00\x04L\x00\x00\x0c\xcc\xcc\xcc\x00\x00\x16\x0b\x00\x00]\xd8\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x00'
        self.r_dat_header = b'\xcd\xef\x124x\x9a\xfe'
        self.full_data_header_len = 52
        self.read_header_len = 19
        self.data_header_len = 7

        self.avg_countdown = 0

        self.config_server_address = (ip, 6341)
        self.data_server_address = (ip, 6342)

        self.t_begin = 1000.00
        self.range = 50

        self.running = running
        self.connected = connected
        self.cmd_ack = cmd_ack
        self.range_changed = range_changed
        self.buffer_emptied = buffer_emptied
        self.acq_running = acq_running

        if not self.ping(ip):
            raise ConnectionError

    @staticmethod
    def ping(host: str):
        """
            determines whether a device is connected or not
        Args:
            host: IP address as a string

        Returns: True for connected, False for not connected

        """
        res = False
        ping_param = "-n" if platform.system().lower() == "windows" else "-c"
        command = ['ping', ping_param, '1', host]
        result = subprocess.call(command)
        if result == 0:
            res = True
        return res

    def wait_for_answer(self, client: socket, length: int = 1024):
        """
            waits for the device to acknowledge the previously sent command
        Args:
            client: socket object
            length: length of the buffer

        Returns: True for valid response, False for error

        """
        while self.running.is_set():
            _data = client.recv(length)[self.read_header_len:]
            if _data:
                _data_decoded = _data.decode("utf-8", "ignore")
                if "OK" in _data_decoded:
                    logging.debug(f"[TCP CONF] received: {_data_decoded}")
                    return True
                elif "MON" in _data_decoded:
                    return True
                logging.debug(f"[TCP CONF] received: {_data_decoded}")
            else:
                logging.error(f"[TCP CONF] No valid reply from device: {_data.decode('utf-8', 'ignore')}")
                return False

    def run_conf_tcp(self, cmd_queue: Queue):
        """
            Config TCP thread on port 6341. This handles all the configurations for the device.
        Args:
            cmd_queue: Queue from main thread with all the interactive

        Returns:

        """
        global status
        global data
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # Set the SO_REUSEADDR option to allow reuse of the port
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # bind server to the address (only works when the address exists)
            s.bind(self.config_server_address)
            logging.info(f"[TCP CONF] Starting server at address {self.config_server_address}")
            # wait for connections
            s.listen()
            # accept connection from device
            client, addr = s.accept()
            logging.info(f"[TCP CONF] Connected by client with address {addr}")
            # now we are connected
            self.connected.set()

            while self.running.is_set():
                # check the queue for commands
                try:
                    cmd = cmd_queue.get(block=False)
                    logging.debug(f"[TCP CONF] sending: {cmd}")
                    (b, c) = cmd
                    message = self.send_header + b + c.encode()
                    # send command
                    client.send(message)
                    if b == b'\x14':
                        # if we request the status, save the response
                        status = client.recv(1024)[self.read_header_len:].decode("utf-8", "ignore")
                        self.cmd_ack.set()
                    elif "RANGE" in c:
                        # if we change the range, also change it for the data thread
                        parts = c.split(" ")
                        self.range = float(parts[-1])
                        data.time = np.linspace(self.t_begin, self.t_begin + self.range, 20 * int(self.range) + 1)
                        # wait for acknowledge
                        if not self.wait_for_answer(client):
                            return
                        self.cmd_ack.set()
                    elif "BEGIN" in c:
                        # if we change the range, also change it for the data thread
                        parts = c.split(" ")
                        self.t_begin = float(parts[-1])
                        data.time = np.linspace(self.t_begin, self.t_begin + self.range, 20 * int(self.range) + 1)
                        # wait for acknowledge
                        if not self.wait_for_answer(client):
                            return
                        self.cmd_ack.set()
                    else:
                        # wait for acknowledge
                        if not self.wait_for_answer(client):
                            return
                        self.cmd_ack.set()
                except Empty:
                    # just to a simple heartbeat
                    (b, c) = (b'\x12', "SYSTEM : MONITOR 1")
                    message = self.send_header + b + c.encode()
                    client.send(message)
                    # wait for acknowledge
                    if not self.wait_for_answer(client):
                        return
                time.sleep(0.25)

    def run_tcp_dat(self, cmd_queue: Queue):
        """
            Data TCP thread on port 6342. This handles receives all the streamed data from the device and decodes it.
        """
        global data
        types = np.dtype([
            ("signal_1", np.int16),
            ("reserved_1", np.int16),
            ("signal_2", np.int16),
            ("reserved_2", np.int16),
        ])

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # Set the SO_REUSEADDR option to allow reuse of the port
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # bind server to the address (only works when the address exists)
            s.bind(self.data_server_address)
            logging.info(f"[TCP DAT] Starting server at address {self.data_server_address}")
            # wait for connections
            s.listen()
            # accept connection from device
            client, addr = s.accept()
            logging.info(f"[TCP DAT] Connected by client with address {addr}")
            # now we are connected
            while self.running.is_set():
                if self.range_changed.is_set():
                    # range has changed and needs to be adjusted
                    # need to empty the read buffer
                    client.settimeout(2)
                    while self.running.is_set():
                        try:
                            client.recv(32100)
                        except socket.timeout:
                            break
                    client.settimeout(None)
                    self.buffer_emptied.set()
                    self.range_changed.clear()

                # data always comes in the shape of 4 datasets each as 16bit ints with length of
                # (20 * self.range + 1)
                # the header is 52 8 bit ints and since we read 8 bit ints we need to multiply the data by 2
                if self.range_changed.is_set():
                    continue
                if not self.acq_running.is_set():
                    # no data received
                    time.sleep(1.0)
                    continue
                raw_data = client.recv(2 * 4 * (20 * int(self.range) + 1) + self.full_data_header_len)
                if not raw_data:
                    # no data received
                    time.sleep(1.0)
                    continue

                if raw_data[:self.data_header_len] != self.r_dat_header:
                    continue

                if len(raw_data) != 2 * 4 * (20 * int(self.range) + 1) + self.full_data_header_len:
                    skip_this = False
                    while self.running.is_set():
                        to_append = client.recv(
                            2 * 4 * (20 * int(self.range) + 1) + self.full_data_header_len - len(raw_data))
                        raw_data += to_append
                        if len(raw_data) == 2 * 4 * (20 * int(self.range) + 1) + self.full_data_header_len:
                            break
                        if len(raw_data) == 2 * 4 * (20 * int(self.range) + 1) + self.full_data_header_len:
                            skip_this = True
                            break
                    if skip_this:
                        continue

                # TODO: the following code is not properly implemented yet, we need
                # to check how we handle it, if the data comes not in the proper packet length

                _data = raw_data[self.full_data_header_len:]

                # check if header is at the beginning of the received payload
                # if raw_data[:self.data_header_len] == self.r_dat_header:
                #     # remove the header
                #     _data = raw_data[self.data_header_len:]
                # else:
                #     _data = raw_data[self.data_header_len:]
                #     # print("header not in the beginning")
                #     while self.running.is_set():
                #         logging.info("data does not have correct length...")
                #
                #         # check if the data is of the correct length
                #         if len(_data) != 2 * 4 * (20 * self.range + 1):
                #             _data = _data + client.recv(2 * 4 * (20 * int(self.range) + 1) - len(_data))
                #         else:
                #             break
                try:
                    # decode received payload to 16 bit ints
                    types = types.newbyteorder('>')
                    arr = np.frombuffer(_data, dtype=types)

                    data.signal_1 = arr['signal_1'] / 20.0 - arr['signal_1'][0] / 20.0
                    data.signal_2 = arr['signal_2'] / 20.0 - arr['signal_2'][0] / 20.0

                    # do fft of signal 1
                    pulse = data.signal_1 * toptica_window(data.time)
                    f, a, arg = get_fft(data.time, pulse)
                    data.freq = f
                    data.fft_1_amp = a / np.max(a)
                    data.fft_1_phase = arg

                    # do fft of signal 2
                    pulse = data.signal_2 * toptica_window(data.time)
                    f, a, arg = get_fft(data.time, pulse)
                    data.fft_2_amp = a / np.max(a)
                    data.fft_2_phase = arg

                    # update avg countdown
                    if self.avg_countdown > 0:
                        self.avg_countdown -= 1

                except Exception as e:
                    logging.error(e)
                    logging.error(f"{len(data.signal_1)=}")
