from opennft import mlproc
from pyniexp.mlplugins import imageProcess
import matplotlib.pyplot as plt
import numpy as np
from time import sleep

META = {
    "plugin_name": "Stat Map",
    "plugin_time": "t3", # according to opennft.eventrecorder.Times
    "plugin_init": "myImageProcess(({MatrixSizeX}, {MatrixSizeY}, {NrOfSlices}))",
    "plugin_signal": "self.eng.evalin('base','isfield(mainLoopData,\\\'tn\\\')')",
    "plugin_exec": "load_image(self.eng.evalin('base','mainLoopData.tn')._data.tolist())"
}

class myImageProcess(imageProcess):
    def __init__(self,image_dimension):
        super().__init__(image_dimension,autostart=False)
        self.figure = plt.figure(figsize=(10,10))
        self.figure.add_axes()
        self.figure.canvas.draw()
        plt.pause(0.001)
        
        self.start_process()

    def process(self,image):
        (vx,vy,vz) = self._image_dimension # (74, 74, 36)
        mxy = int(np.ceil(np.sqrt(vz)))

        tiles = image.reshape(vx,vy,mxy,mxy)
        tiles = np.moveaxis(tiles,[0,1,2,3],[1,3,0,2]).reshape(vx*mxy,vy*mxy)

        plt.imshow(tiles,cmap='jet')
        self.figure.canvas.draw()
        plt.pause(0.001)

# imgDim = (5,5,3)
#
# if __name__ == '__main__':
#     mlp = mlproc.MatlabSharedEngineHelper(startup_options='-desktop', shared_name='test')
#     mlp.connect(start=True, name_prefix='test')
#     mlp.engine.assignin('base','sig',0,nargout=0)
# 
#     t = myImageProcess(imgDim)
# 
#     it = 0
#     while it < 5:
#         cit = mlp.engine.evalin('base','sig')
#         if cit > it:
#             it = cit
#             t.load_image(mlp.engine.evalin('base','mainLoopData.tn')._data.tolist())
#             sleep(2)
# 
#     t = None
#     mlp.destroy_engine()