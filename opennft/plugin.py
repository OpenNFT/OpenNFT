from PyQt5.QtWidgets import QDialog
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt
from PyQt5.uic import loadUi
from loguru import logger
import matlab

import importlib
import os

from opennft import config, utils, eventrecorder

class PluginWindow(QDialog):
    def __init__(self, parent=None):
        self.plugins = []

        super().__init__(parent=parent, flags=Qt.Dialog)
        loadUi(utils.get_ui_file('plugins.ui'), self)

        self.setWindowTitle("Plugins")
        self.setWindowModality(Qt.ApplicationModal)

        model = QStandardItemModel(self.lvPlugins)
        for p in [f for f in os.listdir(config.PLUGIN_PATH) if f.endswith('.py')]:
            plMod = 'opennft.' + os.path.basename(config.PLUGIN_PATH).lower() + '.' + p[:-3]
            self.plugins += [importlib.import_module(plMod)]
            plName = self.plugins[-1].META['plugin_name']
            item = QStandardItem(plName)
            item.setEditable(False)
            item.setCheckable(True)
            model.appendRow(item)
        self.lvPlugins.setModel(model)

class Plugin:

    def __init__(self,parentApplication,module):
        self.parent = parentApplication
        self.module = module
        self.object = None

    def initialize(self):
        if type(self.module.META['plugin_init']) == list: # post-initialization
            initcmd = self.module.META['plugin_init'][0]
            postinitcdm = self.module.META['plugin_init'][1:]
        else: 
            initcmd = self.module.META['plugin_init'] # no post-initialization
            postinitcdm = []
        self.object = eval("self.module." + initcmd.format(**self.parent.P))
        for cmd in postinitcdm:
            exec(cmd.format(**self.parent.P))
        logger.info('Plugin "' + self.module.META['plugin_name'] + '" has been initialized')

    def update(self):
        m = self.module.META
        if (self.parent.recorder.getLastEvent() == eval("eventrecorder.Times." + m['plugin_time'])) and eval(m['plugin_signal']):
            exec("self.object." + m['plugin_exec'])
    
    def finalize(self):
        self.object = None