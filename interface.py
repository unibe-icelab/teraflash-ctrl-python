import numpy as np
import os
import time
import platform
from thz_pulse import pulse
from scipy.fft import rfft, rfftfreq
import matplotlib.pyplot as plt
import socket
import subprocess  # For executing a shell command
import threading
import logging


class TopticaConfigSocket:
    def __init__(self, dataclass):
        self.r_dat_header = b'\xcd\xef\x124x\x9a\xfe\xdc\x00\x00\x00\x01\x00\xff\x91\xe7\x03\xe8\x00\x00'
        self.send_header = b'\xcd\xef\x124x\x9a\xfe\xdc\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00'
        self.r_stat_header = b'\xcd\xef\x124x\x9a\xfe\xdc\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x02'
        self.r_dat_header = b'\xcd\xef\x124x\x9a\xfe\xdc\x00\x00\x00\x01\x00\xff\x91\xe7\x03\xe8\x00'
        self._dataclass = dataclass
        self._dataclass.time = np.linspace(2070, 2070 + 50, 1000)

        self.setup_cmds = [
            (b'\x14', "SYSTEM : TELL STATUS"),
            (b'\x0b', "CHANNEL : D"),
            (b'\x0f', "MOTION : NORMAL"),
            (b'\x16', "TRANSMISSION : SLIDING"),
            (b'\x11', "SYSTEM : TIA ATN2"),
            (b'\x1a', "ACQUISITION : BEGIN 2070.0"),
            # (b'\x1a', "ACQUISITION : BEGIN 1000.0"),
            (b'\x17', "ACQUISITION : AVERAGE 2"),
            (b'\x12', "ACQUISITION : STOP"),
            (b'\x18', "ACQUISITION : RANGE 0.00"),
            (b'\x17', "ACQUISITION : RESET AVG"),
            (b'\x19', "ACQUISITION : RANGE 50.00"),
            (b'\x12', "SYSTEM : MONITOR 1"),
            (b'\x0a', "LASER : ON"),
            (b'\x0a', "VOLT1 : ON"),
            (b'\x13', "ACQUISITION : START"),
        ]

        ip = "169.254.84.101"
        # ip = "localhost"
        self.config_server_adress = (ip, 6341)

    def wait_for_answer(self, client, length=1024):
        while True:
            data = client.recv(length)
            if data:
                logging.debug("Received: " + data.decode("utf-8", "ignore"))
                logging.debug(data[len(self.r_stat_header):].decode("utf-8", "ignore"))
                if "OK" in data.decode("utf-8", "ignore"):
                    return 1
                elif "MON" in data.decode("utf-8", "ignore"):
                    return 1
            else:
                logging.error("Client termianted with FIN.")
                return 0

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(self.config_server_adress)
            logging.info(f"Starting server at address {self.config_server_adress}")
            s.listen()
            client, addr = s.accept()
            logging.debug(f"Connected by client with address {addr}")
            for cmd in self.setup_cmds:
                b, c = cmd
                logging.debug(f"Sending: {b} {c}")
                message = self.send_header + b + c.encode()
                client.send(message)
                if self.wait_for_answer(client) == 0:
                    return
            while True:
                b, c = (b'\x12', "SYSTEM : MONITOR 1")
                message = self.send_header + b + c.encode()
                client.send(message)
                if self.wait_for_answer(client) == 0:
                    return


class TopticaDataSocket:
    def __init__(self, dataclass):
        self.r_dat_header = b'\xcd\xef\x124x\x9a\xfe\xdc\x00\x00\x00\x01\x00\xff\x91\xe7\x03\xe8\x00'
        self.r_dat_header = b'\xcd\xef\x124x\x9a\xfe\xdc\x00\x00\x00\x01\x00'
        self._dataclass = dataclass

        ip = "169.254.84.101"
        # ip = "localhost"
        self.data_server_adress = (ip, 6342)
        if not self.ping(ip):
            raise Exception("[ERROR] ping timeout! Check LAN connection.")

    def ping(self, host):
        res = False
        ping_param = "-n" if platform.system().lower() == "windows" else "-c"
        command = ['ping', ping_param, '1', host]
        result = subprocess.call(command)
        print(result)
        if result == 0:
            res = True
        return res

    def read(self):
        types = np.dtype([
            ("signal_1", np.int16),
            ("ref_1", np.int16),
            ("signal_2", np.int16),
            ("ref_2", np.int16),
        ])
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(self.data_server_adress)
            print(f"Starting server at address {self.data_server_adress}")
            s.listen()
            client, addr = s.accept()
            print(f"Connected by client with address {addr}")
            while True:
                raw_data = client.recv(8060)

                if not raw_data:
                    continue

                if raw_data[:len(self.r_dat_header)] == self.r_dat_header:
                    data = raw_data[len(self.r_dat_header) + 47:]
                else:
                    print("not at the beginning")
                    print(self.r_dat_header)
                    print(raw_data)
                    print(raw_data.split(self.r_dat_header))
                    try:
                        data = raw_data.split(self.r_dat_header)[1][47:]
                    except IndexError:
                        continue
                    print(data)
                print(f"data length before: {len(data)} {4 * 2 * 1000}")
                if len(data) != 8000:
                    data = data + client.recv(8000 - len(data))
                print(f"data length after: {len(data)} {4 * 2 * 1000}")
                print("sanity check: ", self.r_dat_header in data)
                print(data)
                try:
                    types = types.newbyteorder('>')
                    arr = np.frombuffer(data, dtype=types)
                    self._dataclass.signal_1 = arr['signal_1']
                    self._dataclass.ref_1 = arr['ref_1']
                    self._dataclass.signal_2 = arr['signal_2']
                    self._dataclass.ref_2 = arr['ref_2']

                    t = self._dataclass.time
                    p = self._dataclass.signal_1
                    SAMPLE_RATE = len(t) / (t[-1] - t[0]) * 1e12
                    N = len(p)
                    a = rfft(p)
                    f = rfftfreq(N, 1 / SAMPLE_RATE)
                    self._dataclass.freq_1 = f / 1e12
                    self._dataclass.freq_1_amp = np.abs(a)
                except Exception as e:
                    print(e)

        # t = np.linspace(-4, 4, 10000)
        # p = pulse(t)
        #
        # SAMPLE_RATE = len(t) / (t[-1] - t[0]) * 1e12
        # N = len(p)
        # a = rfft(p)
        # f = rfftfreq(N, 1 / SAMPLE_RATE)
        # return t, p, f / 1e12, np.abs(a)


if __name__ == "__main__":
    conf = TopticaConfigSocket()
    dat = TopticaDataSocket()
