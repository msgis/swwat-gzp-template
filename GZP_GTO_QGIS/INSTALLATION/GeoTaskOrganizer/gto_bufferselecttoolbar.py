#!/usr/bin/python
# -*- coding: utf-8 -*-
from qgis.core import QgsFeatureRequest, QgsWkbTypes, QgsGeometry

from PyQt5.QtWidgets import QWidget, QToolBar, QSlider, QDoubleSpinBox
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5 import uic

import os
import math
import numpy

from .gto_info import Info


class BufferSelectToolbar(object):
    def __init__(self, selectTool):
        super(BufferSelectToolbar, self).__init__()
        # references
        self.selectTool = selectTool
        self.result = None
        self.debug = self.selectTool.debug
        self.id = id
        self.config = self.selectTool.config
        self.info = Info(self)
        try:
            self.gtomain = self.selectTool.gtomain
            self.helper = self.gtomain.helper
            self.metadata = self.gtomain.metadata
            self.iface = self.gtomain.iface
            self.canvas = self.iface.mapCanvas()
            # tool data
            self.toolbar_dock = self.config.get("toolbar_dock", 4)
            self.toolbar_height = self.gtomain.toolbar_height
            # widget
            self.toolbar = None
            # load toolbar
            objName = "gtoTB_" + __name__ + str(id)
            self.toolbar = self.gtomain.helper.findToolbar(self.iface, objName)
            if self.toolbar is None:
                if self.debug: self.info.log("load", objName)
                self.toolbar = QToolBar()
                self.toolbar.setObjectName(objName)
                self.toolbar.setWindowTitle(u'GTO Buffer Selection')
                self.toolbar.setAllowedAreas(Qt.BottomToolBarArea | Qt.TopToolBarArea)
                self.iface.mainWindow().addToolBarBreak(self.toolbar_dock)
                self.iface.addToolBar(self.toolbar, self.toolbar_dock)
                # set the iconsize=> changed when self.iface.addToolBar :S
                if self.toolbar_height is not None:
                    self.toolbar.setMaximumHeight(self.gtomain.toolbar_height)
                    self.toolbar.setMinimumHeight(self.gtomain.toolbar_height)
            else:
                self.toolbar.clear()
            self.wid = Widget(self)
            self.toolbar.addWidget(self.wid)
            self.wid.setIconSizes(self.iface.iconSize(False))
            self.wid.geometry_changed.connect(self.getGeometry)
            self.toolbar.setHidden(False)
        except Exception as e:
            self.info.err(e)

    # from mActionbufferselectxy
    def setHidden(self, a0):
        self.toolbar.setHidden(a0)

    def setGeometry(self, geo, isValid, isCircle=False, isRectangle=False):
        self.toolbar.setHidden(False)
        if self.debug: self.info.log("setGeometry", geo.isEmpty(), isValid, isCircle, isRectangle)
        self.wid.setOriginalGeometry(geo, isValid, isCircle, isRectangle)

    def getGeometry(self, geo):
        self.selectTool.setGeometryToMapTool(geo)


