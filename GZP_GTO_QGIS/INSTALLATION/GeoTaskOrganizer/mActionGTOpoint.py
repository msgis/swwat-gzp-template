#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QToolBar, QWidget, QSizePolicy
from PyQt5.QtCore import QObject, Qt

from .gto_point import GTOPointWidget


class run(QObject):  # gtoAction
    def __init__(self, id, gtoTool, config, debug):
        super(run, self).__init__()
        # references
        self.debug = debug
        self.id = id
        self.config = config
        self.info = gtoTool.info

        try:
            self.action = gtoTool.action
            self.action.setCheckable(True)
            self.gtomain = gtoTool.gtomain
            self.helper = self.gtomain.helper
            self.metadata = self.gtomain.metadata
            self.iface = self.gtomain.iface
            self.canvas = self.iface.mapCanvas()
            if not self.config.get("is_widgetaction", False):
                # tool data
                self.toolbar_dock = self.config.get("toolbar_dock", 4)
                # widget
                self.toolbar = None

                # load toolbar
                self.objName = "gtoTB_" + gtoTool.action.objectName() + str(id)
                self.toolbar = self.gtomain.helper.findToolbar(self.iface, self.objName)
                if self.toolbar is None:
                    if self.debug: self.info.log("load", self.objName)
                    self.toolbar = QToolBar()
                    self.toolbar.setObjectName(self.objName)
                    self.toolbar.setWindowTitle(u'GTO Coordinate')
                    self.toolbar.setAllowedAreas(Qt.BottomToolBarArea | Qt.TopToolBarArea)
                    self.iface.mainWindow().addToolBarBreak(self.toolbar_dock)
                    self.iface.addToolBar(self.toolbar, self.toolbar_dock)
                else:
                    self.toolbar.clear()
                self.wid = GTOPointWidget(self.gtomain, self.toolbar)
                self.toolbar.addWidget(self.wid)
                if self.config.get("spacer", False):
                    spacer = QWidget()
                    spacer.setObjectName('spacer')
                    spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                    spacer.setStyleSheet("QWidget{background: transparent;}")
                    self.toolbar.addWidget(spacer)
                self.wid.set_parent_widget(self)
                self.wid.isActive.connect(self.set_status)  # not always(?) working?
                self.wid.setConfig(self.config)
                self.wid.added()
                self.wid.setMapTool()
                self.toolbar.show()
        except Exception as e:
            self.info.err(e)

    def set_status(self, isActive):
        try:
            self.action.setChecked(isActive)
            self.toolbar.setHidden(not isActive)
        except Exception as e:
            self.info.err(e)
