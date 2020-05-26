#!/usr/bin/python
# -*- coding: utf-8 -*-

from builtins import str
from builtins import object
from qgis.core import  QgsProject,QgsMapLayer,QgsVectorLayer,QgsDataProvider,QgsDataSourceUri
from PyQt5.QtCore import Qt

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
            root = prj.layerTreeRoot()
            for g in layers:
                try:
                    group=g['name']
                    #state=g['state']
                    state = g['visible']
                    if debug: gtotool.info.log(group + "/" + str(state))
                    node=prj.layerTreeRoot().findGroup(group)#QgsLayerTreeNode
                    if node: node.setItemVisibilityCheckedRecursive(state)
                except ValueError as e:
                    gtotool.info.err(e)
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
                    #symbology
                    symbology = lyr.get("symbology",None)#list
                    if symbology is not None:
                        if isinstance(symbology,list):
                            ltl = root.findLayer(layer.id())#QgsLayerTreeLayer
                            ltm = iface.layerTreeView().model()
                            legendNodes = ltm.layerLegendNodes(ltl)
                            for ln in legendNodes:  # QgsLayerTreeModelLegendNode
                                for d in symbology:#dic
                                    symLayerName= d.get("name")
                                    if symLayerName == ln.data(0):
                                        if d.get("visible",True):
                                            ln.setData(Qt.Checked, Qt.CheckStateRole)
                                        else:
                                            ln.setData(Qt.Unchecked, Qt.CheckStateRole)
                                        break
                        else:
                            ltl = root.findLayer(layer.id())#QgsLayerTreeLayer
                            ltm = iface.layerTreeView().model()
                            legendNodes = ltm.layerLegendNodes(ltl)
                            for ln in legendNodes:  # QgsLayerTreeModelLegendNode
                                if symbology:
                                    ln.setData(Qt.Checked, Qt.CheckStateRole)
                                else:
                                    ln.setData(Qt.Unchecked, Qt.CheckStateRole)
            #set active layer:
            if activelayer:
                layer = prj.mapLayersByName(activelayer)
                if layer:
                    layer = layer[0]  # duplicte names => take the first
                    prj.layerTreeRoot().findLayer(layer.id()).setItemVisibilityCheckedParentRecursive(True)
                    iface.setActiveLayer(layer)
        except Exception as e:
            gtotool.info.err(e)

