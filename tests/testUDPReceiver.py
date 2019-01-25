# -*- coding: utf-8 -*-

# testing script for udpSender
"""

__________________________________________________________________________
Copyright (C) 2016-2019 OpenNFT.org

Written by Artem Nikonorov
"""

import socket
import select


UDP_IP = "127.0.0.1"
UDP_PORT = 1234
UDP_CONTROL_CHAR = '#'

receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
receiver.bind((UDP_IP, UDP_PORT))

data = [0]
while chr(data[0]) != UDP_CONTROL_CHAR:
    while len(select.select([receiver],[],[],0.001)[0]) == 0:
        pass
    data, addr = receiver.recvfrom(16)
    print(data)
print("Connection started from: ", addr[0])

data = [0]
while chr(data[0]) != UDP_CONTROL_CHAR:
    while len(select.select([receiver],[],[],0.001)[0]) == 0:
        pass
    data = receiver.recv(16)
    print(data)

print("Connection closed")
receiver.close()