# -*- coding: utf-8 -*-

"""
Event recorder class for performance estimation

__________________________________________________________________________
Copyright (C) 2016-2021 OpenNFT.org

Written by Artem Nikonorov, Yury Koush

"""

import time
import numpy as np
import enum

__all__ = ['Times', 'EventRecorder']


class Times(enum.IntEnum):
    # Events timestamps
    t0 = 0      # MR pulse time in online mode

    t1 = 1      # start file reading from the export folder in online mode
                # first non-zero time in online mode, if there is no trigger signal
    t2 = 2      # finish file reading from the export folder,
                # first non-zero time in offline mode
    t3 = 3      # end of prepossessing routine
    t4 = 4      # end of spatial-temporal data processing
    t5 = 5      # end of feedback computation
    t6 = 6      # begin of display instruction in Python Core process
    t7 = 7      # begin of display instruction in Python PtbScreen class
    t8 = 8      # begin of display feedback in Python PtbScreen class
    t9 = 9      # end of display instruction in Matlab PTB Helper
    t10 = 10    # end of display feedback in Matlab PTB Helper

    # optional timestamps
    # DCM special timestamps
    t11 = 11    # first DCM model computation started
    t12 = 12    # last DCM model computation is done

    # Events durations
    d0 = 13     # elapsed time per iteration


# ==============================================================================
class EventRecorder(object):
    """Recording events in time-vectors matrix
    """

    # --------------------------------------------------------------------------
    def __init__(self):
        # TODO: change to dataframe
        timeVectorLength = len(list(Times))
        self.records = np.zeros((1, timeVectorLength), dtype=np.float64)

    # --------------------------------------------------------------------------
    def initialize(self, NrOfVolumes):
        """
        """
        timeVectorLength = len(list(Times))
        self.records = np.zeros((NrOfVolumes + 1, timeVectorLength), dtype=np.float64)

    # --------------------------------------------------------------------------
    def recordEvent(self, position: Times, eventNumber, value=None):
        eventNumber = int(eventNumber)

        if not value:
            value = time.time()
        if eventNumber <= 0:
            eventNumber = int(self.records[0, position]) + 1

        self.records[eventNumber, position] = value
        self.records[0, position] = eventNumber

    # --------------------------------------------------------------------------
    def recordEventDuration(self, position: Times, eventNumber, duration):
        eventNumber = int(eventNumber)

        if eventNumber <= 0:
            eventNumber = int(self.records[0, position]) + 1

        self.records[eventNumber, position] = duration
        self.records[0, position] = eventNumber

    # --------------------------------------------------------------------------
    def getLastEvent(self, iteration=None):
        if iteration is None:
            iteration = [iteration for iteration, item in enumerate(self.records) if any(item != 0)][-1]
        return [index for index, item in enumerate(self.records[iteration]) if item == max(self.records[iteration])][-1]

    # --------------------------------------------------------------------------
    def savetxt(self, filename):
        np.savetxt(filename, self.records)
