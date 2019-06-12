#!/usr/bin/python
# -*- coding: utf-8 -*-

from qgis.core import QgsProject, QgsVectorLayer

def run(id, gtotool, config, debug):
    try:
        #gto
        info = gtotool.info
        iface = gtotool.iface
        gtomain= gtotool.gtomain
        #tool data
        mode=config["mode"]#"all"/"current"/"<layername>"
        selectioncount_0 = config["selectioncount_0"]
        selectioncount_1 = config["selectioncount_1"]
        selectioncount_n = config["selectioncount_n"]
        selectioncount_else = config["selectioncount_else"]
        n = config["n"]
    except Exception as e:
        info.err(e)
    try:
        selcount = 0
        if n is None: n=0
        if mode is None: mode="current"
        if mode == "current":#active layer
            layer = iface.mapCanvas().currentLayer()
            selcount = layer.selectedFeatureCount()
        elif mode == "all":#selection on map
            for layer in QgsProject.instance().mapLayers().values():
                if isinstance(layer, QgsVectorLayer):
                    selcount = selcount + layer.selectedFeatureCount()
        else:#selection on layer
            layer = QgsProject.instance().mapLayersByName(mode)
            if layer:
                layer = layer[0]  # duplicte names => take the first
                selcount = layer.selectedFeatureCount()
            else:
                info.log("Layer %s not found!" % mode)
                return
        if debug:
            info.log ("Mode: %s" % mode)
            info.log ("Selection count = %i" % selcount)
        if selcount == 0:
            gtomain.runcmd(selectioncount_0)
        elif selcount == 1:
            gtomain.runcmd(selectioncount_1)
        elif selcount == n:
            gtomain.runcmd(selectioncount_n)
        else:
            gtomain.runcmd(selectioncount_else)
    except Exception as e:
        info.err(e)
