#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import QAction

from qgis.core import QgsProject, QgsWkbTypes, QgsCoordinateTransform, QgsPointXY, QgsPoint
from qgis.gui import QgsMapToolIdentify, QgsMapMouseEvent


class run(QObject):
    def __init__(self, id, gtotool, config, debug):
        super(run, self).__init__()
        self.debug = debug
        self.info = gtotool.info
        self.iface = gtotool.iface
        self.act = self.sender()
        self.act.setCheckable(True)
        try:
            # create tool
            self.curTool = SelectPolygonTool(self, self.iface.mapCanvas(), config)  # , Qt.PointingHandCursor)
            self.iface.mapCanvas().setMapTool(self.curTool)
            self.act.setChecked(True)
            self.curTool.deactivated.connect(lambda: self.act.setChecked(False))
        except Exception as e:
            self.info.err(e)


class SelectPolygonTool(QgsMapToolIdentify):
    def __init__(self, gtoObj, canvas, config, cursorstyle=Qt.CrossCursor):
        self.info = gtoObj.info
        self.debug = gtoObj.debug
        self.canvas = canvas
        self.layer = None
        QgsMapToolIdentify.__init__(self, canvas)
        try:
            cursor = QCursor()
            cursor.setShape(cursorstyle)
            self.setCursor(cursor)
            # metadata
            layer = config.get("layer", None)
            if layer is not None:
                self.layer = QgsProject.instance().mapLayersByName(layer)[0]
            self.smallest = config.get("smallest", True)
            if self.debug: self.info.log("SelectPolygonTool::init")
        except Exception as e:
            self.info.err(e)

    def canvasReleaseEvent(self, mouseEvent):
        try:
            if self.debug: self.info.log("SelectPolygonTool::on_click", type(mouseEvent))
            # sourceCrs = QgsProject.instance().crs()
            # pointXY = QgsPointXY(mouseEvent.x(), mouseEvent.y())
            # point = QgsPoint(pointXY)
            if self.layer is None:
                results = self.identify(mouseEvent.x(), mouseEvent.y(), QgsMapToolIdentify.ActiveLayer,
                                        QgsMapToolIdentify.VectorLayer)
            else:
                # destCrs = self.layer.crs()
                # tr = QgsCoordinateTransform(sourceCrs, destCrs, QgsProject.instance())
                # point.transform(tr)
                results = self.identify(mouseEvent.x(), mouseEvent.y(), [self.layer],
                                        self.TopDownStopAtFirst)  # without self.TopDownStopAtFirst =>popup menu!
            if len(results) > 0:
                self.on_click(mouseEvent, results)
        except Exception as e:
            self.info.err(e)

    def on_click(self, MouseEvent, results):
        try:
            if self.debug: self.info.log("on_click")
            if MouseEvent.button() == Qt.LeftButton:
                if self.debug: self.info.log("on_click: left button", type(results), results)
                foundfeat = None
                foundarea = 0
                for res in results:
                    self.info.log("res", res.mFeature.id())
                    if res.mLayer.geometryType() == QgsWkbTypes.GeometryType.PolygonGeometry:
                        feat = res.mFeature
                        area = feat.geometry().area()
                        if self.debug: self.info.log("area:", area)
                        if foundarea == 0:
                            foundarea = area
                            foundfeat = feat
                        if self.smallest:
                            if area < foundarea:
                                foundarea = area
                                foundfeat = feat
                        else:
                            if area > foundarea:
                                foundarea = area
                                foundfeat = feat
                if foundfeat is not None:
                    if self.debug: self.info.log(foundfeat.id())
                    res.mLayer.selectByIds([foundfeat.id()])
                    self.canvas.flashFeatureIds(res.mLayer,[foundfeat.id()])
        except Exception as e:
            self.info.err(e)
