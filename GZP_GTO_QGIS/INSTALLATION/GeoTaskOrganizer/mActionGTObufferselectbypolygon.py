#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from PyQt5.QtCore import Qt,pyqtSignal
from PyQt5.QtGui import QColor,QCursor
from PyQt5.QtWidgets import QAction

from qgis.core import QgsGeometry,QgsWkbTypes,QgsPointXY,QgsCircle,QgsPoint
from qgis.gui import QgsMapTool, QgsRubberBand, QgsMapMouseEvent

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
            self.curTool = MapTool(self.iface.mapCanvas())#the maptool
            self.iface.mapCanvas().setMapTool(self.curTool)
            self.curTool.geometry_changed.connect(self.setGeometryToToolbar)
            self.curTool.tool_deactivated.connect(lambda : self.toolbar.setHidden(True))
            self.toolbar.setHidden(False)
        except Exception as e:
            self.info.err(e)

    def setGeometryToMapTool(self, geo):#from the toolbar, buffered
        self.curTool.setGeometry(geo)#=>Maptool

    def setGeometryToToolbar(self, geo, isValid):#from the maptool
        isCircle=False
        self.toolbar.setGeometry(geo, isValid, isCircle)#=> toolbar

class MapTool(QgsMapTool):
    geometry_changed = pyqtSignal(QgsGeometry,bool)
    tool_deactivated =  pyqtSignal()

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

    def setCursorStyle(self):
        cursor = QCursor()
        cursor.setShape(self.cursorStyle)
        self.setCursor(cursor)

    def activate(self):
        self.caller.setChecked(True)
        self.setCursorStyle()

    def deactivate(self):
        self.canvas.scene().removeItem(self.rb)
        self.tool_deactivated.emit()
        self.caller.setChecked(False)
        QgsMapTool.deactivate(self)

    def setGeometry(self,geo):
        self.rb.setToGeometry(geo)

    def canvasReleaseEvent(self, mouseEvent):
        if mouseEvent.button() == Qt.LeftButton:
            if not self.active:
                self.active = True
                self.geometry_changed.emit(QgsGeometry(),False)
                self.rb.reset(QgsWkbTypes.PolygonGeometry)
            self.rb.addPoint(mouseEvent.mapPoint())
            if self.rb.numberOfVertices() > 2:
                self.geometry_changed.emit(self.rb.asGeometry(),False)
        elif mouseEvent.button() == Qt.RightButton:
            if  self.rb.numberOfVertices () > 3:
                self.active = False
                self.rb.removeLastPoint()
                self.rb.closePoints()#Ensures that a polygon geometry is closed and that the last vertex equals the first vertex
                geo = self.rb.asGeometry()
                self.geometry_changed.emit(geo,True)
            else:
                self.rb.reset(QgsWkbTypes.PolygonGeometry)

    def canvasMoveEvent(self, mouseEvent):
        if self.rb.numberOfVertices () > 1 and self.active:
            self.rb.removeLastPoint()
            self.rb.addPoint(mouseEvent.mapPoint())
        pass
