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

udpSender = Udp(IP=UDP_IP,port=UDP_PORT,controlChar=UDP_CONTROL_CHAR)

udpSender.ConnectForSending()

udpSender.SendData([12,34,56,78])

udpSender.Close()