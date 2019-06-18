#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
from PyQt5.QtCore import *
from qgis.core import QgsProject, QgsProcessing,QgsProcessingFeatureSourceDefinition
import processing
import os

class run(QObject):
    def __init__(self, id, gtotool, config, debug):
        super(run, self).__init__()
        self.debug = debug
        self.gtotool=gtotool
        self.info = gtotool.info
        self.iface = gtotool.iface
        if debug: self.info.log("===================processing=================")
        try:
            algs = config['algs']
            self.outlayer = None
            self.lastlayer = None#last loaded outlayer
            QgsProject.instance().layerWasAdded.connect(self.LayerWasAdded)
            tmplayers = []
            i = 1
            for alg in algs:
                new_layer_name = alg['layer']
                #remove layers from previous tasks
                layers = QgsProject.instance().mapLayersByName(new_layer_name)#list because of possible duplicated names
                if debug: self.info.log("Step 1: delete previous")
                for layer in layers:
                    if debug: self.info.log("Step 1: delete previous", layer.id())
                    if layer.isEditable(): layer.rollBack()
                    QgsProject.instance().removeMapLayer(layer.id())
                #run the algorithmn
                cmd = alg['cmd']
                loadLayer = alg['load']
                parameters = alg['parameters']
                if self.debug: self.info.log("step 2 run alg %i:" % i, cmd,parameters)
                outputs = processing.runAndLoadResults(cmd,parameters)
                if self.debug: self.info.log("Result:", outputs)
                outlayer_id = None
                if self.outlayer:
                    outlayer_id = self.outlayer.id()
                    if debug: self.info.log("outlayer id:",outlayer_id)
                    if self.debug: self.info.log("step 4: rename outlayer <%s> to <%s>:" % (self.outlayer.name(),new_layer_name), outlayer_id)
                    self.outlayer.setName(new_layer_name)  # input for next hardcoded alg
                else:
                    loadLayer = False
                #postprocessing
                if loadLayer == False:
                    if self.debug: self.info.log("step 3: add outlayer for deleting: ", outlayer_id)
                    tmplayers.append(outlayer_id)
                else:
                    group = alg['grouplayer']
                    if group is not None:#move the layer to the group
                        self.MoveToGroup(self.outlayer,group)
                    stylefile = alg['stylefile']
                    if stylefile is not None:
                        if os.path.isfile(stylefile):
                            try:
                                layer = QgsProject.instance().mapLayersByName(new_layer_name)[0]
                                layer.loadNamedStyle(stylefile)
                                layer.triggerRepaint()
                            except Exception as e:
                                self.info.gtoWarning(e.args)
                    self.lastlayer = outlayer_id
                i=i+1
            #finally set the last outlayer active
            if self.lastlayer:
                tmpLayer= QgsProject.instance().mapLayer(self.lastlayer)
                if tmpLayer is not None:
                    self.gtotool.iface.setActiveLayer(tmpLayer)
                    QgsProject.instance().layerTreeRoot().findLayer(tmpLayer.id()).setItemVisibilityCheckedParentRecursive(True)
            self.lastlayer = None
            self.outlayer = None
            QgsProject.instance().layerWasAdded.disconnect(self.LayerWasAdded)
        except Exception as e:
            self.info.gtoWarning(e.args)

        if not self.debug or 1==1:
            for id in tmplayers:
                try:
                    self.info.log("step 5:", "remove tmp layers:",id)
                    QgsProject.instance().removeMapLayer(id)
                except Exception as e:
                    self.info.gtoWarning(e.args)

    def LayerWasAdded(self,layer):#QgsMapLayer
        if self.debug: self.info.log(layer.name())
        self.outlayer = layer

    def MoveToGroup(self,layer, groupname):
        try:
            if layer is not None:
                toc = QgsProject.instance().layerTreeRoot()  # QgsLayerTree
                if groupname is None:
                    toc.addLayer(layer)
                    for gr in [child for child in toc.children() if child.nodeType() == 0]:
                        gr.removeLayer(layer)
                else:
                    group = toc.findGroup(groupname)  # QgsLayerTreeGroup
                    print(type(group))
                    if group is not None:
                        if group.findLayer(layer.id()) is None:
                            group.addLayer(layer)
                        for gr in [child for child in toc.children() if child.nodeType() == 0]:
                            if gr.name() != groupname:
                                if gr.findLayer(layer.id()) is not None:
                                    gr.removeLayer(layer)
                        toc.removeLayer(layer)
        except Exception as e:
            self.info.err(e)