from opennft import mlproc
from pyniexp.mlplugins import imageProcess
from time import sleep

META = {
    "plugin_name": "Stat Map",
    "plugin_type": "data_processor",
    "plugin_time": "t3", # according to opennft.eventrecorder.Times
    "plugin_load": "myImageProcess(({MatrixSizeX}, {MatrixSizeY}, {NrOfSlices}))",
    "data": "mainLoopData.tn",
    "data_source": "self.eng",
    "data_load": "load_image"
}

imgDim = (5,5,3)

class myImageProcess(imageProcess):
    def process(self,image):
        print(image[:,:,0])

if __name__ == '__main__':
    mlp = mlproc.MatlabSharedEngineHelper(startup_options='-desktop', shared_name='test')
    mlp.connect(start=True, name_prefix='test')
    mlp.engine.assignin('base','sig',0,nargout=0)

    t = myImageProcess(imgDim)

    it = 0
    while it < 5:
        cit = mlp.engine.evalin('base','sig')
        if cit > it:
            it = cit
            t.load_image(mlp.engine.evalin('base','mainLoopData.tn')._data.tolist())
            sleep(2)

    t = None
    mlp.destroy_engine()