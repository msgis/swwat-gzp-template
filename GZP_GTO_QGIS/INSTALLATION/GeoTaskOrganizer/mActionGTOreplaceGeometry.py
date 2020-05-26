#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from qgis.core import QgsProject, QgsWkbTypes, QgsGeometry, QgsFeature, QgsVectorLayerUtils, QgsCoordinateTransform
from qgis.gui import QgsMapToolEmitPoint, QgsRubberBand, QgsMapToolIdentifyFeature


# from .gto_identify import IdentifyTool

class run(QObject):
    def __init__(self, id, gtotool, config, debug):
        super(run, self).__init__()
        self.debug = debug
        self.gtotool = gtotool
        self.gtomain = gtotool.gtomain
        self.info = gtotool.info
        self.iface = self.gtotool.iface
        self.act = self.sender()
        self.act.setCheckable(True)
        self.sourcefeat = None
        self.rubbers = []
        try:
            # create rubberband
            self.rubber = QgsRubberBand(self.iface.mapCanvas(), QgsWkbTypes.LineGeometry)
            self.rubber.setColor(QColor(Qt.blue))
            self.rubber.setLineStyle(Qt.PenStyle(Qt.DashDotLine))
            self.rubber.setWidth(2)

            # get metadata
            self.sourcelayer = QgsProject.instance().mapLayersByName(config["sourcelayer"])[0]
            self.targetlayer = QgsProject.instance().mapLayersByName(config['targetlayer'])[0]
            self.iface.setActiveLayer(self.targetlayer)
            # start edit
            if not self.targetlayer.isEditable(): self.targetlayer.startEditing()
            if not self.sourcelayer.isEditable(): self.sourcelayer.startEditing()
            # mouse move
            self.canvas = self.iface.mapCanvas()
            self.canvas.xyCoordinates.connect(self.mouse_move)
            # set maptool
            self.mapTool = QgsMapToolIdentifyFeature(self.canvas)
            self.mapTool.setLayer(self.sourcelayer)
            self.canvas.setMapTool(self.mapTool)
            self.mapTool.featureIdentified.connect(self.feature_Identified)
            self.mapTool.deactivated.connect(self.reset_tool)
            self.act.setChecked(True)
        except Exception as e:
            self.info.err(e)

    def mouse_move(self, pointXY):
        try:
            if self.sourcefeat is not None:
                if self.rubber.numberOfVertices() > 1:
                    self.rubber.removeLastPoint()
                self.rubber.addPoint(pointXY)
        except Exception as e:
            self.info.err(e)

    def feature_Identified(self, feature):
        try:
            if self.sourcefeat is None:
                self.sourcefeat = feature
                self.mapTool.setLayer(self.targetlayer)
            else:
                # transform
                geo = self.sourcefeat.geometry()
                sourceCrs = self.sourcelayer.crs()
                destCrs = self.targetlayer.crs()
                tr = QgsCoordinateTransform(sourceCrs, destCrs, QgsProject.instance())
                geo.transform(tr)
                # change geometry
                self.targetlayer.beginEditCommand("New feature")
                self.targetlayer.changeGeometry(feature.id(), geo)
                self.targetlayer.endEditCommand()
                # cleanup
                self.rubber.reset()
                self.iface.mapCanvas().refresh()
                self.mapTool.setLayer(self.sourcelayer)
                self.sourcefeat = None
            print("feature selected : " + str(feature.id()))
        except Exception as e:
            self.info.err(e)

    def reset_tool(self):
        try:
            self.act.setChecked(False)
            self.iface.mapCanvas().scene().removeItem(self.rubber)
        except Exception as e:
            self.info.err(e)