class Widget(QWidget):
    geometry_changed = pyqtSignal(QgsGeometry)

    def __init__(self, toolbar, parent=None):
        super(Widget, self).__init__(parent)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'gto_bufferselect.ui'), self)
        # from gtoAction
        self.toolbar = toolbar
        self.gtomain = self.toolbar.gtomain
        self.info = self.toolbar.info
        self.debug = self.toolbar.debug
        self.config = self.toolbar.config
        try:
            # references
            self.helper = self.gtomain.helper
            self.iface = self.gtomain.iface
            self.canvas = self.iface.mapCanvas()
            # references
            self.geo_original = QgsGeometry()
            self.geo_buffered = QgsGeometry()
            self.isCircle = False  # true=its a polgon geometry, but we need radius
            self.isRectangle = False
            # tool settings
            self.buffer_max = self.config.get('buffer_max', 100)
            self.sldBufferValue.setMaximum(self.buffer_max)
            self.sldBufferValue.setPageStep(self.buffer_max / 10)
            self.sldBufferValue.setSingleStep(self.buffer_max / 100)
            self.dblSpinBox.setMaximum(self.buffer_max)
            # init
            self.setOriginalGeometry(QgsGeometry(), False, False)
            # signals
            self.sldBufferValue.valueChanged.connect(self.buffer)
            self.dblSpinBox.valueChanged.connect(self.buffer)
            self.btnNewSelection.clicked.connect(lambda: self.select(0))
            self.btnAddSelection.clicked.connect(lambda: self.select(1))
            self.btnRemoveSelection.clicked.connect(lambda: self.select(2))
        except Exception as e:
            self.info.err(e)

    def setIconSizes(self, toolbar):
        try:
            self.btnNewSelection.setIconSize(toolbar.iconSize())
            self.btnAddSelection.setIconSize(toolbar.iconSize())
            self.btnRemoveSelection.setIconSize(toolbar.iconSize())
        except Exception as e:
            self.info.err(e)

    def setOriginalGeometry(self, geo, isValid, isCircle=False, isRectangle=False):
        self.isCircle = isCircle
        self.isRectangle = isRectangle
        if isValid and not geo.isEmpty():
            self.geo_original = geo
            self.geo_buffered = geo
        self.btnNewSelection.setEnabled(isValid and not geo.isEmpty())
        self.btnAddSelection.setEnabled(isValid and not geo.isEmpty())
        self.btnRemoveSelection.setEnabled(isValid and not geo.isEmpty())
        self.sldBufferValue.setEnabled(isValid and not geo.isEmpty())
        self.dblSpinBox.setEnabled(isValid and not geo.isEmpty())
        if geo.isEmpty():
            self.lblArea.setText('---')
        else:
            self.showInfo(geo)
        self.sldBufferValue.setValue(0)
        self.dblSpinBox.setValue(0)

    def buffer(self, value):
        try:
            if self.debug: self.info.log("buffer", "value", value)
            sld = self.sldBufferValue
            spin = self.dblSpinBox
            if sld.hasFocus():
                spin.setValue(value)
            else:
                sld.setValue(value)
            if self.debug: self.info.log(value)
            if value == 0:
                self.geo_buffered = self.geo_original
            else:
                self.geo_buffered = self.geo_original.buffer(value, 100)  # roundfactor of buffer corner =3 (Segments)
                if self.isRectangle:
                    self.geo_buffered = QgsGeometry.fromRect(self.geo_buffered.boundingBox())
            self.showInfo(self.geo_buffered)
            self.geometry_changed.emit(self.geo_buffered)
        except Exception as e:
            self.info.err(e)

    def select(self, mode):
        try:
            lay = self.iface.activeLayer()
            geo = self.geo_buffered
            req = QgsFeatureRequest()
            req.setFilterRect(geo.boundingBox())
            req.setNoAttributes()
            if mode == 0:
                selFeat = []
            else:
                selFeat = lay.selectedFeatureIds()
            for feat in lay.getFeatures(req):
                if geo.intersects(feat.geometry()):
                    if mode < 2:
                        selFeat.append(feat.id())
                    else:
                        try:
                            selFeat.remove(feat.id())
                        except:
                            pass
            lay.selectByIds(selFeat)
            self.gtomain.runcmd(self.config.get('tools', []))
        except Exception as e:
            self.info.err(e)

    def showInfo(self, geo):
        try:
            infoTxt = '---'
            lblInfo = self.lblArea
            if geo is not None:
                if geo.type() == QgsWkbTypes.PolygonGeometry:
                    if self.isCircle:
                        rec = geo.boundingBox()
                        radius = rec.width()/2
                        if radius > 1000:
                            infoTxt = 'Radius: ' + str(round(radius / 1000, 4)) + ' km'
                        else:
                            infoTxt = 'Radius: ' + str(round(radius, 2)) + ' m'
                        if self.debug: self.info.log("Fläche Kreis:", geo.area())
                    else:
                        if geo.area() > 1000000:
                            infoTxt = 'Fläche: ' + str(round(geo.area() / 1000000, 4)) + ' km²'
                        else:
                            infoTxt = 'Fläche: ' + str(round(geo.area(), 2)) + ' m²'
                elif geo.type() == QgsWkbTypes.LineGeometry:
                    if geo.length() > 1000:
                        infoTxt = 'Länge: ' + str(round(geo.length() / 1000, 4)) + ' km'
                    else:
                        infoTxt = 'Länge: ' + str(round(geo.length(), 1)) + ' m'
            lblInfo.setText(infoTxt)
        except Exception as e:
            self.info.err(e)
