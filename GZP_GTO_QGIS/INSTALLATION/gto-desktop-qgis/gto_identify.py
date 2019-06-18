#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5.QtGui import *
from PyQt5.QtCore import *

from qgis.core import *
from qgis.gui import *

class IdentifyTool(QgsMapToolIdentify):
    geomIdentified = pyqtSignal(QgsMapMouseEvent, QgsVectorLayer, QgsFeature)
    mouseevent = pyqtSignal(QgsMapMouseEvent)

    def __init__(self, canvas, pickMode = 'all',cursorstyle = Qt.CrossCursor, layers = None):
        self.canvas = canvas
        QgsMapToolIdentify.__init__(self, canvas)
        self.setCursorStyle(cursorstyle)
        self.setPickMode(pickMode)
        self.layers = layers

    def setPickMode(self, pickMode):
        if pickMode == 'selection':
            self.selectionMode = self.LayerSelection
        elif pickMode == 'active':
            self.selectionMode = self.ActiveLayer
        else:
            self.selectionMode = self.TopDownStopAtFirst

    def setCursorStyle(self,cursorstyle):
        cursor = QCursor()
        cursor.setShape(cursorstyle)
        self.setCursor(cursor)

    def setLayers(self,layers):
        self.layers = layers

    def canvasReleaseEvent(self, mouseEvent):
        '''
        try:
            results = self.identify(mouseEvent.x(), mouseEvent.y(), self.LayerSelection, self.VectorLayer)
        except:
        '''

        feat = QgsFeature()
        lyr = QgsVectorLayer()
        try:
            if self.layers is not None:
                results = self.identify(mouseEvent.x(), mouseEvent.y(), self.layers, self.selectionMode)
            else:
                results = self.identify(mouseEvent.x(), mouseEvent.y(), self.selectionMode, self.VectorLayer)
            if len(results) > 0:
                lyr = results[0].mLayer
                feat = QgsFeature(results[0].mFeature)
        except:
            pass
        try:
            self.geomIdentified.emit(mouseEvent, lyr, feat)
        except:
            pass

    def canvasMoveEvent(self, QgsMapMouseEvent):  # real signature unknown; restored from __doc__
        """ QgsMapToolIdentify.canvasMoveEvent(QgsMapMouseEvent) """