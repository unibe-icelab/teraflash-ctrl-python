import numpy as np
import os
import time
import platform
from thz_pulse import pulse
from scipy.fft import rfft, rfftfreq
import matplotlib.pyplot as plt
import socket
import subprocess  # For executing a shell command

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
gateway_address = ('169.254.84.101', 6341)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind(gateway_address)
    s.listen()
    conn, addr = s.accept()
    with conn:
        print(f"Connected by {addr}")
        print("sending...")
        payload = [0xcd, 0xef, 0x12, 0x34, 0x78, 0x9a, 0xfe, 0xdc, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00,
                   0x00, 0x00, 0x14, 0x53, 0x59, 0x53, 0x54, 0x45, 0x4d, 0x20, 0x3a, 0x20, 0x54, 0x45, 0x4c, 0x4c, 0x20,
                   0x53, 0x54, 0x41, 0x54, 0x55, 0x53]
        payload = [0x34, 0x78, 0x9a, 0xfe, 0xdc, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00,
                   0x00, 0x00, 0x14, 0x53, 0x59, 0x53, 0x54, 0x45, 0x4d, 0x20, 0x3a, 0x20, 0x54, 0x45, 0x4c, 0x4c, 0x20,
                   0x53, 0x54, 0x41, 0x54, 0x55, 0x53]
        payload = "".join(map(chr, payload))
        payload = payload.encode('utf8')
        print(len(payload))
        print(payload.decode("UTF-8"))

        payload = "cdef1234789afedc00000002000000000000001453595354454d203a2054454c4c20535441545553"
        payload = bytes.fromhex(payload)
        # payload = b"SYSTEM : TELL STATUS"
        conn.send(payload) #, socket.MSG_OOB | socket.MSG_DONTROUTE)
        while True:
            data = conn.recv(1026)
            if not data:
                pass
