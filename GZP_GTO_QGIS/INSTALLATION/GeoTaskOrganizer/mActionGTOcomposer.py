#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

from PyQt5.QtCore import QObject

from qgis.PyQt.QtXml import QDomDocument
from qgis.core import QgsLayout, QgsRectangle,QgsProject,QgsLayoutManager,QgsMasterLayoutInterface,QgsReadWriteContext,QgsPathResolver,QgsPrintLayout,QgsLayoutItemMap,QgsLayout
from qgis.gui import QgsLayoutViewToolMoveItemContent,QgsLayoutView,QgsLayoutViewTool
from PyQt5.QtWidgets import QActionGroup

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
            template = config.get('template',None)
            activetool= config.get('active_tool',None)
            scale = config.get('scale',0)
            #init
            templatefile = None
            layoutname =config.get('layoutname', None)
            if template and layoutname is None:
                layoutname= os.path.splitext(template)[0]#default layoutname for template
            if self.debug:self.info.log("layoutname:",layoutname)
            prj = QgsProject.instance()
            projectLayoutManager = prj.layoutManager()#QgsLayoutManager
            self.layout = None
            if template is not None:
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
            if self.debug and self.layout:self.info.log("found layout:",self.layout.name())
            if self.layout:
                result = self.iface.openLayoutDesigner(self.layout)#QgsLayoutDesignerInterface

                self.layoutview = result.view()#QgsLayoutView
                currenttool = self.layoutview.tool()#QgsLayoutViewTool
                if self.debug: self.info.log(currenttool.toolName())

                if activetool:
                    tool = QgsLayoutViewToolMoveItemContent(self.layoutview)
                    self.layoutview.setTool(tool)

                #itemMap = QgsLayoutItemMap(self.layout)
                referencemap = self.layout.referenceMap()
                referencemap.zoomToExtent(self.iface.mapCanvas().extent())
                if scale < 0:
                    referencemap.setScale(self.iface.mapCanvas().scale())
                elif scale > 0:
                    referencemap.setScale(scale)
                referencemap.refresh()

                if activetool:
                    menu = result.editMenu()
                    for a in menu.actions():
                        if a.objectName() == activetool:
                            if self.debug: self.info.log("set active tool:",activetool)
                            a.trigger()
                            break
                self.result = True
            else:
                self.result="Layout <%s> not found!" % layoutname
        except Exception as e:
            self.info.err(e)





