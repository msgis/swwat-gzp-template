#!/usr/bin/python
# -*- coding: utf-8 -*-

from builtins import str

from qgis.core import QgsProject

import os

def run(id, gtotool, config, debug):
    try:
        #init
        iface = gtotool.iface
        info = gtotool.info
        #metadata
        layer = config['layer']
        field = config['field']
        onlyfirst = config['onlyfirst']
        #do
        if layer is None:
            layer = iface.activeLayer()
        else:
            layer = QgsProject.instance().mapLayersByName(layer)[0]
        for feat in layer.selectedFeatures():
            file= feat[field]
            try:
                if file:
                    if debug: info.log (file)
                    os.startfile(str(file))
                else:
                    info.gtoWarning('Feld <{0}> ist leer!'.format(field))
            except Exception as e:
                info.gtoWarning(e.args)
            if onlyfirst: return True
        return True
    except Exception as e:
        info.err(e)