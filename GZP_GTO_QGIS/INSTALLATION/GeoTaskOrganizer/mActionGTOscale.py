#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
from qgis.core import QgsProject


class run(object):
    def __init__(self, id, gtoTool, config, debug):
        super(run, self).__init__()
        try:
            #references
            self.result = None
            self.debug = debug
            self.info = gtoTool.info
            self.gtomain = gtoTool.gtomain
            self.metadata = self.gtomain.metadata
            self.iface = self.gtomain.iface
            self.iface = self.gtomain.iface
            self.prj = QgsProject.instance()
            self.canvas = self.iface.mapCanvas()

            # tool data
            self.scale = config.get('scale', 0)
            self.min_scale = config.get('min_scale', 0)
            self.max_scale = config.get('max_scale', 0)
            # do the job
            if self.scale != 0:
                self.canvas.zoomScale(self.scale)
            else:
                if self.canvas.scale()< self.min_scale:
                    self.canvas.zoomScale(self.min_scale)
                elif self.canvas.scale()>self.max_scale and self.max_scale != 0:
                    self.canvas.zoomScale(self.max_scale)
        except Exception as e:
            self.info.err(e)