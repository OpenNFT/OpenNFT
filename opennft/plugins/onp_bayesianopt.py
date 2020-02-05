# -*- coding: utf-8 -*-

"""
# Plugins
Plugins allow flexible modification and execution of OpenNFT without touching the core codebase. Plugins can access data, process them in a specific way, 
and they can be switched on and off according to the user's need.

Each plugin has to be a subclass of *Process class specified in pyniexp.mlplugins. It has to contain a header in a format of dictionary (called META) with prespecified keys:
- plugin_name: It is a freeform text which will be displayed in the plugin dialog and in the logs.
- plugin_time: It is a event timestamp as specified in opennft.eventrecorder. Times, and it determines the execution time of the plugin (so far only t3 is implemented)
- plugin_init: It is the initialization code of the plugin. "{}" can be used to refer to OpenNFT parameters as specified in the P paremeter dictionary.
- plugin_signal: It is an expression returning to logical value, and it speicies the condition when the plugin can be executed.
- plugin_exec: It is the execution code of the plugin, and it is usually calls the plugin's load_data method to transfer some data to the plugin.

*Process classes pyniexp.mlplugins has an abstract/placeholder method called process, which should be overwritten to specify the operation on the data.
- the input to the process method of dataProcess (called data) is a one-dimensional numpy array
- the input to the process method of imageProcess (called image) is a multi-dimensional (usually 3D) numpy array as specified during initialization

# Bayesian Optimisation
This plugin is part of a project using real-time fMRI to inform non-invasive brain stimulation as outlined by Violante, Leech, and Lorenz (2019), IEEE Brain.

N.B.:The plugin is under active development.

__________________________________________________________________________
Copyright (C) 2016-2019 OpenNFT.org

Written by Tibor Auer

"""

from pyniexp.mlplugins import dataProcess, SIG_NOTSTARTED, SIG_RUNNING, SIG_STOPPED, SIG_NEWIMAGE
from loguru import logger


META = {
    "plugin_name": "Bayesian Optimisation",
    "plugin_time": "t3", # according to opennft.eventrecorder.Times
    "plugin_init": "BOengine(int({NrROIs}))",
    "plugin_signal": "self.eng.evalin('base','isfield(mainLoopData,\\\'tn\\\')')",
    "plugin_exec": "load_data(self.eng.evalin('base','onp_extract_rois')._data.tolist())"
}

class BOengine(dataProcess):
    def __init__(self,nROIs):
        super().__init__(nROIs)

    def process(self,data):
        logger.info(('ROIs: [ ' + '{:.3f} '*len(data) + ']').format(*data))
