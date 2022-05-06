import socket
import numpy as np
import matplotlib.pyplot as plt

header = "cdef1234789afedc00000002"
send_header = b'\xcd\xef\x124x\x9a\xfe\xdc\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00'
recv_header = b'\xcd\xef\x124x\x9a\xfe\xdc\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x02'
r_dat_header = b'\xcd\xef\x124x\x9a\xfe\xdc\x00\x00\x00\x01\x00\xff\x91\xe7\x03\xe8\x00'

gateway_address = ('169.254.84.101', 6342)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.settimeout(10.0)
    s.bind(gateway_address)
    print(f"Starting server at address {gateway_address}")
    s.listen()
    client, addr = s.accept()
    print(f"Connected by client with address {addr}")
    while True:
        data = b""
        for i in range(5):
            data += client.recv(1460)[len(r_dat_header):]
        data += client.recv(760)[len(r_dat_header):]
        print(data)
        try:
            arr = np.frombuffer(data, dtype=np.int8)
            print(arr)
            print(arr.shape)
            plt.plot(range(len(arr)),arr)
            plt.show()
        except Exception as e:
            print(e)

message = b'SYSTEM : TELL STATUS'
message = send_header + message
print(message.hex())
print("cdef1234789afedc00000002000000000000001a4143515549534954494f4e203a20424547494e20313030302e30")
print(send_header.hex() + b"\x1a".hex() + b"ACQUISITION : BEGIN 1000.0".hex())
print(send_header.hex() + b"\x1a".hex() + b"ACQUISITION : BEGIN 1000.0".hex() == "cdef1234789afedc00000002000000000000001a4143515549534954494f4e203a20424547494e20313030302e30")


