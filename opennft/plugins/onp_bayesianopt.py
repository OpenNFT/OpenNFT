from pyniexp.mlplugins import imageProcess, SIG_NOTSTARTED, SIG_RUNNING, SIG_STOPPED, SIG_NEWIMAGE
from multiprocessing import Value, RawArray
from loguru import logger


META = {
    "plugin_name": "Bayesian Optimisation",
    "plugin_time": "t3", # according to opennft.eventrecorder.Times
    "plugin_init": "BOengine(int({NrROIs}))",
    "plugin_signal": "self.eng.evalin('base','isfield(mainLoopData,\\\'tn\\\')')",
    "plugin_exec": "load_image(self.eng.evalin('base','onp_extract_rois')._data.tolist())"
}

class BOengine(imageProcess):
    def __init__(self,nROIs):
        self._buffer = RawArray('d',[0]*nROIs)
        self._signal = Value('b',SIG_NOTSTARTED)
        
        self.start_process()

    def _run(self):
        while self._signal.value != SIG_STOPPED:
            if self._signal.value == SIG_NOTSTARTED: 
                logger.info('Process is running')
                self._signal.value = SIG_RUNNING
            if self._signal.value == SIG_NEWIMAGE:
                logger.info('New data: [{:.3f}, {:.3f}]'.format(*self._buffer))
                self._signal.value = SIG_RUNNING
        logger.info('Process is stopped')