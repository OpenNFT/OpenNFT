# -*- coding: utf-8 -*-

"""
# Plugins
Plugins allow flexible modification and execution of OpenNFT without touching the core codebase. Plugins can access data, process them in a specific way, 
and they can be switched on and off according to the user's need.

Each plugin has to be a subclass of *Process class specified in pyniexp.mlplugins. It has to contain a header in a format of dictionary (called META) with prespecified keys:
- plugin_name: It is a freeform text which will be displayed in the plugin dialog and in the logs.
- plugin_time: It is a event timestamp as specified in opennft.eventrecorder. Times, and it determines the execution time of the plugin (so far only t3 is implemented)
- plugin_init: It is the initialization code of the plugin. "{}" can be used to refer to OpenNFT parameters as specified in the P parameter dictionary. It can be a list of 
commands, in which case, the first is run to create the object, and the rest are executed afterwards.
- plugin_signal: It is an expression returning to logical value, and it speicies the condition when the plugin can be executed.
- plugin_exec: It is the execution code of the plugin, and it is usually calls the plugin's load_data method to transfer some data to the plugin.

*Process classes pyniexp.mlplugins has an abstract/placeholder method called process, which should be overwritten to specify the operation on the data.
- the input to the process method of dataProcess (called data) is a one-dimensional numpy array
- the input to the process method of imageProcess (called image) is a multi-dimensional (usually 3D) numpy array as specified during initialization

# ROI step-wise GLM
This plugin demonstrates how to add you own approach (this one is a step-wise addition of each block) for ROI analysis.

__________________________________________________________________________
Copyright (C) 2016-2021 OpenNFT.org

Written by Tibor Auer

"""

from pyniexp.mlplugins import dataProcess, SIG_NOTSTARTED, SIG_RUNNING, SIG_STOPPED, SIG_NEWIMAGE
from loguru import logger
from multiprocessing import Value, RawArray
from numpy import array, meshgrid, savetxt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from os import path

META = {
    "plugin_name": "ROI step-wise GLM",
    "plugin_time": "t4", # according to opennft.eventrecorder.Times
    "plugin_init": [
        "ROIswGLM(int({NrROIs}),len({ProtNF}),r'{nfbDataFolder}')",
        "self.parent.eng.evalin('base','onp_roiswglm')"
    ],
    "plugin_signal": "self.parent.eng.evalin('base','isfield(mainLoopData,\\\'tmp_rawTimeSeriesAR1\\\')')",
    "plugin_exec": "load_data(self.parent.eng.evalin('base','onp_roiswglm'))",
}

class ROIswGLM(dataProcess):
    def __init__(self,nROIs,nBlocks,nfbDataFolder):
        super().__init__(nROIs*nBlocks,autostart=False)

        self.nfbDataFolder = nfbDataFolder
        self.nROIs = nROIs
        self.nBlocks = nBlocks

        self.rtdata = RawArray('d',[0]*self.nROIs*self.nBlocks*self.nBlocks)
        self.nData = Value('i',0)

        self.start_process()

    def process(self,data):
        if any(array(data) != 0):
            for r in data:
                self.rtdata[self.nData.value] = r
                self.nData.value += 1
        logger.info(('ROIs: [ ' + '{:.3f} '*len(data) + ']').format(*data))

    def finalize_process(self):
        dat = array(self.rtdata).reshape(self.nBlocks,self.nROIs,self.nBlocks)

        for b in range(0,self.nBlocks):
            fname = path.join(path.normpath(self.nfbDataFolder), 'ROIswGLM_{:02d}.txt'.format(b+1))
            savetxt(fname=fname, X=dat[b,:,0:b+1].transpose(), fmt='%.3f', delimiter=',')


        X,Y = meshgrid(self.nBlocks,self.nBlocks) 
        for r in range(0,self.nROIs):
            ax = plt.subplot(120+(r+1),projection='3d')
            ax.plot_surface(X,Y,dat[:,r,:])        
        plt.show()
