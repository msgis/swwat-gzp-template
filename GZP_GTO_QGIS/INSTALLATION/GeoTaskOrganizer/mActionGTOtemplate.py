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
            self.prj = QgsProject.instance()
            self.canvas = self.iface.mapCanvas()

            # tool data
            self.tools = config.get("tools", [])
            self.targetlayer = config.get('targetlayer',None)


            #init
            self.targetlayer = self.prj.mapLayersByName(self.targetlayer)
            if self.targetlayer:
                self.targetlayer = self.targetlayer[0]#if duplicate names
            else:
                self.targetlayer = self.iface.activeLayer()

            # do the job


            #run tools
            self.gtomain.runcmd(self.tools)
        except Exception as e:
            self.info.err(e)