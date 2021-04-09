# -*- coding: utf-8 -*-

# testing UDP
"""

__________________________________________________________________________
Copyright (C) 2016-2021 OpenNFT.org

Written by Tibor Auer
"""

from pyniexp.connection import Udp
import keyboard
from time import sleep
from random import uniform

UDP_IP = "127.0.0.1"
UDP_PORT = 1234
UDP_CONTROL_CHAR = '#'

sender = Udp(IP=UDP_IP,port=UDP_PORT,control_signal=UDP_CONTROL_CHAR)

sender.connect_for_sending()
sender.sending_time_stamp = True

sender.info()

while not(keyboard.is_pressed('q')):
    if keyboard.is_pressed('b'): 
        cond = 'Bas'
    if keyboard.is_pressed('n'): 
        cond = 'NF'
    if keyboard.is_pressed('f'): 
        cond = 'FB'

    sender.send_data(cond)
    val = float(uniform(-100,100))
    sender.send_data(val)
    print(cond,val)
    
    sleep(0.1)

sender.close()