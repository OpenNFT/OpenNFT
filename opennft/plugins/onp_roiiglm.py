# -*- coding: utf-8 -*-

"""
# Plugins
Plugins allow flexible modification and execution of OpenNFT without touching the core codebase. Plugins can access data, process them in a specific way,
and they can be switched on and off according to the user's need.

Each plugin has to be a subclass of *Process class specified in pyniexp.mlplugins. It has to contain a header in a format of dictionary (called META) with prespecified keys:
- plugin_name: It is a freeform text which will be displayed in the plugin dialog and in the logs.
- plugin_prot (optional): If specified, plugin is allowed only for certrain protocols. Multiple protocols can be specified as a semicolon-separated list.
- plugin_time: It is a event timestamp as specified in opennft.eventrecorder. Times, and it determines the execution time of the plugin (so far only t3 and t4 are implemented)
- plugin_init: It is the initialization code of the plugin. "{}" can be used to refer to OpenNFT parameters as specified in the P parameter dictionary.
- plugin_signal: It is an expression returning to logical value, and it speicies the condition when the plugin can be executed.
- plugin_exec: It is the execution code of the plugin, and it is usually calls the plugin's load_data method to transfer some data to the plugin.

*Process classes pyniexp.mlplugins has an abstract/placeholder method called process, which should be overwritten to specify the operation on the data.
- the input to the process method of dataProcess (called data) is a one-dimensional numpy array
- the input to the process method of imageProcess (called image) is a multi-dimensional (usually 3D) numpy array as specified during initialization

# ROI iGLM
This plugin demonstrates how volume-wise iGLM infomration for the ROIs can be extracted.

__________________________________________________________________________
Copyright (C) 2016-2021 OpenNFT.org

Written by Tibor Auer

"""  # noqa: E501

from pyniexp.mlplugins import dataProcess
from loguru import logger
from multiprocessing.sharedctypes import Value, Array
from ctypes import c_double
from numpy import array, savetxt
import matplotlib.pyplot as plt
from os import path

META = {
    "plugin_name": "ROI iGLM",
    "plugin_time": "t3",  # according to opennft.eventrecorder.Times
    "plugin_init": "ROIiGLM(int({NrROIs}),int({NrOfVolumes}),int({nrSkipVol}),r'{nfbDataFolder}')",
    "plugin_signal": "self.parent.eng.evalin('base','isfield(mainLoopData,\\\'tn\\\')')",
    "plugin_exec": "load_data(self.parent.eng.evalin('base','onp_extract_rois'))"
}


class ROIiGLM(dataProcess):
    def __init__(self, nROIs, nVols, nSkipVols, nfbDataFolder):
        super().__init__(nROIs, autostart=False)

        self.nfbDataFolder = nfbDataFolder
        self.nROIs = nROIs
        self.nVols = nVols

        self.rtdata = Array(c_double, [0]*self.nROIs*self.nVols)
        self.nData = Value('i', self.nROIs*nSkipVols)

        self.start_process()

    def process(self, data):
        for r in data:
            self.rtdata[self.nData.value] = r
            self.nData.value += 1
        logger.info(('ROIs: [ ' + '{:.3f} '*len(data) + ']').format(*data))

    def finalize_process(self):
        dat = array(self.rtdata).reshape(self.nVols, self.nROIs)

        fname = path.join(path.normpath(self.nfbDataFolder), 'ROIiGLM.csv')
        savetxt(fname=fname, X=dat, fmt='%.3f', delimiter=',')

        plt.plot(dat)
        plt.show()
