# coding=utf-8

"""
MR Scanner pulse trigger

__________________________________________________________________________
Copyright (C) 2016-2019 OpenNFT.org

Written by Artem Nikonorov

"""                                                       

import pythoncom, pyHook
import sys
import multiprocessing as mp, time
import numpy as np
from opennft.eventrecorder import Times

global pulses
global displayEvent
global recorder

def toNpData(mp_arr):
    np_arr = np.frombuffer(mp_arr.get_obj())
    return np_arr

def recordPulseEvent():
    global pulses
    global recorder
    # t0
    recorder.recordEvent(Times.t0, 0)

    t = time.time()
    np_arr = toNpData(pulses)
    counter = np_arr[0]
    counter += 1
    np_arr[counter] = t
    np_arr[0] = counter
    #print(toNpData(pulses))


def keypressed(event):
    global pulses
    global displayEvent
    if event.Ascii == 13:
        keys='<ENTER>'
    elif event.Ascii == 8:
        keys='<BACK SPACE>'
    elif event.Ascii == 9:
        keys='<TAB>'
        np_arr = toNpData(pulses)
        #counter = np_arr[0]
        #counter += 1
        #tmp = np_arr[counter]
        #np_arr[counter] = counter + 1
        #np_arr[counter] = tmp

        print(np_arr)
    elif event.Ascii == 35: # it is # sign
        recordPulseEvent()
        #displayEvent.set()

    elif event.Ascii == 27:
        np_arr = toNpData(pulses)
        print(pulses)
        print(np_arr)
        keys='<ESC>'
        sys.exit(0)
    else:
        #keys=chr(event.Ascii)
        keys=str(event.Ascii)

def setHook(pulses_,displayEvent_):
    global pulses
    global displayEvent
    displayEvent = displayEvent_
    counter = 0
    pulses = pulses_
    np_arr = toNpData(pulses)
    obj = pyHook.HookManager()
    obj.KeyDown = keypressed
    obj.HookKeyboard()
    pythoncom.PumpMessages()

def start(NrVolumes, ptbEvent, recorder_):
    global recorder
    recorder = recorder_
    pulses = mp.Array('d', [0] * ((NrVolumes + 1)))
    np_pulses = toNpData(pulses)
    np_pulses[0] = 0
    p = mp.Process(target=setHook, args=(pulses, ptbEvent,))
    p.start()
    #p.join()

    #print(toNpData(tvData))
    #print(tvData)
    return (p, pulses)

if __name__ == '__main__':
    start(12, 1)

