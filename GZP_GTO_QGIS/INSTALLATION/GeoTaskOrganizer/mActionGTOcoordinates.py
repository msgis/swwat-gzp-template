#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QDockWidget
from .gto_coordinate import GTOCoordinatesDockWidget


class run(object):
    def __init__(self, id, gtoTool, config, debug):
        super(run, self).__init__()
        try:
            # references
            self.result = None
            self.debug = debug
            self.info = gtoTool.info
            self.gtomain = gtoTool.gtomain
            self.helper = self.gtomain.helper
            self.metadata = self.gtomain.metadata
            self.iface = self.gtomain.iface
            # find widget and init
            self.dlg = self.iface.mainWindow().findChild(QDockWidget, 'GTOCoordinatesDockWidget')
            if self.dlg is None:  # should not happen: gtomain:__init__=>self.gtowids=[gtoCoordinate(self)]
                self.dlg = GTOCoordinatesDockWidget(self.gtomain, self.iface.mainWindow())
            self.dlg.init(config)
            self.dlg.show()
        except Exception as e:
            self.info.err(e)
