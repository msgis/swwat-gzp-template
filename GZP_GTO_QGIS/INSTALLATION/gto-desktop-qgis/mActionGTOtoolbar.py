#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import QToolBar

class run(QObject):
    def __init__(self, id, gtotool, config, debug):
        super(run, self).__init__()
        self.debug = debug
        self.gtotool=gtotool
        self.gtomain = gtotool.gtomain
        self.helper=self.gtomain.helper
        self.iface = gtotool.iface
        self.info = gtotool.info
        try:
            objName = "gtoTB_" + gtotool.action.objectName()
            caption = config.get("toolbar_name", objName)
            toolbar_style = config.get("toolbar_style", 3)
            toolbar_dock = config.get("toolbar_dock", 4)
            tools = config.get("tools", None)
            toolbar = None
            # load toolbar
            toolbar= self.gtomain.helper.findToolbar(self.iface, objName)
            if toolbar is None:
                if self.debug: self.info.log("load", objName)
                toolbar = QToolBar()
                toolbar.setObjectName(objName)
                self.iface.addToolBar(toolbar, toolbar_dock)
            else:
                toolbar.clear()
                toolbar.setHidden(False)

            toolbar.setWindowTitle(caption)
            toolbar.setToolButtonStyle(toolbar_style)
            if self.debug: self.info.log("ToolbarStyle",toolbar_style)
            if self.debug: self.info.log("ToolbarDock", toolbar_dock)
            for t in tools:
                tname = t.lower()
                if tname == "separator":
                    self.gtotb.addSeparator()
                    if self.debug: self.info.log(caption, 'Add: separator')
                else:
                    action = gtotool.gtomain.findAction(tname)
                    if action is not None:
                        toolbar.addAction(action)
        except Exception as e:
            self.info.gtoWarning(e.args)
