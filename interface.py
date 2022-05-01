import numpy as np
import os
import time
import platform
from thz_pulse import pulse
from scipy.fft import rfft, rfftfreq
import matplotlib.pyplot as plt
import socket
import subprocess  # For executing a shell command


class TopticaSocket:
    def __init__(self):
        ip = "169.254.84.148"
        ip = "tf5-1700v.local"
        if not self.ping(ip):
            raise Exception("[ERROR] ping timeout! Check LAN connection.")
        TFReadPort = (ip, 61235)
        self.TFWritePort = (ip, 61234)
        self.write_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.write_socket.bind(("", 61237))
        self.read_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.read_socket.bind(TFReadPort)
        self.get_laser_status()

    def ping(self, host):
        res = False
        ping_param = "-n" if platform.system().lower() == "windows" else "-c"
        command = ['ping', ping_param, '1', host]
        result = subprocess.call(command)
        print(result)
        if result == 0:
            res = True
        return res

    def get_laser_status(self):
        msgFromClient = "RD-LASER"
        bytesToSend = str.encode(msgFromClient)
        self.write_socket.sendto(bytesToSend, self.TFWritePort)
        print("waiting for response...")
        msgFromServer = self.read_socket.recvfrom(1024)
        print(msgFromServer)

    def read(self):
        t = np.linspace(-4, 4, 10000)
        p = pulse(t)

        SAMPLE_RATE = len(t) / (t[-1] - t[0]) * 1e12
        N = len(p)
        a = rfft(p)
        f = rfftfreq(N, 1 / SAMPLE_RATE)
        return t, p, f / 1e12, np.abs(a)


if __name__ == "__main__":
    socket = TopticaSocket()
    exit()
    t, p, f, a = socket.read()
    fig, (ax1, ax2) = plt.subplots(2, 1)
    ax1.plot(t, p)
    ax2.plot(f, a)
    ax2.set_xlim(0, 10)
    plt.show()
