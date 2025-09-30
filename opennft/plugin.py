from PyQt6.QtWidgets import QDialog
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt
from PyQt6.uic import loadUi
from loguru import logger

import importlib

from opennft import config, utils

# import modules referred by plugin methods (often evaluated)
from opennft import eventrecorder
import matlab

class PluginWindow(QDialog):
    def __init__(self, parent=None):
        self.plugins = []

        super().__init__(parent=parent, flags=Qt.WindowType.Dialog)
        loadUi(utils.get_ui_file('plugins.ui'), self)

        self.setWindowTitle("Plugins")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        model = QStandardItemModel(self.lvPlugins)
        for p in [f.name for f in config.PLUGIN_PATH.glob('*.py')]:
            plMod = 'opennft.' + config.PLUGIN_PATH.name.lower() + '.' + p[:-3]
            self.plugins += [importlib.import_module(plMod)]
            plName = self.plugins[-1].META['plugin_name']
            item = QStandardItem(plName)
            item.setEditable(False)
            item.setCheckable(True)
            model.appendRow(item)
        self.lvPlugins.setModel(model)


class Plugin:

    def __init__(self, parentApplication, module):
        self.parent = parentApplication
        self.module = module
        self.object = None

    def initialize(self):
        if type(self.module.META['plugin_init']) == list:  # post-initialization
            initcmd = self.module.META['plugin_init'][0]
            postinitcdm = self.module.META['plugin_init'][1:]
        else:
            initcmd = self.module.META['plugin_init']  # no post-initialization
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
