from PyQt5.QtWidgets import QDialog
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt
from PyQt5.uic import loadUi

import importlib
import os

from opennft import config, utils

class PluginWindow(QDialog):
    def __init__(self, parent=None):
        self.plugins = []

        super().__init__(parent=parent, flags=Qt.Dialog)
        loadUi(utils.get_ui_file('plugins.ui'), self)

        self.setWindowTitle("Plugins")
        self.setWindowModality(Qt.ApplicationModal)

        model = QStandardItemModel(self.lvPlugins)
        for p in os.listdir(config.PLUGIN_PATH):
            if p[0] == '_': continue
            plMod = 'opennft.' + os.path.basename(config.PLUGIN_PATH).lower() + '.' + p[:-3]
            self.plugins += [importlib.import_module(plMod)]
            plName = self.plugins[-1].META['plugin_name']
            item = QStandardItem(plName)
            item.setEditable(False)
            item.setCheckable(True)
            model.appendRow(item)
        self.lvPlugins.setModel(model)
