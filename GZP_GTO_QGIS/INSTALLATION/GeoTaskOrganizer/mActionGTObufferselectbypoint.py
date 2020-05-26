#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from PyQt5.QtCore import Qt,pyqtSignal
from PyQt5.QtGui import QColor,QCursor
from PyQt5.QtWidgets import QAction

from qgis.core import QgsGeometry,QgsWkbTypes,QgsPointXY,QgsCircle,QgsPoint, QgsProject, QgsSnappingUtils, QgsSnappingConfig
from qgis.gui import QgsMapTool, QgsRubberBand, QgsMapMouseEvent, QgsVertexMarker

import math

class run(object):
    def __init__(self, id, gtoTool, config, debug):
        super(run, self).__init__()
        try:
            #references
            self.result = None
            self.debug = debug
            self.info = gtoTool.info
            self.gtomain = gtoTool.gtomain
            self.helper = self.gtomain.helper
            self.metadata = self.gtomain.metadata
            self.iface = self.gtomain.iface
            self.canvas = self.iface.mapCanvas()
            self.toolID = id
            self.config=config
            self.action =gtoTool.action

            # references
            self.geo = None
            #get the toolbar
            module = self.gtomain.helper.importModule("gto_bufferselecttoolbar")
            self.toolbar= module.BufferSelectToolbar(self)#=> all references to toolbar
            #create tool and activate
            self.action.setCheckable(True)
            #self.action.setChecked(True)
            self.curTool = SnapMapTool(self.iface.mapCanvas())#the maptool
            self.iface.mapCanvas().setMapTool(self.curTool)
            self.curTool.geometry_changed.connect(self.setGeometryToToolbar)
            self.curTool.tool_deactivated.connect(lambda : self.toolbar.setHidden(True))
            self.toolbar.setHidden(False)
        except Exception as e:
            self.info.err(e)

    def setGeometryToMapTool(self, geo):#from the toolbar, buffered
        self.curTool.setGeometry(geo)#=>Maptool

    def setGeometryToToolbar(self, geo, isValid):#from the maptool
        self.toolbar.setGeometry(geo, isValid)#=> toolbar

class SnapMapTool(QgsMapTool):
    geometry_changed = pyqtSignal(QgsGeometry, bool)
    tool_deactivated = pyqtSignal()

    def __init__(self, canvas, cursorstyle = Qt.CrossCursor):
        self.canvas = canvas
        QgsMapTool.__init__(self, canvas)
        self.caller = self.sender()
        self.cursorStyle=cursorstyle
        self.active = False
        # get selection color
        selcolor =self.canvas.selectionColor()
        mycolor = QColor(selcolor.red(), selcolor.green(), selcolor.blue(), 40)
        self.rb = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
        self.rb.setStrokeColor(QColor(255, 0, 0, 40))
        self.rb.setFillColor(mycolor)
        self.rb.setLineStyle(Qt.PenStyle(Qt.SolidLine))
        self.rb.setWidth(2)

        #snapping
        self.useSnapped = True
        self.snapper = None
        self.markerSnapped = None
        self.prj = QgsProject.instance()
        self.snapConfig = self.prj.snappingConfig()
        self.prj.snappingConfigChanged.connect(self.setSnapping)

        self.setSnapping(self.prj.snappingConfig())

    def setCursorStyle(self):
        cursor = QCursor()
        cursor.setShape(self.cursorStyle)
        self.setCursor(cursor)

    def setGeometry(self,geo):
        self.rb.setToGeometry(geo)

    def activate(self):
        self.caller.setChecked(True)
        self.setCursorStyle()

    def canvasMoveEvent(self, event):
        point = self.toMapCoordinates(event.pos())
        if self.snapConfig.enabled() and self.useSnapped:
            self.isSnapped(point)
        else:
            self.resetMarker()

    def canvasReleaseEvent(self, event):
        point = self.toMapCoordinates(event.pos())
        if self.useSnapped: point=self.isSnapped(point)
        self.rb.reset(QgsWkbTypes.PointGeometry)
        self.rb.addPoint(point)
        geo = self.rb.asGeometry()
        self.geometry_changed.emit(geo,True)

    def deactivate(self):
        self.resetMarker()
        self.canvas.scene().removeItem(self.rb)
        self.tool_deactivated.emit()
        self.caller.setChecked(False)
        QgsMapTool.deactivate(self)

    def setSnapping(self, config):
        self.snapConfig = config
        self.snapper = QgsSnappingUtils(self.canvas)
        self.snapper.setConfig(self.snapConfig)
        self.snapper.setMapSettings(self.canvas.mapSettings())

    def isSnapped(self, pointxy):
        self.resetMarker()
        matchres = self.snapper.snapToMap(pointxy)  # QgsPointLocator.Match
        if matchres.isValid():
            self.markerSnapped = QgsVertexMarker(self.canvas)
            self.markerSnapped.setColor(Qt.red)
            self.markerSnapped.setIconSize(7)
            self.markerSnapped.setIconType(QgsVertexMarker.ICON_BOX)
            self.markerSnapped.setPenWidth(3)
            self.markerSnapped.setCenter(matchres.point())
            self.markerSnapped.show()
            return matchres.point()
        else:
            return pointxy
    def resetMarker(self):
        self.canvas.scene().removeItem(self.markerSnapped)
