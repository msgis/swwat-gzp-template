#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

from qgis.core import QgsProject, QgsWkbTypes, QgsVectorLayer, QgsFeature
from qgis.gui import QgsRubberBand, QgsMapToolIdentify, QgsMapMouseEvent

from PyQt5.QtGui import *
from PyQt5.QtCore import *


class run(QObject):
    def __init__(self, id, gtotool, config, debug):
        super(run, self).__init__()
        self.gtomain = gtotool.gtomain
        self.debug = debug
        self.gtotool = gtotool
        self.iface = self.gtotool.iface
        self.canvas = self.iface.mapCanvas()
        try:
            # get metadata
            sourcelayer = QgsProject.instance().mapLayersByName(config["sourcelayer"])[0]
            targetlayer = QgsProject.instance().mapLayersByName(config['targetlayer'])[0]
            _fields = config['fields']
            self.iface.setActiveLayer(targetlayer)
            if not targetlayer.isEditable(): targetlayer.startEditing()
            # save current tool
            prevTool = self.canvas.mapTool()
            # create tool
            curTool = IdentifyTool(self.canvas)  # QgsMapToolIdentifyFeatur(iface.mapCanvas())
            curTool.setLayer = sourcelayer
            # curTool.featureIdentified.connect(self.feature_Identified)
            # create rubberband
            myrubber = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
            myrubber.setColor(QColor(Qt.blue))
            myrubber.setLineStyle(Qt.PenStyle(Qt.DashDotLine))
            myrubber.setWidth(2)

            def showrubberband(currentPos):
                if myrubber and myrubber.numberOfVertices():
                    myrubber.removeLastPoint()
                    myrubber.addPoint(currentPos)

            self.canvas.xyCoordinates.connect(showrubberband)
            # references
            self.sourcefeat = None
            self.feat = None
            self.lyr = None
            self.rubbers = []

            def on_click(mouseEvent, lyr, feat):
                try:
                    if debug and feat.isValid():
                        gtotool.info.log("identified: layer", lyr.name(), "feat-ID:", feat.id())
                    else:
                        gtotool.info.log("clicked:", mouseEvent.mapPoint())
                    if myrubber.numberOfVertices() < 2:
                        if feat.isValid():
                            self.sourcefeat = feat
                            sourcelayer.selectByIds([self.sourcefeat.id()])
                            myrubber.addPoint(mouseEvent.mapPoint())
                            curTool.layers = [targetlayer]
                    else:
                        if mouseEvent.button() == Qt.LeftButton:
                            if feat.isValid() and feat.id() != self.sourcefeat.id():
                                try:
                                    targetlayer.selectByIds([feat.id()], QgsVectorLayer.AddToSelection)
                                    self.canvas.flashFeatureIds(targetlayer, [feat.id()])
                                    provider = targetlayer.dataProvider()  # QgsVectorDataProvider
                                    fields = provider.fields()  # QMap<int, QgsField>
                                    targetlayer.beginEditCommand("attribute transfer")
                                    for fsource, ftarget in _fields.items():
                                        feat[ftarget] = fields.field(ftarget).convertCompatible(
                                            self.sourcefeat[fsource])  # QgsField
                                    targetlayer.updateFeature(feat)
                                    targetlayer.endEditCommand()
                                except Exception as e:
                                    gtotool.info.err(e)
                                    targetlayer.destroyEditCommand()
                        elif mouseEvent.button() == Qt.RightButton:
                            try:
                                targetlayer.endEditCommand()
                                myrubber.removeLastPoint()
                                resetscreen()
                                self.canvas.refresh()
                                curTool.layers = [sourcelayer]
                            except Exception as e:
                                gtotool.info.err(e)
                                targetlayer.destroyEditCommand()
                except Exception as e:
                    gtotool.info.err(e)

            def resetscreen():
                for r in self.rubbers:
                    self.canvas.scene().removeItem(r)

            def tool_changed(tool):  # another tool was activated
                self.canvas.xyCoordinates.disconnect(showrubberband)
                self.canvas.mapToolSet.disconnect(tool_changed)
                self.gtotool.action.setChecked(False)
                self.canvas.scene().removeItem(myrubber)
                resetscreen()

            curTool.geomIdentified.connect(on_click)
            self.canvas.setMapTool(curTool)
            self.gtotool.action.setCheckable(True)
            self.gtotool.action.setChecked(True)
            self.canvas.mapToolSet.connect(tool_changed)
            if not debug:
                targetlayer.commitChanges()
                sourcelayer.commitChanges()
        except Exception as e:
            gtotool.info.err(e)


class IdentifyTool(QgsMapToolIdentify):
    geomIdentified = pyqtSignal(QgsMapMouseEvent, QgsVectorLayer, QgsFeature)
    mouseevent = pyqtSignal(QgsMapMouseEvent)

    def __init__(self, canvas, pickMode='all', cursorstyle=Qt.CrossCursor, layers=None):
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

    def setCursorStyle(self, cursorstyle):
        cursor = QCursor()
        cursor.setShape(cursorstyle)
        self.setCursor(cursor)

    def setLayers(self, layers):
        self.layers = layers

    def setLayer(self, layer):
        self.layers = [layer]

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
