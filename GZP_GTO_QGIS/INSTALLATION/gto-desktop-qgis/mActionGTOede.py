#!/usr/bin/python
# -*- coding: utf-8 -*-

from qgis.core import QgsProject, QgsSnappingConfig, QgsVectorLayer

def run(id, gtotool, config, debug):
    try:
        #common tool objects
        iface = gtotool.iface
        info = gtotool.info
        gtomain = gtotool.gtomain
        #tool data
        activelayer =  config.get('active_layer',None)
        active_tool = config['active_tool']
        snapmode = config['snap_mode']
        topologicalediting = config['topologicalediting']
        snapping_on_intersection = config['snapping_on_intersection']
        #default snappings
        default_snap_type = config['default_snap_type']
        default_snap_tolerance= config['default_snap_tolerance']
        default_snap_tolerance_unit= config['default_snap_tolerance_unit']
        #layers for advanced setting
        layers = config['layers']

        # needed objects
        prj = QgsProject.instance()
        snapconfig = QgsSnappingConfig(prj)
        avoidIntersectLayers=[]

        if snapmode == 0:
            snapconfig.setEnabled(False)
        else:
            # set default snapping
            snapconfig.setMode(snapmode)
            snapconfig.setIntersectionSnapping(snapping_on_intersection)
            snapconfig.setType(default_snap_type)
            snapconfig.setUnits(default_snap_tolerance_unit)
            snapconfig.setTolerance(default_snap_tolerance)

            if snapmode == QgsSnappingConfig.AdvancedConfiguration:
                #disable snapping for all layers
                for maplayername, layer in prj.mapLayers().items():
                    if isinstance(layer, QgsVectorLayer):
                        snaplayer = snapconfig.individualLayerSettings(layer)
                        if layer.name() in layers:
                            snaplayer.setEnabled(True)
                        else:
                            snaplayer.setEnabled(False)
                        snapconfig.setIndividualLayerSettings(layer, snaplayer)
                #set settings for layers
                for setting in layers:
                    if debug: info.log("settings:",setting)
                    maplayer = prj.mapLayersByName(setting['name'])[0]
                    snaplayer = snapconfig.individualLayerSettings(maplayer)
                    snaplayer.setEnabled(setting.get('snap', snaplayer.enabled()))
                    snaplayer.setUnits(setting.get('units', snaplayer.units()))
                    snaplayer.setTolerance(setting.get('tolerance', snaplayer.tolerance()))
                    snaplayer.setType(setting.get('mode',setting.get('snap_type' ,snaplayer.type())))
                    snapconfig.setIndividualLayerSettings(maplayer, snaplayer)
                    if setting.get('avoidintersection', True):
                        avoidIntersectLayers.append(maplayer)

                prj.avoidIntersectionsLayers = avoidIntersectLayers
            #enable the settings (snapping)
            snapconfig.setEnabled(True)

        #set topology editing for project
        prj.setTopologicalEditing(topologicalediting)
        #set snappingconfig to project
        prj.setSnappingConfig(snapconfig)
    except IndexError as e:
        info.err(e)
    try:
        #set activelayer
        activelayer = prj.mapLayersByName(activelayer)
        if activelayer: activelayer = activelayer[0]
        if isinstance(activelayer,QgsVectorLayer):
            iface.setActiveLayer(activelayer)
    except IndexError as e:
        info.err(e)
    try:
        #start editing
        layer = iface.activeLayer()
        if not layer.isEditable():
            layer.startEditing()
        # run active tool
        if active_tool:
            gtomain.runcmd(active_tool)
    except IndexError as e:
        info.err(e)


