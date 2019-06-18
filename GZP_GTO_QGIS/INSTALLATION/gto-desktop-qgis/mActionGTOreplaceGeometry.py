#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from qgis.core import *
from qgis.gui import QgsMapToolEmitPoint, QgsRubberBand

#from .gto_identify import IdentifyTool

class run(QObject):
    def __init__(self, id, gtotool, config, debug):
        super(run, self).__init__()
        self.debug = debug
        self.gtotool=gtotool
        self.gtomain =  gtotool.gtomain
        iface = self.gtotool.iface
        try:
            # get metadata
            sourcelayer =QgsProject.instance().mapLayersByName(config["sourcelayer"])[0]
            targetlayer = QgsProject.instance().mapLayersByName(config['targetlayer'])[0]
            iface.setActiveLayer(targetlayer)
            if not targetlayer.isEditable(): targetlayer.startEditing()
            if not sourcelayer.isEditable() : sourcelayer.startEditing()
            #save current tool
            prevTool = iface.mapCanvas().mapTool()
            #create tool
            curTool =self.gtomain.indentifyTool# IdentifyTool(iface.mapCanvas(),layers=[sourcelayer])
            curTool.layers = [sourcelayer]
            #create rubberband
            myrubber = QgsRubberBand(iface.mapCanvas(), QgsWkbTypes.LineGeometry)
            myrubber.setColor(QColor(Qt.blue))
            myrubber.setLineStyle(Qt.PenStyle(Qt.DashDotLine))
            myrubber.setWidth(2)

            def showrubberband(currentPos):
                if myrubber and myrubber.numberOfVertices():
                    myrubber.removeLastPoint()
                    myrubber.addPoint(currentPos)

            iface.mapCanvas().xyCoordinates.connect(showrubberband)

            #references
            self.sourcefeat = None
            self.feat = None
            self.lyr = None
            self.rubbers = []

            def highlightfeature(layer, feature, color = QColor(Qt.red)):
                r = QgsRubberBand(iface.mapCanvas())
                color.setAlpha(20)
                r.setColor(color)
                r.setToGeometry(feature.geometry(), layer)
                self.rubbers.append(r)
                r.show()

            def on_click(mouseEvent, lyr, feat):
                try:
                    if myrubber.numberOfVertices() < 2:
                        if feat.isValid():
                            self.sourcefeat = feat
                            highlightfeature(sourcelayer, self.sourcefeat)
                            myrubber.addPoint(mouseEvent.mapPoint())
                            curTool.layers=[targetlayer]
                    else:
                        newgeo = QgsGeometry(self.sourcefeat.geometry())
                        if mouseEvent.button() == Qt.LeftButton:#replace the target geometry
                            if feat.isValid():
                                try:
                                    targetlayer.beginEditCommand("Replace geometry")
                                    # set new geometry (QgsGeometry instance) for a feature
                                    targetlayer.changeGeometry(feat.id(), newgeo)
                                    targetlayer.endEditCommand()
                                    deleteSource()
                                    myrubber.removeLastPoint()
                                    resetscreen()
                                    iface.mapCanvas().refresh()
                                    curTool.layers = [sourcelayer]
                                except Exception as e:
                                    gtotool.info.gtoWarning(e.args)
                                    targetlayer.destroyEditCommand()
                        elif mouseEvent.button() == Qt.RightButton:  # add a new feature
                            try:
                                #if debug: self.gtotool.info.log("clicked:",mouseEvent.mapPoint())
                                targetlayer.beginEditCommand("New feature")
                                feature = QgsFeature()
                                feature.setGeometry(newgeo)
                                targetlayer.addFeatures([feature])
                                targetlayer.endEditCommand()
                                deleteSource()
                                myrubber.removeLastPoint()
                                resetscreen()
                                iface.mapCanvas().refresh()
                                curTool.layers = [sourcelayer]
                            except Exception as e:
                                gtotool.info.e(e)
                                targetlayer.destroyEditCommand()
                except Exception as e:
                    gtotool.info.err(e)

            def deleteSource():
                try:
                    sourcelayer.beginEditCommand("delete feature")
                    sourcelayer.dataProvider().deleteFeatures([self.sourcefeat.id()])
                    self.sourcefeat = None
                    sourcelayer.endEditCommand()
                except Exception as e:
                    gtotool.info.gtoWarning(e.args)
                    sourcelayer.destroyEditCommand()

            def resetscreen():
                for r in self.rubbers:
                    r.reset()
                    iface.mapCanvas().scene().removeItem(r)

            def tool_changed(tool):#another tool was activated
                iface.mapCanvas().xyCoordinates.disconnect(showrubberband)
                iface.mapCanvas().mapToolSet.disconnect(tool_changed)
                self.gtotool.action.setChecked(False)
                #curTool.deleteLater()
                iface.mapCanvas().scene().removeItem(myrubber)
                resetscreen()

            def on_mouse_clicked(mouseEvent):
                if debug: self.gtotool.info.log("clicked:", mouseEvent.mapPoint())

            curTool.geomIdentified.connect(on_click)
            iface.mapCanvas().setMapTool(curTool)
            self.gtotool.action.setCheckable(True)
            self.gtotool.action.setChecked(True)
            iface.mapCanvas().mapToolSet.connect(tool_changed)
            if not debug:
                targetlayer.commitChanges()
                sourcelayer.commitChanges()
        except Exception as e:
            gtotool.info.gtoWarning(e.args)