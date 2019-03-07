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

receiver = Udp(IP=UDP_IP,port=UDP_PORT,control_signal=UDP_CONTROL_CHAR)

receiver.connect_for_receiving()
receiver.sending_time_stamp = True

receiver.info()

n = 0
cond = 'test'
while receiver.is_open:
    data = receiver.receive_data(n=1,dtype='float')
    if len(data) > 1:
        if type(data[1]) == str:
            cond = data[1]
            continue

        n += 1
        # if n == 1: receiver.ResetClock()
        receiver.log('volume #{:3d}, condition: {}, feedback: {} - {}'.format(n,cond,data[0],data[1]))
    elif receiver.is_open: receiver.log('volume #{:3d} no data!'.format(n))

receiver.close()