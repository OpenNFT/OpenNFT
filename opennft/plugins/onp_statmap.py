from pyniexp.mlplugins import imageProcess
import matplotlib.pyplot as plt
import numpy as np

META = {
    "plugin_name": "Stat Map",
    "plugin_time": "t3", # according to opennft.eventrecorder.Times
    "plugin_init": "myImageProcess(({MatrixSizeX}, {MatrixSizeY}, {NrOfSlices}),toDraw=False)", # Setting toDraw to True significantly slows down plugin update
    "plugin_signal": "self.eng.evalin('base','isfield(mainLoopData,\\\'tn\\\')')",
    "plugin_exec": "load_data(self.eng.evalin('base','mainLoopData.tn.pos')._data.tolist())"
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
        mxy = int(np.ceil(np.sqrt(vz)))
        tiles = image.reshape(vx,vy,mxy,mxy)
        tiles = np.moveaxis(np.rot90(tiles),[0,1,2,3],[1,3,0,2]).reshape(vx*mxy,vy*mxy)

        if self.toDraw:
            self.axes.imshow(tiles,cmap='jet')
            self.figure.canvas.draw()
            plt.pause(0.01)