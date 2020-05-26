#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt, QObject, QSize
from PyQt5.QtWidgets import QApplication, QDialog, QWidget, QAction, QToolBar, QDockWidget, QSizePolicy, QVBoxLayout, \
    QScrollArea, QPlainTextEdit, QTextBrowser, QPushButton, QHBoxLayout, QSpacerItem, QToolBar, QMainWindow
from PyQt5.QtGui import QIcon


class run(QObject):
    def __init__(self, id, gtotool, config, debug):
        super(run, self).__init__()

        self.debug = debug
        self.gtotool = gtotool
        self.gtomain = gtotool.gtomain
        self.metadata = self.gtomain.metadata
        self.helper = self.gtomain.helper
        self.iface = gtotool.iface
        self.info = gtotool.info
        try:
            # tooldata
            self.title = config.get("title", None)
            self.height = config.get("height", 0)
            self.width = config.get("width", 0)
            self.fixed_size = config.get("fixed_size", False)
            self.use_scrollareas = config.get("no_scrollareas", False)
            self.modal = config.get("modal", False)
            self.widgets = config.get("widgets", [])
            # do task
            self.dlg = QDialog(self.iface.mainWindow())
            if self.title is not None:
                self.dlg.setWindowTitle(self.title)
            self.layout = QVBoxLayout()
            self.parents = []
            available_widgets = []
            # all_widgets =QApplication.instance().allWidgets()
            all_widgets = self.iface.mainWindow().findChildren(QWidget)
            for wid in all_widgets:
                if isinstance(wid, QDockWidget):
                    if not self.widgets and wid.objectName() != '' and wid.windowTitle() != '':
                        txt = "QDockWidget: object name: {0} => title: {1}".format(wid.objectName(), wid.windowTitle())
                        available_widgets.append(txt)
                    if wid.objectName() in self.widgets:
                        dw = wid
                        widget = dw.widget()
                        self.parents.append((dw, widget))
                        self.addWidget(widget)
                elif isinstance(wid, QToolBar):
                    if not self.widgets and wid.objectName() != '' and wid.windowTitle() != '':
                        txt = "QToolBar: object name: {0} => title: {1}".format(wid.objectName(), wid.windowTitle())
                        available_widgets.append(txt)
                    if wid.objectName() in self.widgets:
                        tb = wid
                        parent = wid.parent()
                        self.parents.append((parent, tb))
                        self.layout.addWidget(tb)
                else:
                    if isinstance(wid, QWidget):
                        if not self.widgets:
                            if not self.widgets and wid.objectName() != '' and wid.windowTitle() != '':
                                txt = "QWidget: object name: {0} => title: {1}".format(wid.objectName(), wid.windowTitle())
                                available_widgets.append(txt)
                        if wid.objectName() in self.widgets:
                            widget = wid
                            self.parents.append((widget.nativeParentWidget(), widget))
                            self.addWidget(widget)
            if not self.widgets:
                available_widgets.sort()
                txt = ''
                for line in available_widgets:
                    txt = txt + line + "\n"
                txtBrowser = QTextBrowser()
                txtBrowser.setText(txt)
                self.layout.addWidget(txtBrowser)
            self.setDialog()
            if self.modal:
                self.dlg.exec_()
                self.restore_widgets()
            else:
                self.dlg.show()
        except Exception as e:
            self.info.err(e)

    def restore_widgets(self):
        try:
            for tup in self.parents:
                try:
                    parent = tup[0]
                    wid = tup[1]
                    if isinstance(parent, QDockWidget):
                        parent.setWidget(wid)
                    else:
                        try:
                            self.iface.mainWindow().addToolBarBreak()
                            self.iface.addToolBar(wid, 4)
                        except:
                            if isinstance(parent, QMainWindow):
                                dw = QDockWidget(self.iface.mainWindow())
                                dw.setObjectName("dw_" + wid.objectName())
                                dw.setWindowTitle("GTO " + wid.windowTitle())
                                dw.setWidget(wid)
                                self.iface.addDockWidget(Qt.RightDockWidgetArea, dw)
                                dw.show()
                            else:
                                parent.layout().addWidget(wid)
                    # elif isinstance(parent, QMainWindow):
                    #     self.iface.mainWindow().addToolBarBreak()
                    #     self.iface.addToolBar(wid, 4)
                    # else:
                    #     parent.layout().addWidget(wid)
                except Exception as e:
                    self.info.gtoWarning(
                        'Remove Widget <{0}>\n({1})\nfrom config and restart QGIS!\n'.format(wid.objectName(), wid),
                        e.args)
                    self.info.err(e)
        except Exception as e:
            self.info.err(e)

    def addWidget(self, widget):
        try:
            if self.use_scrollareas:
                scrollarea = QScrollArea()
                scrollarea.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
                scrollarea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
                scrollarea.setWidget(widget)
                self.layout.addWidget(scrollarea)
            else:
                self.layout.addWidget(widget)
            widget.show()
        except Exception as e:
            self.info.err(e)

    def setDialog(self, ):
        try:
            layBtns = QHBoxLayout()
            btnOk = QPushButton('OK')
            btnOk.setMinimumWidth(90)
            btnOk.clicked.connect(self.dlg.accept)
            hspacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
            layBtns.addItem(hspacer)
            layBtns.addWidget(btnOk)
            hspacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
            layBtns.addItem(hspacer)
            self.layout.addLayout(layBtns)
            self.dlg.setLayout(self.layout)
            if self.fixed_size:
                if self.width > 100 and self.height > 100:
                    self.dlg.setFixedSize(QSize(self.width, self.height))
            else:
                if self.width > 100:
                    self.dlg.setMinimumWidth(self.width)
                if self.height > 100:
                    self.dlg.setMinimumHeight(self.height)
        except Exception as e:
            self.info.err(e)
