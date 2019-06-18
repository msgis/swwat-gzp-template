#!/usr/bin/python
# -*- coding: utf-8 -*-

from builtins import str
from builtins import object
from qgis.core import QgsProject,QgsWkbTypes,QgsVectorLayerUtils

class run(object):
    def __init__(self, id, gtotool, config, debug):
        super(run, self).__init__()
        try:
            #tool data
            targetlayer = config['targetlayer']
            #init
            iface=  gtotool.iface
            prj = QgsProject.instance()
            layPoly = iface.activeLayer()
            layLine = QgsProject.instance().mapLayersByName(targetlayer)[0]
            if not layLine.isEditable(): layLine.startEditing()
            layLine.beginEditCommand("New feature")
            for f in layPoly.selectedFeatures():
                geo = f.geometry().convertToType(QgsWkbTypes.LineGeometry)
                feature = QgsVectorLayerUtils.createFeature(layLine)
                feature.setGeometry(geo)
                layLine.addFeatures([feature])
                layLine.updateFeature(feature)
                #layLine.dataProvider().addFeatures([feature])#no roll back because no edit buffer/beginedit!
            layLine.endEditCommand()
        except Exception as e:
            gtotool.info.err(e)