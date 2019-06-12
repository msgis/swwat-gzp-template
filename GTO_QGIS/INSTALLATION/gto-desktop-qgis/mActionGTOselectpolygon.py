#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5.QtGui import *
from PyQt5.QtCore import *

from qgis.core import *
from qgis.gui import *

class run(QObject):
    def __init__(self, id, gtotool, config, debug):
        super(run, self).__init__()
        self.debug = debug
        self.info = gtotool.info
        iface =gtotool.iface
        try:
            # get metadata
            layer = config["layer"]
            smallest = config["smallest"]
            if layer is not None:
                layer = QgsProject.instance().mapLayersByName(layer)[0]
            # create tool
            curTool = SelectPolygonTool(self, iface.mapCanvas(),layer,Qt.PointingHandCursor)

            def on_click(MouseEvent, results):
                try:
                    if self.debug: self.info.log("on_click")
                    if MouseEvent.button() == Qt.LeftButton:
                        if self.debug: self.info.log("on_click: left button",type(results),results)
                        foundfeat = None
                        foundarea = 0
                        for res in results:
                            self.info.log("res",res.mFeature)
                            if res.mLayer.wkbType()== QgsWkbTypes.Polygon:
                                feat = res.mFeature
                                area = feat.geometry().area()
                                if self.debug: self.info.log("area:",area)
                                if foundarea == 0:
                                    foundarea = area
                                    foundfeat = feat
                                if smallest:
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
                except Exception as e:
                    self.info.err(e)

            def tool_changed(tool):  # another tool was activated
                iface.mapCanvas().mapToolSet.disconnect(tool_changed)
                curTool.deleteLater()

            curTool.geomIdentified.connect(on_click)
            iface.mapCanvas().setMapTool(curTool)
            iface.mapCanvas().mapToolSet.connect(tool_changed)
        except Exception as e:
            self.info.err(e)

class SelectPolygonTool(QgsMapToolIdentify):
    geomIdentified = pyqtSignal(QgsMapMouseEvent, QVariant)
    def __init__(self, gtoObj, canvas,layer, cursorstyle =  Qt.CrossCursor):
        self.info = gtoObj.info
        self.debug = gtoObj.debug
        self.canvas = canvas
        QgsMapToolIdentify.__init__(self, canvas)
        cursor = QCursor()
        cursor.setShape(cursorstyle)
        self.setCursor(cursor)
        self.layer =layer
        if self.debug: self.info.log("SelectPolygonTool::init")

    def canvasReleaseEvent(self, mouseEvent):
        if self.debug: self.info.log("SelectPolygonTool::on_click",type(mouseEvent))
        if self.layer is None:
            results = self.identify(mouseEvent.x(), mouseEvent.y(), self.ActiveLayer, self.VectorLayer)
            self.geomIdentified.emit(mouseEvent, results)
        else:
            results = self.identify(mouseEvent.x(), mouseEvent.y(),[self.layer])
            self.geomIdentified.emit(mouseEvent, results)