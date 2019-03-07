# -*- coding: utf-8 -*-

# testing script for udpSender
"""

__________________________________________________________________________
Copyright (C) 2016-2019 OpenNFT.org

Written by Artem Nikonorov
"""

import socket
from time import sleep

UDP_IP = "127.0.0.1"
UDP_PORT = 1234

receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
receiver.bind((UDP_IP, UDP_PORT))

while True:
    sleep(0.01)
    data, addr = receiver.recvfrom(1024)
    print("Received message: ", data)