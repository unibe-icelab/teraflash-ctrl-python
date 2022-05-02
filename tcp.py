import os
import time
import platform
from thz_pulse import pulse
import socket
import subprocess  # For executing a shell command

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
gateway_address = ('169.254.84.101', 6341)

send_header = b'\xcd\xef\x124x\x9a\xfe\xdc\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x14'
recv_header = b'\xcd\xef\x124x\x9a\xfe\xdc\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x02'

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind(gateway_address)
    s.listen()
    conn, addr = s.accept()
    with conn:
        print(f"Connected by {addr}")
        print("sending...")
        payload = "cdef1234789afedc00000002000000000000001453595354454d203a2054454c4c20535441545553"
        payload = bytes.fromhex(payload)
        message = b'SYSTEM : TELL STATUS'
        message = send_header + message
        conn.send(payload)  # , socket.MSG_OOB | socket.MSG_DONTROUTE)
        while True:
            data = conn.recv(1024)
            if not data:
                continue
            print("received: ")
            data = data[len(recv_header):]
            print(data)
            print(data.decode("utf-8", "ignore"))
