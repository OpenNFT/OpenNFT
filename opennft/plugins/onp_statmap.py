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

# Stat Map
It is an example plugin, which demonstrates how one can access and process the activation map resulted from OpenNFT's iGLM. 
Its process method converts the 3D map into 2D mosaic for visualization, and if toDraw is set to True during initialization, then it also displays it.

N.B.: Displaying the activation map can significantly slows down plugin and OpenNFT!

__________________________________________________________________________
Copyright (C) 2016-2019 OpenNFT.org

Written by Tibor Auer

"""

from pyniexp.mlplugins import imageProcess
import matplotlib.pyplot as plt
import numpy as np
from functools import reduce

META = {
    "plugin_name": "Stat Map",
    "plugin_time": "t3",
    "plugin_init": "myImageProcess(({MatrixSizeX}, {MatrixSizeY}, {NrOfSlices}),toDraw=False)",
    "plugin_signal": "self.parent.eng.evalin('base','isfield(mainLoopData,\\\'tn\\\')')",
    "plugin_exec": "load_data(self.parent.eng.evalin('base','mainLoopData.tn.pos'))"
}

class myImageProcess(imageProcess):
    def __init__(self,image_dimension,toDraw=False):
        super().__init__(image_dimension,autostart=False)
        
        self.toDraw = toDraw
        if self.toDraw:
            self.figure = plt.figure(figsize=(10,10))
            self.axes = self.figure.add_axes((0,0,1,1))

        self.start_process()

    def __del__(self):
        if self.toDraw:
            plt.close(self.figure)
        
        super().__del__()

    def process(self,image):
        # Convert 3D to 2D mosaic
        (vx,vy,vz) = self._image_dimension
        [mxy, mxx] = getFactorPair(vz)
        tiles = image.reshape(vx,vy,mxx,mxy)
        tiles = np.moveaxis(np.rot90(tiles),[0,1,2,3],[1,3,0,2]).reshape(vx*mxx,vy*mxy)

        if self.toDraw:
            self.axes.imshow(tiles,cmap='jet')
            self.figure.canvas.draw()
            plt.pause(0.01)
    
def getFactorPair(n): # retrieve the pair of factors with the smalles difference   
    factorPairs = [[i, n//i] for i in range(1, int(n**0.5) + 1) if n % i == 0]
    factorPairDiff = [int(np.diff(p)) for p in factorPairs]
    return sorted(factorPairs[factorPairDiff.index(min(factorPairDiff))])
