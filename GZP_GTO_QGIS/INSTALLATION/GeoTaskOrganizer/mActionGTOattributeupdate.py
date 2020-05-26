#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import qgis

def run(id, gtotool, config, debug):
    iface = gtotool.iface
    info = gtotool.info
    try:
        # get metadata
        layer = config.get("layer",None)
        selection = config.get("selection",True)
        attributes = config.get("attributes",{})
        tools=config.get("tools",[])
        # do work
        if layer is None:
            layer = iface.activeLayer()
        else:
            layer = qgis.core.QgsProject.instance().mapLayersByName(layer)[0]
        provider = layer.dataProvider()  # QgsVectorDataProvider
        fields = provider.fields()  # QMap<int, QgsField>
        if not layer.isEditable(): layer.startEditing()
        layer.beginEditCommand("attribute update")
        features = []
        if selection:
            features = layer.selectedFeatures()
        else:
            features = layer.getFeatures()
        for f in features:
            for a,v in list(attributes.items()):
                if debug: info.log ( "id:",f.id(),"attr:",a,"value:",v)
                f[a] = fields.field(a).convertCompatible(v)
                layer.updateFeature(f)
        layer.endEditCommand()
        gtotool.gtomain.runcmd(tools)
        return True
    except Exception as e:
        info.err(e)
        try:
            layer.destroyEditCommand()
        except:
            pass

