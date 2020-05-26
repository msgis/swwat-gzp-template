#!/usr/bin/python
# -*- coding: utf-8 -*-

from qgis.core import QgsProject, QgsPointXY, QgsSnappingUtils
from qgis.gui import QgsMapTool, QgsVertexMarker

from PyQt5.QtCore import pyqtSignal, Qt


class GTOPointTool(QgsMapTool):
    canvasReleased = pyqtSignal(QgsPointXY, bool)
    isActive = pyqtSignal(bool)

    def __init__(self, iface, canvas, useSnapped=True):
        super(GTOPointTool, self).__init__(canvas)

        self.setCursor(Qt.CrossCursor)

        # sta vars
        self.iface = iface
        self.canvas = self.iface.mapCanvas()
        self.snapper = None
        self.marker = None
        self.useSnapped = useSnapped
        self.prj = QgsProject.instance()

        self.marker = QgsVertexMarker(self.canvas)
        self.marker.setColor(Qt.red)
        self.marker.setIconSize(7)
        self.marker.setIconType(QgsVertexMarker.ICON_BOX)
        self.marker.setPenWidth(3)

        self.snapConfig = self.prj.snappingConfig()  # QgsSnappingConfig
        self.setSnapping(self.prj.snappingConfig())
        # signals
        self.prj.snappingConfigChanged.connect(self.setSnapping)

    def setSnapping(self, config):
        self.snapConfig = config
        self.snapper = QgsSnappingUtils(self.canvas)
        self.snapper.setConfig(self.snapConfig)
        self.snapper.setMapSettings(self.canvas.mapSettings())

    def canvasMoveEvent(self, event):
        point = self.toMapCoordinates(event.pos())
        if self.snapConfig.enabled() and self.useSnapped:
            self.isSnapped(point)
        else:
            self.marker.hide()

    def canvasReleaseEvent(self, event):
        point = self.toMapCoordinates(event.pos())
        if self.useSnapped:
            point, isnaped = self.isSnapped(point)
            self.canvasReleased.emit(point, isnaped)
        else:
            self.canvasReleased.emit(point, False)

    def reset_marker(self):
        self.marker.hide()

    def activate(self):
        self.isActive.emit(True)
        QgsMapTool.activate(self)

    def deactivate(self):
        self.marker.hide()
        self.isActive.emit(False)
        QgsMapTool.deactivate(self)

    def isSnapped(self, pointxy):
        matchres = self.snapper.snapToMap(pointxy)  # QgsPointLocator.Match
        if matchres.isValid():
            self.marker.setCenter(matchres.point())
            self.marker.show()
            return matchres.point(), True
        else:
            self.marker.hide()
            return pointxy, False
