# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/will/scripts/qtpad/gui.ui'
#
# Created by: PyQt5 UI code generator 5.9
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(253, 219)
        Form.setAutoFillBackground(False)
        Form.setStyleSheet("QWidget\n"
"{\n"
"    background-color: white;\n"
"}\n"
"\n"
"QWidget.QPlainTextEdit, QWidget.QTextEdit\n"
"{\n"
"    border: none;\n"
"}\n"
"\n"
"QWidget.QLineEdit\n"
"{\n"
"    border: 1px solid black;\n"
"    margin: 6px;\n"
"}\n"
"\n"
"QWidget.QLabel#renameLabel\n"
"{\n"
"    padding-top: 6px;\n"
"    padding-left: 4px;\n"
"}\n"
"\n"
"QWidget.QScrollBar\n"
"{\n"
"    width: 18px;\n"
"    color: black;\n"
"    background-color: lightgray\n"
"}\n"
"\n"
"")
        self.gridLayout = QtWidgets.QGridLayout(Form)
        self.gridLayout.setSizeConstraint(QtWidgets.QLayout.SetMaximumSize)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName("gridLayout")
        self.textEdit = QtWidgets.QPlainTextEdit(Form)
        self.textEdit.setPlainText("")
        self.textEdit.setObjectName("textEdit")
        self.gridLayout.addWidget(self.textEdit, 1, 0, 1, 1)
        self.inputText = QtWidgets.QLineEdit(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.inputText.sizePolicy().hasHeightForWidth())
        self.inputText.setSizePolicy(sizePolicy)
        self.inputText.setAcceptDrops(False)
        self.inputText.setFrame(True)
        self.inputText.setObjectName("inputText")
        self.gridLayout.addWidget(self.inputText, 3, 0, 1, 1)
        self.inputLabel = QtWidgets.QLabel(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.inputLabel.sizePolicy().hasHeightForWidth())
        self.inputLabel.setSizePolicy(sizePolicy)
        self.inputLabel.setObjectName("inputLabel")
        self.gridLayout.addWidget(self.inputLabel, 2, 0, 1, 1)
        self.imageLabel = QtWidgets.QLabel(Form)
        self.imageLabel.setText("")
        self.imageLabel.setObjectName("imageLabel")
        self.gridLayout.addWidget(self.imageLabel, 0, 0, 1, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.inputLabel.setText(_translate("Form", "Enter new name:"))

