#!/usr/bin/python
# -*- coding: utf-8 -*-

from builtins import str
from builtins import object
from qgis.core import QgsProject, QgsWkbTypes, QgsVectorLayerUtils, QgsCoordinateTransform


class run(object):
    def __init__(self, id, gtotool, config, debug):
        super(run, self).__init__()
        try:
            # tool data
            targetlayer = config['targetlayer']
            tools=config.get("tools",[])
            # init
            self.iface = gtotool.iface
            self.canvas = self.iface.mapCanvas()
            self.layPoly = self.iface.activeLayer()
            if self.layPoly.geometryType() == QgsWkbTypes.GeometryType.PolygonGeometry:
                layLine = QgsProject.instance().mapLayersByName(targetlayer)[0]
                if not layLine.isEditable(): layLine.startEditing()
                layLine.beginEditCommand("New feature")
                for f in self.layPoly.selectedFeatures():
                    geo = f.geometry().convertToType(QgsWkbTypes.LineGeometry)
                    # transform
                    sourceCrs = self.layPoly.crs()
                    destCrs = layLine.crs()
                    tr = QgsCoordinateTransform(sourceCrs, destCrs, QgsProject.instance())
                    geo.transform(tr)
                    # create feature
                    feature = QgsVectorLayerUtils.createFeature(layLine)
                    feature.setGeometry(geo)
                    layLine.addFeatures([feature])
                    layLine.updateFeature(feature)
                    # layLine.dataProvider().addFeatures([feature])#no roll back because no edit buffer/beginedit!
                layLine.endEditCommand()
                gtotool.gtomain.runcmd(tools)
        except Exception as e:
            gtotool.info.err(e)
            try:
                layLine.destroyEditCommand()
            except:
                pass
