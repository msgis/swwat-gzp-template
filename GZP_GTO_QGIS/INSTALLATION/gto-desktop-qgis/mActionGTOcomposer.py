#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

from PyQt5.QtCore import QObject

from qgis.PyQt.QtXml import QDomDocument
from qgis.core import QgsLayout, QgsRectangle,QgsProject,QgsLayoutManager,QgsMasterLayoutInterface,QgsReadWriteContext,QgsPathResolver,QgsPrintLayout,QgsLayoutItemMap,QgsLayout

import os

class run(QObject):
    def __init__(self, id, gtotool, config, debug):
        super(run, self).__init__()
        try:
            self.debug = debug
            self.gtotool=gtotool
            self.gtomain = gtotool.gtomain
            self.info =gtotool.info
            self.metadata = self.gtomain.metadata
            templatedir = self.metadata.dirPrintLayouts
            self.iface = self.gtomain.iface
            #tool data
            composername =  config['composer']
            template = config['template']
            activetool= config['active_tool']
            activetoolcaption = config['active_tool_caption']
            set_to_mapextent = config['set_to_mapextent']
            scale = config['scale']
            #init
            templatefile = None
            layoutname= os.path.splitext(template)[0]
            layoutname = config.get('displayname', layoutname)
            prj = QgsProject.instance()
            projectLayoutManager = prj.layoutManager()#QgsLayoutManager
            self.layout = None
            if template is not None and template !='':
                templatefile = os.path.join(templatedir , template)
                if debug: self.info.log("template:",templatefile)
                if os.path.isfile(templatefile):
                    f= open(templatefile, 'r')
                    templateContent = f.read()
                    f.close()
                    doc=QDomDocument()
                    doc.setContent(templateContent)
                    pr = QgsPathResolver(templatefile)
                    rwc = QgsReadWriteContext()
                    rwc.setPathResolver(pr)
                    self.layout = QgsPrintLayout(prj)
                    self.layout.loadFromTemplate(doc,rwc)
                    self.layout.setName(layoutname)
                    projectLayoutManager.addLayout(self.layout)
            self.layout = projectLayoutManager.layoutByName(layoutname)
            if self.debug: self.info.log(type(self.layout))
            if self.debug:self.info.log("found layout:",self.layout.name())
            result = self.iface.openLayoutDesigner(self.layout)#QgsLayoutDesignerInterface

            self.layoutview = result.view()#QgsLayoutView
            currenttool = self.layoutview.tool()#QgsLayoutViewTool
            #tool = QgsLayoutViewToolMoveItemContent(self.layoutview)
            # self.layoutview.setTool(tool)

            if self.debug: self.info.log (currenttool.toolName())
            for ld in self.iface.openLayoutDesigners():
                if self.debug: self.info.log(type(ld))
            #itemMap = QgsLayoutItemMap(self.layout)
            referencemap = self.layout.referenceMap()
            if set_to_mapextent:
                referencemap.zoomToExtent(self.iface.mapCanvas().extent())
            if scale != 0:
                referencemap.setScale(scale)
            referencemap.refresh()

        except IndexError as e:
            self.info.err(e)





