# -*- coding: utf-8 -*-

# testing script for udpSender
"""

__________________________________________________________________________
Copyright (C) 2016-2017 OpenNFT.org

Written by Artem Nikonorov
"""

import socket
from time import sleep

UDP_IP = "127.0.0.1"
UDP_PORT = 5077
UDP_CONTROL_CHAR = '#'

# Initialise
udpSender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#data = "HI\n"
data = UDP_CONTROL_CHAR
#self.printToLog(data)
data = bytes(data, 'UTF-8')
udpSender.sendto(data, (UDP_IP, UDP_PORT))

# Send
for data in [12, 34, 56, 78, 90]:
    sleep(0.01)
    data = bytes(str(data), 'UTF-8')
    udpSender.sendto(data, (UDP_IP, UDP_PORT))    
    print("Sent message: ", data)

# Finalize
#data = "BYE\n"
data = UDP_CONTROL_CHAR
#self.printToLog(data)
data = bytes(data, 'UTF-8')
udpSender.sendto(data, (UDP_IP, UDP_PORT))
udpSender.close()
udpSender = None