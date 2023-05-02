import time

import numpy as np
import platform
from scipy.fft import rfft, rfftfreq
import socket
import subprocess  # For executing a shell command
import logging
import queue


class TopticaSocket:
    def __init__(self, ip, data):
        self.send_header = b'\xcd\xef\x124x\x9a\xfe\xdc\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00'
        self.r_stat_header = b'\xcd\xef\x124x\x9a\xfe\xdc\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x02'
        self.r_dat_header = b'\xcd\xef\x124x\x9a\xfe\xdc\x00\x00\x00\x01\x00'
        self.config_server_address = (ip, 6341)
        self.data_server_address = (ip, 6342)
        self.range = 50
        self.running = True
        self.status = ""
        self._data = data

    def wait_for_answer(self, client, length=1024):
        while self.running:
            data = client.recv(length)
            if data:
                if "OK" in data.decode("utf-8", "ignore"):
                    return 1
                elif "MON" in data.decode("utf-8", "ignore"):
                    return 1
            else:
                logging.error("[TCP CONF] Client terminated with FIN.")
                return 0

    def run_conf_tcp(self, cmd_queue):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(self.config_server_address)
            logging.info(f"[TCP CONF] Starting server at address {self.config_server_address}")
            s.listen()
            client, addr = s.accept()
            logging.info(f"[TCP CONF] Connected by client with address {addr}")

            while self.running:

                # check the queue for commands
                cmd = cmd_queue.get()
                if cmd:
                    (b, s) = cmd
                    message = self.send_header + b + s.encode()
                    client.send(message)
                    if b == b'0x14':
                        # if we request the status, save the response
                        while self.running:
                            self.status = client.recv(1024).decode("utf-8", "ignore")
                        print(self.status)
                    elif "RANGE" in s:
                        self.range = float(s[-6:])
                    else:
                        if self.wait_for_answer(client) == 0:
                            return
                else:
                    # just to a simple heartbeat
                    b, c = (b'\x12', "SYSTEM : MONITOR 1")
                    message = self.send_header + b + s.encode()
                    client.send(message)
                    if self.wait_for_answer(client) == 0:
                        return
                time.sleep(0.25)

    def ping(self, host):
        res = False
        ping_param = "-n" if platform.system().lower() == "windows" else "-c"
        command = ['ping', ping_param, '1', host]
        result = subprocess.call(command)
        logging.debug(result)
        if result == 0:
            res = True
        return res

    def run_tcp_dat(self):
        types = np.dtype([
            ("signal_1", np.int16),
            ("reserved_1", np.int16),
            ("signal_2", np.int16),
            ("reserved_2", np.int16),
        ])
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(self.data_server_address)
            logging.info(f"[TCP DAT] Starting server at address {self.data_server_address}")
            s.listen()
            client, addr = s.accept()
            logging.info(f"[TCP DAT] Connected by client with address {addr}")
            old_range = self.range
            while self.running:
                if old_range != self.range:
                    # range has changed and needs to be adjusted
                    pass

                old_range = self.range

                raw_data = client.recv(2 * 4 * (20 * self.range + 1) + 52)

                if not raw_data:
                    continue

                if raw_data[:len(self.r_dat_header)] == self.r_dat_header:
                    data = raw_data[len(self.r_dat_header) + 47:]
                else:
                    try:
                        data = raw_data.split(self.r_dat_header)[1][47:]
                    except IndexError:
                        continue
                while True:
                    if len(data) != 2 * 4 * (20 * self.range + 1):
                        data = data + client.recv(2 * 4 * (20 * self.range + 1) - len(data))
                    else:
                        break
                try:
                    types = types.newbyteorder('>')
                    arr = np.frombuffer(data, dtype=types)
                    self._data.signal_1 = arr['signal_1'] / 20.0 - arr['signal_1'][0] / 20.0
                    self._data.signal_2 = arr['signal_2'] / 20.0 - arr['signal_2'][0] / 20.0

                    t = self._data.time
                    p = self._data.signal_1
                    sample_rate = len(t) / (t[-1] - t[0]) * 1e12
                    n = len(p)
                    a = rfft(p)
                    f = rfftfreq(n, 1 / sample_rate)
                    self._data.freq_1 = f / 1e12
                    self._data.freq_1_amp = np.abs(a)
                except Exception as e:
                    logging.error(e)
                    logging.error(f"{len(data)=}")
