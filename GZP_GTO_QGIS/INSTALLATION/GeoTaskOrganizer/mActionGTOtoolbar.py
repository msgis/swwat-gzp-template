#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

from PyQt5.QtCore import Qt, QObject
from PyQt5.QtWidgets import QMainWindow, QAction, QWidget, QToolBar, QMenu, QToolButton, QPushButton, QSizePolicy
from PyQt5.QtGui import QIcon, QPixmap


class run(QObject):
    def __init__(self, id, gtotool, config, debug):
        super(run, self).__init__()
        self.debug = debug
        self.gtotool = gtotool
        self.gtomain = gtotool.gtomain
        self.helper = self.gtomain.helper
        self.iface = gtotool.iface
        self.info = gtotool.info
        self.action = gtotool.action  # threading!
        self.action.setCheckable(True)  # toogle toolbar
        try:
            # get config
            toolbar_name = config.get("toolbar_name", None)
            object_name = config.get("object_name", None)
            tools = config.get("tools", [])
            toolbar_style = config.get("toolbar_style", 3)
            toolbar_dock = config.get("toolbar_dock", 4)
            show_hide_button = config.get("show_hide_button", False)
            new_line = config.get("new_line", True)

            if object_name is not None:  # find standard toolbar eg "toolbar_name":"mShapeDigitizeToolBar"
                self.toolbar = self.gtomain.helper.findToolbar(self.iface, object_name)
                if self.toolbar is not None:
                    if self.debug: self.info.log('found QGIS toolbar', 'object_name', object_name)
                    if show_hide_button:
                        spacer = QWidget()
                        spacer.setObjectName('spacer')
                        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                        spacer.setStyleSheet("QWidget{background: transparent;}")
                        if self.toolbar.findChild(QWidget, 'spacer') is None:
                            self.toolbar.addWidget(spacer)
                            self.toolbar.addAction(self.toolbar.toggleViewAction())
                else:
                    return
            else:
                object_name = "gtoTB_" + gtotool.action.objectName()  # gto toolbar

                self.toolbar = self.helper.getToolBar(self, object_name, toolbar_name, self.iface.mainWindow())
                if self.debug: self.info.log('GTO toolbar', 'object_name', object_name)
                self.toolbar.clear()
                # self.toolbar = self.gtomain.helper.findToolbar(self.iface, object_name)
                # if self.toolbar is None:
                #     if self.debug: self.info.log('create GTO toolbar', 'object_name', object_name)
                #         self.toolbar = QToolBar(self.iface.mainWindow())
                #         self.toolbar.setObjectName(object_name)
                #         # toggle action objectname = QT: toolbar.objectName + _toggle
                #         self.toolbar.setWindowTitle(toolbar_name)
                #     self.toolbar.clear()

                # set properties
                if tools is not None:
                    for t in tools:
                        self.helper.addAction(self.toolbar, t)
            # common
            self.toolbar.setToolButtonStyle(toolbar_style)
            if show_hide_button:
                    self.helper.addToolbarClose(self.toolbar)
            if new_line: self.iface.mainWindow().addToolBarBreak(toolbar_dock)
            self.iface.addToolBar(self.toolbar, toolbar_dock)  # apply dock
            self.toolbar.setHidden(False)
        except Exception as e:
            self.info.err(e)
