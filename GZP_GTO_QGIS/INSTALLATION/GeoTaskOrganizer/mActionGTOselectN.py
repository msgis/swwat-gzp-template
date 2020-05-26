#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
from qgis.core import QgsProject,QgsVectorLayer


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
            self.sourcelayer = config.get('sourcelayer',None)
            self.targetlayer = config.get('targetlayer',None)
            self.source_fields=config.get('source_fields',[])
            self.query = config.get('query','')
            self.tools = config.get("tools",[])

            #init
            self.targetlayer = self.prj.mapLayersByName(self.targetlayer)
            if self.targetlayer is not None:
                self.targetlayer = self.targetlayer[0]#if duplicate names
            else:
                self.targetlayer = self.iface.activeLayer()

            self.sourcelayer = self.prj.mapLayersByName(self.sourcelayer)
            if self.sourcelayer is not None:
                self.sourcelayer = self.sourcelayer[0]  # if duplicate names
            else:
                self.sourcelayer = self.iface.activeLayer()
            # do the job
            fids = self.sourcelayer.selectedFeatureIds ()
            self.targetlayer.removeSelection()
            if self.debug:self.info.log("sourcelayer:",self.sourcelayer.name())
            for f in fids:
                feat = self.sourcelayer.getFeature(f)
                expr = self.query.replace("'",'"')
                values = []
                for field in self.source_fields:
                    value = feat[field]
                    if isinstance(value,str):
                        values.append("'"+ str(value)+"'")
                    else:
                        values.append(value)
                    if self.debug: self.info.log("values",values)
                expr = expr.format(*values)
                if self.debug: self.info.log("expr:",expr)
                self.targetlayer.selectByExpression(expr,QgsVectorLayer.AddToSelection )
            if self.debug: self.info.log("Selected features on ",self.targetlayer.name(),":",self.targetlayer.selectedFeatureCount ())
            self.iface.setActiveLayer(self.targetlayer)
            #rund tools
            self.gtomain.runcmd(self.tools)
        except Exception as e:
            self.info.err(e)