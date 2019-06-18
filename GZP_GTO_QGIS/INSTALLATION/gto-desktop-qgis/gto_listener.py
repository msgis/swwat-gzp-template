#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5.QtGui import *
from PyQt5.QtCore import *

class gtoListener(QObject):
    def __init__(self,gtomain, parent = None ):
        self.gtomain = gtomain
        self.iface = gtomain.iface
        self.debug = gtomain.debug
        self.info = gtomain.info

        self.iface.layerTreeView().currentLayerChanged.connect(self.layer_signals)
        self.layer = None
        self.newFeatures = []
        self.lastFeature = None
        if self.debug: self.info.log ("Listener started")

    def layer_signals(self,lyr):
        self.layers_disconnect()
        try:
            self.layer=lyr
            self.layer.layerModified.connect(self.logLayerModified)
            self.layer.featureAdded.connect(self.logFeatureAdded)
            self.layer.editingStarted.connect(self.logEditingStarted)
            self.layer.committedFeaturesAdded.connect(self.logCommittedFeaturesAdded)
            self.layer.attributeValueChanged.connect(self.logattributeValueChanged)
            if self.debug: self.info.log("Listener connected")
        except Exception as e:
            self.info.err(e)

    def layers_disconnect(self):
        try:
            if self.layer is not None:
                self.layer.layerModified.disconnect( self.logLayerModified)
                self.layer.featureAdded.disconnect( self.logFeatureAdded)
                self.layer.editingStarted.disconnect( self.logEditingStarted)
                self.layer.committedFeaturesAdded.disconnect( self.logCommittedFeaturesAdded)
                self.layer.attributeValueChanged.disconnect(self.logattributeValueChanged)
                if self.debug: self.info.log("Listener disconneted")
        except Exception as e:
            self.info.err(e)
        self.layer = None

    def logLayerModified(self, onlyGeometry = None ):
        self.info.log("layer modified")

    def logFeatureAdded(self,fid):
        if self.debug: self.info.log("feature added")
        self.layer.setSelectedFeatures([fid])

    def logattributeValueChanged(self,featID,idx, x):
        if self.debug: self.info.log(featID,idx,x)

    def logEditingStarted(self):
        if self.debug: self.info.log("Editing Started")

    def logCommittedFeaturesAdded(self, layerId, addedFeatures ):
        try:
            self.newFeatures = []
            if self.debug: self.info.log("layer:",layerId,"has new features added:")
            for feature in addedFeatures:
                if self.debug: self.info.log("ID:",feature.id())
                self.newFeatures.append(feature)
        except Exception as e:
            self.info.err(e)
