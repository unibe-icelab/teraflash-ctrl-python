import os
import time
import platform
from thz_pulse import pulse
import socket
import subprocess  # For executing a shell command


class TCPserver:

    def __init__(self):
        self.gateway_address = ('169.254.84.101', 6341)

        self.send_header = b'\xcd\xef\x124x\x9a\xfe\xdc\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00'
        self.r_stat_header = b'\xcd\xef\x124x\x9a\xfe\xdc\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x02'
        self.r_dat_header = b'\xcd\xef\x124x\x9a\xfe\xdc\x00\x00\x00\x01\x00\xff\x91\xe7\x03\xe8\x00'

        self.cmds = [
            (b'\x14', "SYSTEM : TELL STATUS"),
            (b'\x0b', "CHANNEL : D"),
            (b'\x0f', "MOTION : NORMAL"),
            (b'\x16', "TRANSMISSION : SLIDING"),
            (b'\x11', "SYSTEM : TIA ATN2"),
            (b'\x1a', "ACQUISITION : BEGIN 1000.0"),
            (b'\x17', "ACQUISITION : AVERAGE 2"),
            (b'\x12', "ACQUISITION : STOP"),
            (b'\x18', "ACQUISITION : RANGE 0.00"),
            (b'\x17', "ACQUISITION : RESET AVG"),
            (b'\x19', "ACQUISITION : RANGE 50.00"),
            (b'\x12', "SYSTEM : MONITOR 1"),
            (b'\x11', "MON 1: -0.024058"),
            (b'\x0a', "LASER : ON"),
            (b'\x0a', "VOLT1 : ON"),
            (b'\x13', "ACQUISITION : START"),
        ]

    def wait_for_answer(self, client, length=1024):
        while True:
            data = client.recv(length)
            if data:
                print(data.decode("utf-8", "ignore"))
                if "OK" in data.decode("utf-8", "ignore"):
                    return

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(self.gateway_address)
            s.listen()
            conn, addr = s.accept()
            print(f"Connected by {addr}")
            with conn:
                for cmd in self.cmds:
                    b, c = cmd
                    print(f"sending: {b} {c}")
                    message = self.send_header + b + c.encode()
                    conn.send(message)
                    self.wait_for_answer(conn)
                self.wait_for_answer(conn, 2048)
                return


if __name__ == "__main__":
    server = TCPserver()
    server.run()
