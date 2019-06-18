# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'gtoTree_dockwidget_base.ui'
#
# Created by: PyQt5 UI code generator 5.9
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_GTODockWidgetBase(object):
    def setupUi(self, GTODockWidgetBase):
        GTODockWidgetBase.setObjectName("GTODockWidgetBase")
        GTODockWidgetBase.resize(507, 876)
        GTODockWidgetBase.setStyleSheet("")
        self.dockWidgetContents = QtWidgets.QWidget()
        self.dockWidgetContents.setObjectName("dockWidgetContents")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.dockWidgetContents)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.splitter = QtWidgets.QSplitter(self.dockWidgetContents)
        self.splitter.setStyleSheet("")
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.splitter.setObjectName("splitter")
        self.scrollArea_Info = QtWidgets.QScrollArea(self.splitter)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollArea_Info.sizePolicy().hasHeightForWidth())
        self.scrollArea_Info.setSizePolicy(sizePolicy)
        self.scrollArea_Info.setMinimumSize(QtCore.QSize(0, 100))
        self.scrollArea_Info.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.scrollArea_Info.setStyleSheet("")
        self.scrollArea_Info.setWidgetResizable(True)
        self.scrollArea_Info.setObjectName("scrollArea_Info")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 487, 120))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.gridLayout = QtWidgets.QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        self.label_Info = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_Info.sizePolicy().hasHeightForWidth())
        self.label_Info.setSizePolicy(sizePolicy)
        self.label_Info.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_Info.setStyleSheet("")
        self.label_Info.setText("")
        self.label_Info.setObjectName("label_Info")
        self.gridLayout.addWidget(self.label_Info, 0, 0, 1, 1)
        self.scrollArea_Info.setWidget(self.scrollAreaWidgetContents)
        self.treeWidget = QtWidgets.QTreeWidget(self.splitter)
        font = QtGui.QFont()
        self.treeWidget.setFont(font)
        self.treeWidget.setStyleSheet("")
        self.treeWidget.setObjectName("treeWidget")
        self.treeWidget.headerItem().setText(0, "1")
        item_0 = QtWidgets.QTreeWidgetItem(self.treeWidget)
        item_0 = QtWidgets.QTreeWidgetItem(self.treeWidget)
        item_0 = QtWidgets.QTreeWidgetItem(self.treeWidget)
        item_0 = QtWidgets.QTreeWidgetItem(self.treeWidget)
        item_0 = QtWidgets.QTreeWidgetItem(self.treeWidget)
        self.verticalLayout.addWidget(self.splitter)
        GTODockWidgetBase.setWidget(self.dockWidgetContents)

        self.retranslateUi(GTODockWidgetBase)
        QtCore.QMetaObject.connectSlotsByName(GTODockWidgetBase)

    def retranslateUi(self, GTODockWidgetBase):
        _translate = QtCore.QCoreApplication.translate
        GTODockWidgetBase.setWindowTitle(_translate("GTODockWidgetBase", "GeoTaskOrganizer"))
        self.treeWidget.headerItem().setText(1, _translate("GTODockWidgetBase", "New Column"))
        self.treeWidget.headerItem().setText(2, _translate("GTODockWidgetBase", "New Column"))
        self.treeWidget.headerItem().setText(3, _translate("GTODockWidgetBase", "New Column"))
        self.treeWidget.headerItem().setText(4, _translate("GTODockWidgetBase", "New Column"))
        __sortingEnabled = self.treeWidget.isSortingEnabled()
        self.treeWidget.setSortingEnabled(False)
        self.treeWidget.topLevelItem(0).setText(0, _translate("GTODockWidgetBase", "New Item"))
        self.treeWidget.topLevelItem(1).setText(0, _translate("GTODockWidgetBase", "New Item"))
        self.treeWidget.topLevelItem(2).setText(0, _translate("GTODockWidgetBase", "New Item"))
        self.treeWidget.topLevelItem(3).setText(0, _translate("GTODockWidgetBase", "New Item"))
        self.treeWidget.topLevelItem(4).setText(0, _translate("GTODockWidgetBase", "New Item"))
        self.treeWidget.setSortingEnabled(__sortingEnabled)

