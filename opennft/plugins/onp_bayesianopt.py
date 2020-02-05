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
