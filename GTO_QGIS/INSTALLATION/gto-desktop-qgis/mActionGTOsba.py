#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5.QtGui import *
import qgis

def run(id, gtotool, config, debug):
    try:
        #tool data
        layers = config['layers']
        info = gtotool.info
    except Exception as e:
        gtotool.info.err(e)
    try:
        for lyr in layers:
            layer = qgis.core.QgsProject.instance().mapLayersByName(lyr['name'])
            method = lyr['method']
            if layer:
                layer = layer[0]  # duplicte names => take the first
                #filter
                filter=lyr['filter']
                if not filter is None:
                    if debug: gtotool.info.log(filter)
                    filter=filter.replace("[","")#if using old filter strings from arcgisGTO-sba
                    filter = filter.replace("]", "")
                    layer.setSubsetString(filter)
                #select
                expression=lyr['select']
                if not expression is None:
                    expression=expression.replace("[","")#if using old filter strings from arcgisGTO-sbaW
                    expression = expression.replace("]", "")
                    ids = []
                    expr = qgis.core.QgsExpression(expression)
                    request = qgis.core.QgsFeatureRequest(expr)
                    it = layer.getFeatures(request)
                    ids = [i.id() for i in it]
                    if method == 1:#add
                        selected = layer.selectedFeatures()
                        selectedIds =[i.id() for i in selected]
                        ids.extend(selectedIds)
                    elif method == 2:#remove
                        selected = layer.selectedFeatures()
                        selectedIds = [i.id() for i in selected]
                        ids=[i for i in ids if i not in selectedIds]
                    elif method == 3:#intersection
                        selected = layer.selectedFeatures()
                        selectedIds = [i.id() for i in selected]
                        ids= list(set(ids) & set(selectedIds))
                    elif method == 4:#remove inverse
                        selected = layer.selectedFeatures()
                        selectedIds = [i.id() for i in selected]
                        ids=[i for i in selectedIds if i not in ids]
                    layer.selectByIds(ids)
    except Exception as e:
        gtotool.info.err(e)