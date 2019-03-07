# -*- coding: utf-8 -*-

# testing UDP
"""

__________________________________________________________________________
Copyright (C) 2016-2017 OpenNFT.org

Written by Tibor Auer
"""

from pyniexp.connection import Udp

UDP_IP = "127.0.0.1"
UDP_PORT = 1234
UDP_CONTROL_CHAR = '#'

sender = Udp(IP=UDP_IP,port=UDP_PORT,control_signal=UDP_CONTROL_CHAR)

sender.connect_for_sending()
sender.sending_time_stamp = True

sender.info()

for data in ['Bas',34.0,'NF',78.0]:
    sender.send_data(data)

sender.close()