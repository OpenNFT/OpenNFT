# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'opennft\ui\rtQAUI.ui'
#
# Created by: PyQt5 UI code generator 5.12.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_rtQA(object):
    def setupUi(self, rtQA):
        rtQA.setObjectName("rtQA")
        rtQA.resize(878, 243)
        self.layoutWidget = QtWidgets.QWidget(rtQA)
        self.layoutWidget.setGeometry(QtCore.QRect(10, 10, 721, 221))
        self.layoutWidget.setObjectName("layoutWidget")
        self.layoutPlot1 = QtWidgets.QVBoxLayout(self.layoutWidget)
        self.layoutPlot1.setContentsMargins(0, 0, 0, 0)
        self.layoutPlot1.setObjectName("layoutPlot1")
        self.comboBox = QtWidgets.QComboBox(rtQA)
        self.comboBox.setGeometry(QtCore.QRect(740, 10, 131, 22))
        self.comboBox.setObjectName("comboBox")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.snrVolCheckBox = QtWidgets.QCheckBox(rtQA)
        self.snrVolCheckBox.setGeometry(QtCore.QRect(740, 40, 121, 16))
        self.snrVolCheckBox.setObjectName("snrVolCheckBox")

        self.retranslateUi(rtQA)
        QtCore.QMetaObject.connectSlotsByName(rtQA)

    def retranslateUi(self, rtQA):
        _translate = QtCore.QCoreApplication.translate
        rtQA.setWindowTitle(_translate("rtQA", "RTQA"))
        self.comboBox.setCurrentText(_translate("rtQA", "Raw"))
        self.comboBox.setItemText(0, _translate("rtQA", "Raw"))
        self.comboBox.setItemText(1, _translate("rtQA", "Processed"))
        self.snrVolCheckBox.setText(_translate("rtQA", "Volume SNR"))


