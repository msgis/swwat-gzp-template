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
            self.active = False
            #get the toolbar
            module = self.gtomain.helper.importModule("gto_bufferselecttoolbar")
            self.toolbar= module.BufferSelectToolbar(self)#=> all references to toolbar
            #create tool and activate
            self.action.setCheckable(True)
            #self.action.setChecked(True)
            self.curTool = MapTool(self.iface.mapCanvas())#the maptool
            self.curTool.geometry_changed.connect(self.setGeometryToToolbar)
            self.curTool.tool_deactivated.connect(lambda : self.toolbar.setHidden(True))
            self.iface.mapCanvas().setMapTool(self.curTool)
            self.toolbar.setHidden(False)
        except Exception as e:
            self.info.err(e)

    def setGeometryToMapTool(self, geo):#from the toolbar, buffered
        self.curTool.setGeometry(geo)#=>Maptool

    def setGeometryToToolbar(self, geo, isValid):#from the maptool
        isCircle=True
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
        self.rb = QgsRubberBand(self.canvas)
        self.rb.setStrokeColor(QColor(255, 0, 0, 40))
        self.rb.setFillColor(mycolor)
        self.rb.setLineStyle(Qt.PenStyle(Qt.SolidLine))
        self.rb.setWidth(2)
        self.center = None
        self.segments = 120#circle of 30 segments

    def setCursorStyle(self):
        cursor = QCursor()
        cursor.setShape(self.cursorStyle)
        self.setCursor(cursor)

    def activate(self):
        self.caller.setChecked(True)
        self.setCursorStyle()
        self.geometry_changed.emit(QgsGeometry(),False)

    def deactivate(self):
        self.canvas.scene().removeItem(self.rb)
        self.tool_deactivated.emit()
        self.caller.setChecked(False)
        QgsMapTool.deactivate(self)

    def setGeometry(self,geo):
        self.rb.setToGeometry(geo)

    def canvasPressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.active = True
            self.center = self.toMapCoordinates(e.pos())
            self.geometry_changed.emit(QgsGeometry(),False)
            self.rb.reset()
        pass

    def canvasMoveEvent(self, QgsMapMouseEvent):
        if self.active:
            cp = self.toMapCoordinates(QgsMapMouseEvent.pos())
            self.rbcircle(self.rb, self.center, cp, self.segments)
            self.geometry_changed.emit(self.rb.asGeometry(),True)
        pass

    def canvasReleaseEvent(self, mouseevent):
        if mouseevent.button() == Qt.LeftButton:
            self.active = False
            self.geometry_changed.emit(self.rb.asGeometry(),True)
        pass

    def rbcircle(self, rb, center, edgePoint, N):
        r = math.sqrt(center.sqrDist(edgePoint))
        rb.reset(QgsWkbTypes.PolygonGeometry)
        for itheta in range(N + 1):
            theta = itheta * (2.0 * math.pi / N)
            rb.addPoint(QgsPointXY(center.x() + r * math.cos(theta), center.y() + r * math.sin(theta)))
        return