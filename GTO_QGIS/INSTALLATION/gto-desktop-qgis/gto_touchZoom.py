#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from qgis.core import *
from qgis.gui import *

class TouchZoom(QgsMapTool):
    def __init__(self, canvas, gtomain):
        QgsMapTool.__init__(self, canvas)
        self.gtomain = gtomain
        self.mapcanvas = canvas
        self.info = gtomain.info
        self.pinch = False
        self.filter =MapCanvasFilter(self.mapcanvas, self.gtomain)
        #self.mapcanvas.installEventFilter(self.filter)
        self.mapcanvas.grabGesture(Qt.PinchGesture)

    def gestureEvent(self, e):
        try:
            gesture = e.gesture(Qt.PinchGesture)
            if gesture:
                if gesture.state() == Qt.GestureStarted:
                    self.pinch = True
                if gesture.state() == Qt.GestureFinished:
                    self.pinch = False
                    self.mapcanvas.setMagnificationFactor(1)
                    rect = self.mapcanvas.extent()
                    rect.scale(1 / gesture.totalScaleFactor(), self.mappostion(gesture))
                    self.mapcanvas.setExtent(rect)
                    self.mapcanvas.refresh()
                if self.pinch:# and gesture.state() == Qt.GestureUpdated:
                    self.mapcanvas.setMagnificationFactor(gesture.totalScaleFactor())
                return True
            else:
                if self.pinch: return True
            return False
        except Exception as e:
            self.info.err(e)

    def mappostion(self, gesture):
        pos = gesture.centerPoint().toPoint()
        pos = self.mapcanvas.mapFromGlobal(pos)
        center = self.mapcanvas.getCoordinateTransform().toMapPoint(pos.x(), pos.y())
        return center

    def canvasReleaseEvent(self, mouseEvent):
        self.info.log(mouseEvent.x(), mouseEvent.y())

class MapCanvasFilter(QObject):
    def __init__(self, mapcanvas, gtomain, parent=None):
        super().__init__()
        self.info = gtomain.info
        self.pinch = False
        self.mapcanvas = mapcanvas

    def eventFilter(self,  obj,  event):
        return False
        try:
            self.info.log(event.type())
            #print (event.type)
            if event.type() == QGestureEvent.Gesture:
                    event.accept()
                    #print ('gesture event',event)
                    gesture = event.gesture(Qt.PinchGesture)
                    #print ('QGesture',event.gesture(Qt.PinchGesture))
                    if gesture:
                        if gesture.state()==Qt.GestureStarted:
                            self.pinch = True
                        if gesture.state() == Qt.GestureFinished:
                            self.mapcanvas.setMagnificationFactor(1)
                            rect = self.mapcanvas.extent()
                            rect.scale(1 / gesture.totalScaleFactor(), self.mappostion(gesture))
                            self.mapcanvas.setExtent(rect)
                            self.mapcanvas.refresh()
                            self.pinch = False
                        if gesture.state() == Qt.GestureUpdated and self.pinch:
                            self.mapcanvas.setMagnificationFactor(gesture.totalScaleFactor())
                            #self.mapcanvas.refresh()
                        #event.accept()
                        #print ("pinch", self.pinch)
                        return True
                    else:
                        if self.pinch: return True
                    return False
            return False
        except Exception as e:
            self.info.err(e)
            return False

    def mappostion(self, gesture):
        try:
            pos = gesture.centerPoint().toPoint()
            pos = self.mapcanvas.mapFromGlobal(pos)
            center = self.mapcanvas.getCoordinateTransform().toMapPoint(pos.x(), pos.y())
            return center
        except Exception as e:
            self.info.err(e)