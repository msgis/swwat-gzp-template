#!/usr/bin/python
# -*- coding: utf-8 -*-

from builtins import str
from builtins import object
from qgis.core import QgsProject,QgsMapLayer,QgsVectorLayer,QgsDataProvider,QgsDataSourceUri

class run(object):
    def __init__(self, id, gtotool, config, debug):
        super(run, self).__init__()

        try:
            #tool data
            activelayer = config.get('active_layer',None)
            layers = config['layers']
            #init
            iface=  gtotool.iface
            prj = QgsProject.instance()
            for g in layers:
                try:
                    group=g['name']
                    #state=g['state']
                    state = g['visible']
                    if debug: gtotool.info.log(group + "/" + str(state))
                    node=prj.layerTreeRoot().findGroup(group)#QgsLayerTreeNode
                    if node: node.setItemVisibilityCheckedRecursive(state)
                except ValueError as e:
                    gtotool.info.gtoWarning(e.args)
            #set layers
            for lyr in layers:
                layer = prj.mapLayersByName(lyr['name'])
                if layer:
                    layer = layer[0]  # duplicte names => take the first
                    visible = lyr['visible']
                    if visible:
                        prj.layerTreeRoot().findLayer(layer.id()).setItemVisibilityCheckedParentRecursive(True)
                    else:
                        prj.layerTreeRoot().findLayer(layer.id()).setItemVisibilityChecked(False)
            #set active layer:
            if activelayer:
                layer = prj.mapLayersByName(activelayer)
                if layer:
                    layer = layer[0]  # duplicte names => take the first
                    prj.layerTreeRoot().findLayer(layer.id()).setItemVisibilityChecked(True)
                    iface.setActiveLayer(layer)
        except Exception as e:
            gtotool.info.err(e)

