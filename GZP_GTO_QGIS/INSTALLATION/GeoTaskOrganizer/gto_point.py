#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

# QDoubleValidator needs QValidator in qgis 3.4!
from PyQt5.QtCore import Qt, QLocale, pyqtSignal
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtWidgets import QWidget, QLabel, QLineEdit, QHBoxLayout, QToolButton, QToolBar, QComboBox, QDoubleSpinBox
from PyQt5 import uic

from qgis.core import QgsProject, QgsCoordinateReferenceSystem, QgsPointXY, QgsCoordinateTransform, QgsVectorLayerUtils, \
    QgsWkbTypes, QgsGeometry
from qgis.gui import QgsProjectionSelectionWidget, QgsVertexMarker

import os

from .gto_point_tool import GTOPointTool


class GTOPointWidget(QWidget):
    isActive = pyqtSignal(bool)

    def __init__(self, gtoObj, parent=None):
        super(GTOPointWidget, self).__init__(parent)

        self.gtomain = gtoObj.gtomain
        self.info = self.gtomain.info
        self.debug = self.gtomain.debug

        try:
            # references
            self.helper = self.gtomain.helper
            self.iface = self.gtomain.iface
            self.prj = QgsProject.instance()
            self.canvas = self.iface.mapCanvas()
            # references
            self.x = 0
            self.y = 0
            self.xt = 0
            self.yt = 0
            self.snaped = False
            self.crs_transform = None
            self.crs_layer = None
            self.parent_widget = None  # e.g toolbar
            self.userEditX = False
            self.userEditY = False
            # config
            self.tools = []
            self.coordinatereferences = None
            self.scale = 0
            self.center = True
            self.enable_save = False
            self.precision = -1
            self.cboCoordSystems = None
            self.is_widgetaction = False
            self.show_tool_button = False
            self.addpoint_attributes = {}
            self.tools_after_addpoint = []
            # widgets:
            uic.loadUi(os.path.join(os.path.dirname(__file__), 'gto_point.ui'), self)
            # point tool
            self.btnPointTool = self.btnPoint
            # x
            self.coordX = self.coordX
            # self.validX = QDoubleValidator(sys.float_info.min, sys.float_info.max, 16, self.coordX)  # no negative numbers possible?
            # self.validX = QDoubleValidator(-999999999, 999999999, 16, self.coordX)  # working but no range limit
            self.validX = QDoubleValidator(self.coordX)  # so we use the standard:
            self.validX.setNotation(QDoubleValidator.StandardNotation)  # By default, this property is set to ScientificNotation: i.e. 1.5E-2  is possible
            self.coordX.setValidator(self.validX)

            self.btnCopyXt = self.btnCopyXt
            self.lblX = self.lblX
            # y
            self.coordY = self.coordY
            self.validY = QDoubleValidator(self.coordY)
            self.validY.setNotation(QDoubleValidator.StandardNotation)
            self.coordY.setValidator(self.validY)

            self.btnCopyYt = self.btnCopyYt
            self.lblY = self.lblY
            # show
            self.btnShow = self.btnShow
            self.btnShow.setIcon(self.helper.getIcon('mActionZoomPoint.png'))
            # add point
            self.btnAddPoint = self.btnAddPoint
            self.btnAddPoint.setIcon(self.helper.getIcon('mActionAddPoint.png'))
            self.btnAddPoint.setToolTip("Punkt erstellen")

            # marker
            self.marker = QgsVertexMarker(self.canvas)
            self.marker.setColor(Qt.yellow)
            self.marker.setIconType(QgsVertexMarker.ICON_CROSS)
            self.marker.setIconSize(10)
            self.marker.setPenWidth(3)
            # See the enum IconType from http://www.qgis.org/api/classQgsVertexMarker.html

            # maptool
            self.mapTool = GTOPointTool(self.iface, self.canvas)
            self.mapTool.isActive.connect(self.setToolStatus)
            self.mapTool.canvasReleased.connect(self.setCoords)
            # signals
            # QToolButton.toggled()
            self.btnPoint.clicked.connect(self.setMapTool)

            # self.coordX.textChanged.connect(self.set_user_editX)
            # self.coordY.textChanged.connect(self.set_user_editY)
            self.coordX.textEdited.connect(self.set_user_editX)
            self.coordY.textEdited.connect(self.set_user_editY)
            # self.coordX.editingFinished.connect(self.check_coords)
            # self.coordY.editingFinished.connect(self.check_coords)

            self.btnShow.clicked.connect(self.showCoordinate)
            self.btnCopyXt.clicked.connect(self.copyXt)
            self.btnCopyYt.clicked.connect(self.copyYt)
            self.btnAddPoint.clicked.connect(self.add_point)
            self.prj.crsChanged.connect(self.prj_crs_changed)
            self.iface.mapCanvas().currentLayerChanged.connect(self.layer_changed)
        except Exception as e:
            self.info.err(e)

    def set_user_editX(self, *args):
        try:
            if self.debug: self.info.log("set_user_editX")
            self.userEditX = True
            self.marker.hide()
            self.marker.setColor(Qt.blue)
            self.snaped = False
        except Exception as e:
            self.info.err(e)

    def set_user_editY(self, *args):
        try:
            if self.debug: self.info.log("set_user_editY")
            self.userEditY = True
            self.marker.hide()
            self.marker.setColor(Qt.blue)
            self.snaped = False
        except Exception as e:
            self.info.err(e)

    def reset_user_edit(self):
        if self.debug: self.info.log("reset_user_edit")
        self.userEditX = False
        self.userEditY = False

    def check_coords(self):
        try:
            self.marker.hide()
            if self.debug: self.info.log("useredit: X:", self.userEditX, "userEditY:", self.userEditY)
            if self.coordX.text() == '':
                self.coordX.setText('0')
                self.x = 0
            if self.coordY.text() == '':
                self.coordY.setText('0')
                self.y = 0
            if self.userEditX or self.userEditY:
                self.snaped = False
                self.userEditX = False
                self.userEditY = False
                self.xt = float(self.coordX.text().replace(",", "."))
                self.yt = float(self.coordY.text().replace(",", "."))
            tr = QgsCoordinateTransform(self.crs_transform, self.prj.crs(), self.prj)
            trPoint = tr.transform(QgsPointXY(self.xt, self.yt))
            self.x = trPoint.x()
            self.y = trPoint.y()
            if self.debug: self.info.log("check_coords:", self.x, "/", self.y, "/snaped:", self.snaped)
        except Exception as e:
            self.info.err(e)

    def setMapTool(self):
        try:
            self.canvas.setMapTool(self.mapTool)
        except Exception as e:
            self.info.err(e)

    def set_parent_widget(self, widget):
        try:
            self.parent_widget = widget
            if self.parent_widget.action.isChecked():
                self.setMapTool()
        except Exception as e:
            self.info.err(e)

    def setToolStatus(self, isActive):
        try:
            self.btnPoint.setChecked(isActive)
            self.marker.hide()
            self.isActive.emit(isActive)
            if self.parent_widget is not None:
                self.parent_widget.set_status(isActive)
        except Exception as e:
            self.info.err(e)

    def setConfig(self, config):
        try:
            self.tools = config.get("tools", [])
            self.coordinatereferences = config.get("coordinatereferences", None)
            self.scale = config.get("scale", 0)
            self.center = config.get("center", True)
            self.enable_save = config.get('enable_save', False)
            self.precision = config.get('precision', -1)
            self.is_widgetaction = config.get('is_widgetaction', False)
            self.show_tool_button = config.get('show_tool_button', not self.is_widgetaction)
            self.addpoint_attributes = config.get("addpoint_attributes", {})
            self.tools_after_addpoint = config.get("tools_after_addpoint", [])
            if self.precision < 0:
                self.precision, type_conversion_ok = self.prj.readNumEntry("PositionPrecision", "DecimalPlaces", 3)
            # labels:
            self.lblX.setText(config.get('label_x', 'X:'))
            self.lblY.setText(config.get('label_y', 'Y:'))
            # text
            text = ''
            if self.scale > 0 and self.center:
                text = "Auf Koordinate zentrieren, Maßstab: " + str(self.scale)
            elif self.center:
                text = "Auf Koordinate zentrieren"
            elif self.scale > 0:
                text = "Maßstab: " + str(self.scale)
            elif len(self.tools) > 0:
                text = self.tools[0]
                act = self.gtomain.findAction(self.tools[0])
                if act is not None:
                    text = act.toolTip()
                    if act.icon() is not None:
                        self.btnShow.setIcon(act.icon())
            if self.debug: self.info.log(text)
            self.btnShow.setToolTip(text)
            if self.btnShow.toolTip() == '':
                self.btnShow.setHidden(True)
            # add point
            self.btnAddPoint.setHidden(not self.enable_save)
            # point tool
            self.btnPointTool.setHidden(not self.show_tool_button)
        except Exception as e:
            self.info.err(e)

    def added(self):  # widget was added to parent
        try:
            self.crs_transform = self.prj.crs()
            self.crs_layer = self.iface.activeLayer().crs()
            # set crs widget
            if self.coordinatereferences is None:
                # qgis transform
                self.cboCoordSys.setHidden(True)
                self.cboCoordSystems = self.mQgsProjectionSelectionWidget
                self.cboCoordSystems.setMinimumWidth(460)
                self.cboCoordSystems.setOptionVisible(QgsProjectionSelectionWidget.ProjectCrs, True)
                self.cboCoordSystems.setCrs(self.prj.crs())
                self.setCrs(self.cboCoordSystems.crs())
                self.cboCoordSystems.crsChanged.connect(self.setCrs)
            else:
                # custom transform
                self.mQgsProjectionSelectionWidget.setHidden(True)
                self.cboCoordSystems = self.cboCoordSys
                self.cboCoordSystems.setMinimumWidth(400)

                self.cboCoordSystems.currentIndexChanged.connect(
                    lambda: self.setCrs(self.cboCoordSystems.currentData()))
                self.cboCoordSystems.addItem(
                    "Projekt CRS: " + self.crs_transform.authid() + " - " + self.crs_transform.description(),
                    self.crs_transform)
                for crsID in self.coordinatereferences:
                    try:
                        crs = QgsCoordinateReferenceSystem(crsID)
                        self.cboCoordSystems.addItem(crs.authid() + " - " + crs.description(), crs)
                    except Exception as e:
                        self.info.err(e)
                self.cboCoordSystems.setCurrentIndex(0)
            # here we know which type is cboCoordSystems!
            self.setIconSizes()
        except Exception as e:
            self.info.err(e)

    def setIconSizes(self):
        try:
            if self.parentWidget() is not None:
                btns = self.findChildren(QToolButton)
                for btn in btns:
                    try:
                        btn.setIconSize(self.iface.iconSize(False))
                    except:
                        pass
                # help for the QGIS widget :S
                self.cboCoordSystems.setMaximumHeight(self.cboCoordSys.height())
                btns = self.cboCoordSystems.findChildren(QToolButton)
                for btn in btns:
                    btn.setIconSize(self.iface.iconSize(False))
        except Exception as e:
            self.info.err(e)

    def layer_changed(self, layer):
        try:
            if layer.geometryType() == QgsWkbTypes.GeometryType.PointGeometry:
                self.btnAddPoint.setEnabled(True)
            else:
                self.btnAddPoint.setEnabled(False)
        except Exception as e:
            self.info.err(e)

    def prj_crs_changed(self):
        try:
            self.reset_user_edit()
            if self.coordinatereferences is not None:  # my combo
                self.crs_transform = self.prj.crs()
                self.cboCoordSystems.setItemText(0,
                                                 "Projekt CRS: " + self.crs_transform.authid() + " - " + self.crs_transform.description())
                self.cboCoordSystems.setItemData(0, self.crs_transform)
                self.x = 0
                self.y = 0
                self.xt = 0
                self.yt = 0
                self.coordX.setText("---")
                self.coordY.setText("---")
        except Exception as e:
            self.info.err(e)

    def add_point(self):
        try:
            self.check_coords()
            layer = self.iface.activeLayer()
            if layer.geometryType() == QgsWkbTypes.GeometryType.PointGeometry:
                self.prj.layerTreeRoot().findLayer(layer.id()).setItemVisibilityCheckedParentRecursive(True)
                if self.x != 0 and self.y != 0:
                    feat = QgsVectorLayerUtils.createFeature(layer)
                    tr = QgsCoordinateTransform(self.prj.crs(), self.crs_layer, self.prj)
                    trPoint = tr.transform(QgsPointXY(self.x, self.y))
                    feat.setGeometry(QgsGeometry.fromPointXY(trPoint))
                    # direct save
                    # (res, features) = layer.dataProvider().addFeatures([feat])
                    # if self.debug: self.info.log("new point:", res, features[0])
                    # set attributes

                    dic_info = {"x": self.x, "y": self.y, "snaped": self.snaped}
                    # self.info.err(None,"mapping:",dic_info)
                    # self.info.err(None, "addpoint_attributes:", self.addpoint_attributes)
                    for k, v in self.addpoint_attributes.items():
                        # self.info.err(None,"attribute:",k,"value:",dic_info[v])
                        feat[k] = layer.fields().field(k).convertCompatible(dic_info[v])
                    features = [feat]
                    layer.featureAdded.connect(self.select_new_feature)
                    self.save_features(layer, features)
                    layer.featureAdded.disconnect(self.select_new_feature)

                    self.marker.hide()
                    self.helper.refreshLayer(layer)
                    self.gtomain.runcmd(self.tools_after_addpoint)
                else:
                    self.info.gtoWarning('Ungültige Koordinaten! x:', self.x, "y:", self.y)
            else:
                self.info.gtoWarning('Kein Punktlayer ausgewählt!')
        except Exception as e:
            self.info.err(e)

    def select_new_feature(self, featId):
        try:
            if self.debug: self.info.log("new featue:", self.iface.activeLayer().name(), "/ fid:", featId)
            self.iface.activeLayer().selectByIds([featId])
            self.mapTool.reset_marker()
            self.marker.hide()
            self.helper.refreshLayer(self.iface.activeLayer())
        except Exception as e:
            self.info.err(e)

    def save_features(self, layer, features):
        if not layer.isEditable():
            layer.startEditing()
        layer.beginEditCommand("layer {0} edit".format(layer.name()))
        try:
            layer.addFeatures(features)
            layer.endEditCommand()
        except Exception as e:
            layer.destroyEditCommand()
            raise e

    def copyXt(self):
        self.check_coords()
        dsp = QDoubleSpinBox()
        dsp.setDecimals(16)
        self.helper.copyToClipboard(dsp.textFromValue(self.xt))

    def copyYt(self):
        self.check_coords()
        dsp = QDoubleSpinBox()
        dsp.setDecimals(16)
        self.helper.copyToClipboard(dsp.textFromValue(self.yt))

    def reset(self):
        if self.debug: self.info.log("widget reset")
        self.marker.hide()

    def setCoords(self, point, snaped):
        try:
            self.reset_user_edit()
            self.snaped = snaped
            self.x = point.x()
            self.y = point.y()
            if self.debug: self.info.log("setCoords", self.x, "/", self.y)
            self.setCrs(self.crs_transform)
            # marker
            self.marker.setCenter(QgsPointXY(self.x, self.y))
            if snaped:
                self.marker.setColor(Qt.red)
            else:
                self.marker.setColor(Qt.blue)
            self.marker.show()
        except Exception as e:
            self.info.err(e)

    def showCoordinate(self):
        try:
            self.check_coords()
            self.marker.hide()
            if self.x != 0 and self.y != 0:
                pt_center = QgsPointXY(self.x, self.y)
                self.marker.setCenter(pt_center)
                self.marker.show()

                # center map
                if self.center:
                    self.canvas.setCenter(pt_center)
                # scale map
                if self.scale is not None and self.scale > 0:
                    self.canvas.zoomScale(self.scale)
                self.canvas.refresh()
                # run tools
                self.gtomain.runcmd(self.tools)
            else:
                self.info.gtoWarning('Ungültige Koordinate! x:', self.x, "y:", self.y)
        except Exception as e:
            self.info.err(e)

    def setCrs(self, crs):
        try:
            if self.debug: self.info.log("setCrs")
            self.crs_transform = crs
            tr = QgsCoordinateTransform(self.prj.crs(), self.crs_transform, self.prj)
            trPoint = tr.transform(QgsPointXY(self.x, self.y))

            self.xt = trPoint.x()
            self.yt = trPoint.y()

            d = round(trPoint.x(), self.precision)
            display = str(d).replace(".", QLocale().decimalPoint())
            self.coordX.setText(display)

            d = round(trPoint.y(), self.precision)
            display = str(d).replace(".", QLocale().decimalPoint())
            self.coordY.setText(display)
        except Exception as e:
            self.info.err(e)
