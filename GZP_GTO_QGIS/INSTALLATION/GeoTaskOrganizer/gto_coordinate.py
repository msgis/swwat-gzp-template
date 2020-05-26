#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QDockWidget, QWidget, QComboBox, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel, \
    QHeaderView, QHBoxLayout, QToolButton, QAbstractItemView
from PyQt5.QtCore import Qt, QPersistentModelIndex, pyqtSignal, QSize, QEvent, QTimer
from PyQt5.QtGui import QColor
from PyQt5 import uic

from qgis.core import QgsProject, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsExpression, \
    QgsExpressionContext, QgsWkbTypes, QgsPointXY, QgsGeometry, QgsPoint
from qgis.gui import QgsRubberBand, QgsProjectionSelectionWidget

import os


class GTOCoordinatesDockWidget(QDockWidget):
    def __init__(self, gtoMain, parent=None):
        super(GTOCoordinatesDockWidget, self).__init__(parent)

        self.gtomain = gtoMain
        self.debug = self.gtomain.debug
        self.info = self.gtomain.info
        self.iface = self.gtomain.iface

        self.setObjectName(self.__class__.__name__)
        self.setWindowTitle("Koordinaten Vertizes")
        self.wid = GTOCoordinatesWidget(gtoMain, self)
        self.setWidget(self.wid)
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self)
        self.setHidden(True)

    def init(self, config):  # from customized action/tool
        self.wid.init(config)


class GTOCoordinatesWidget(QWidget):
    def __init__(self, gtoMain, parent=None):
        super(GTOCoordinatesWidget, self).__init__(parent)
        try:
            self.setObjectName(self.__class__.__name__)
            self.gtomain = gtoMain
            self.helper = self.gtomain.helper
            self.setObjectName(self.__class__.__name__)  # for info
            self.info = self.gtomain.getInfoObject(self)
            self.debug = self.gtomain.debug
            self.metadata = self.gtomain.metadata
            self.iface = self.gtomain.iface
            self.iface = self.gtomain.iface
            self.prj = QgsProject.instance()
            self.canvas = self.iface.mapCanvas()
            if self.debug: self.info.log("__init__")
            # settings
            self.coords = []
            self.pointScale = 1000
            self.buffer_scale = 0.1
            self.minimum_scale = 5000
            # references
            self.result = None
            self.icon = self.helper.getIcon("mActionToggleEditing.png")
            self.markedFeature = None
            self.markedVertex = None
            self.markedNewVertex = None
            self.colorNewVertex = Qt.darkGreen
            self.rubber = None

            self.blockItemChange = True
            self.blockGeometryChanged = False
            self.layer = self.iface.activeLayer()
            # create form
            uic.loadUi(os.path.join(os.path.dirname(__file__), 'gto_coordinates.ui'), self)
            self.lblLayer = self.lblLayer
            self.cboFeat = self.cboFeat
            self.btnZoomTo = self.btnZoomTo
            self.projectWid = self.mQgsProjectionSelectionWidget
            self.projectWid.setHidden(True)
            self.cboCoordSystems = self.cboCoordSystems
            self.cboLayer = self.mMapLayerComboBox
            self.cboLayer.setHidden(True)

            # transform
            self.projectWid.setCrs(self.prj.crs())

            self.tblCoords.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.tblCoords.setSelectionMode(QAbstractItemView.SingleSelection)

            self.layout = QVBoxLayout(self)

            # signals
            self.canvas.currentLayerChanged.connect(self.fillCombo)
            self.canvas.selectionChanged.connect(self.fillCombo)
            self.cboFeat.currentIndexChanged.connect(self.fillTable)

            self.cboCoordSystems.currentIndexChanged.connect(lambda: self.setCrs(self.cboCoordSystems.currentData()))
            self.projectWid.crsChanged.connect(self.setCrs)

            self.tblCoords.itemChanged.connect(self.item_changed)
            self.tblCoords.currentCellChanged.connect(self.currentCellChanged)
            self.btnZoomTo.clicked.connect(self.zoomTo)

            # init
            self.crsLay = None
            self.crs = None

            # default
            self.init({})
        except Exception as e:
            self.info.err(e)

    def init(self, config):  # called from tool
        try:
            self.debug = config.get('debug', False)
            if self.debug: self.info.log("init")
            #status
            self.layer = self.iface.activeLayer()
            self.prj = QgsProject.instance()
            self.cboCoordSystems.clear()
            # tooldata
            self.coords = config.get('coordinatereferences', self.coords)
            self.pointScale = config.get('point_scale', self.pointScale)
            self.buffer_scale = config.get("buffer_scale", self.buffer_scale)
            self.minimum_scale = config.get("minimum_scale", self.minimum_scale)

            if not self.coords:
                self.cboCoordSystems.setHidden(True)
                self.projectWid.setHidden(False)
                self.projectWid.setCrs(self.prj.crs())
                cbos= self.projectWid.findChildren(QComboBox)
                for cbo in cbos:
                    cbo.setMaximumHeight(self.iface.iconSize().height())
            else:
                self.projectWid.setHidden(True)
                self.cboCoordSystems.setHidden(False)
                crs = self.prj.crs()
                self.cboCoordSystems.addItem("Project CRS: " + crs.authid() + " - " + crs.description(), crs)
                for crsID in self.coords:
                    try:
                        crs = QgsCoordinateReferenceSystem(crsID)
                        self.cboCoordSystems.addItem(crs.authid() + " - " + crs.description(), crs)
                    except Exception as e:
                        self.info.err(e)
            #ui stuff
            btns = self.findChildren(QToolButton)
            for btn in btns:
                btn.setIconSize(self.iface.iconSize())
            #start
            self.fillCombo(self.layer)
            self.fillTable(True)
        except Exception as e:
            self.info.err(e)

    def reset(self, *args):
        try:
            if self.debug: self.info.log("reset")

            self.btnZoomTo.setEnabled(False)

            self.canvas.scene().removeItem(self.markedFeature)
            self.markedFeature = None

            self.canvas.scene().removeItem(self.markedVertex)
            self.markedVertex = None

            self.canvas.scene().removeItem(self.markedNewVertex)
            self.markedNewVertex = None

            if self.rubber:
                self.canvas.scene().removeItem(self.rubber)
                self.rubber = None

            self.canvas.refresh()
        except Exception as e:
            self.info.err(e)

    def setCrs(self, crs):
        self.crs = crs
        self.fillTable()

    def zoomTo(self):
        try:
            if self.debug: self.info.log("zoomTo")
            if self.cboFeat.currentData():
                feat = self.layer.getFeature(self.cboFeat.currentData())
                geo = feat.geometry()
                if self.debug: self.info.log("zoomto", geo == QgsWkbTypes.GeometryType.PointGeometry, )
                if geo.type() == QgsWkbTypes.GeometryType.PointGeometry:
                    self.canvas.setCenter(geo.asPoint())
                    self.canvas.zoomScale(self.pointScale)
                else:
                    buffer = 0
                    if geo.boundingBox().width() > geo.boundingBox().height():
                        buffer = geo.boundingBox().width()
                    else:
                        buffer = geo.boundingBox().height()
                    geo = geo.buffer(buffer * self.buffer_scale, 0)
                    self.canvas.setExtent(geo.boundingBox())
                    if self.canvas.scale() < self.minimum_scale: self.canvas.zoomScale(self.minimum_scale)
                    self.canvas.refresh()
        except Exception as e:
            self.info.err(e)

    def item_changed(self, item):  # value changed
        try:
            if self.blockItemChange: return
            if self.debug: self.info.log("item_changed", item.data(0), item.row(), item.column())
            currentRow = item.row()
            btn = self.tblCoords.cellWidget(currentRow, 2)
            if btn is not None: btn.setEnabled(True)

            x, y = self.xyMap()

            self.canvas.scene().removeItem(self.markedNewVertex)
            if self.isVisible():
                self.markedNewVertex = self.helper.markVertex(x, y, self.colorNewVertex)
                self.setRubber()
        except Exception as e:
            self.info.err(e)

    def currentCellChanged(self, currentRow, currentColumn, previousRow, previousColumn):  # row changed
        try:
            if self.cboFeat.currentData() is None: return
            if self.blockItemChange: return
            if self.debug: self.info.log("currentCellChanged")

            self.canvas.scene().removeItem(self.markedVertex)
            self.canvas.scene().removeItem(self.markedNewVertex)

            btn = self.tblCoords.cellWidget(currentRow, 2)
            if btn is None: return

            x, y = self.getRealXY(currentRow)
            if self.isVisible():
                self.markedVertex = self.helper.markVertex(x, y)

            if btn.isEnabled():
                x, y = self.xyMap()
                self.markedNewVertex = self.helper.markVertex(x, y, self.colorNewVertex)
            self.setRubber()
        except Exception as e:
            self.info.err(e)

    def fillCombo(self, maplayer):
        try:
            if self.debug: self.info.log("fillCombo")
            self.reset()  # map,zoom
            self.tblCoords.clear()
            self.cboFeat.clear()
            self.layer = self.iface.activeLayer()
            if self.layer is not None:
                self.layer.geometryChanged.connect(self.layer_geometryChanged)
                self.layer.featureDeleted.connect(self.cboFeat.clear)  # (QgsFeatureId fid)
            if maplayer is not None:
                self.crsLay = maplayer.crs()
                self.lblLayer.setText(maplayer.name())
                for f in maplayer.selectedFeatures():
                    self.cboFeat.addItem(self.getFeatureDisplayName(maplayer, f), f.id())
                self.cboFeat.model().sort(0)
                if self.cboFeat.count() > 0:
                    self.cboFeat.setCurrentIndex(0)
        except Exception as e:
            self.info.err(e)

    def fillTable(self, init=False):
        try:
            if self.crs is None or self.crsLay is None: return
            if self.isHidden() and not init: return
            if self.debug: self.info.log("fillTable", "debug", self.debug)
            self.blockItemChange = True
            self.tblCoords.clear()
            self.tblCoords.setColumnCount(5)
            self.tblCoords.setHorizontalHeaderItem(0, QTableWidgetItem("X"))
            self.tblCoords.setHorizontalHeaderItem(1, QTableWidgetItem("Y"))
            self.tblCoords.setHorizontalHeaderItem(2, QTableWidgetItem(""))
            self.tblCoords.setHorizontalHeaderItem(3, QTableWidgetItem("Xr"))
            self.tblCoords.setHorizontalHeaderItem(4, QTableWidgetItem("Yr"))
            self.tblCoords.horizontalHeader().setSectionHidden(3, self.debug)
            # self.tblCoords.setColumnHidden(3, self.debug)
            self.tblCoords.setColumnHidden(4, self.debug)

            self.tblCoords.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.tblCoords.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)  # QHeaderView.Fixed

            destCrs = self.crs
            self.canvas.refresh()

            if self.cboFeat.currentData():
                feat = self.layer.getFeature(self.cboFeat.currentData())
                geometry = feat.geometry()
                tr = QgsCoordinateTransform(self.crsLay, destCrs, self.prj)
                row = 0
                column = 2  # btn column
                for v in geometry.vertices():
                    self.tblCoords.setRowCount(row + 1)
                    if self.debug: self.info.log("vertex:", v.x(), v.y())
                    v.transform(tr)

                    itemX = QTableWidgetItem(str(v.x()))
                    self.tblCoords.setItem(row, 0, itemX)
                    itemY = QTableWidgetItem(str(v.y()))
                    self.tblCoords.setItem(row, 1, itemY)

                    itemXr = QTableWidgetItem(str(v.x()))
                    self.tblCoords.setItem(row, 3, itemXr)
                    itemYr = QTableWidgetItem(str(v.y()))
                    self.tblCoords.setItem(row, 4, itemYr)

                    index = QPersistentModelIndex(self.tblCoords.model().index(row, column))
                    btn = MyButton(self.gtomain)
                    btn.setIcon(self.icon)
                    btn.click.connect(lambda *args, index=index: self.cellClick(index.row(), index.column()))
                    btn.setEnabled(False)
                    btn.setPixmap(self.icon.pixmap(24, 24))

                    self.tblCoords.setCellWidget(row, 2, btn)
                    row = row + 1
                    if self.debug: self.info.log("vertex transformed:", v.x(), v.y())
                self.reset()

                if geometry.type() == QgsWkbTypes.GeometryType.PolygonGeometry:  # remove double vertex????
                    self.tblCoords.removeRow(self.tblCoords.rowCount() - 1)
                if self.isVisible():
                    self.setRubber()
                    self.markedFeature = self.helper.markFeature(self.layer, feat)
                    self.btnZoomTo.setEnabled(True)
                    self.blockItemChange = False
                    self.tblCoords.setCurrentCell(0, 0)
            else:
                self.reset()
            self.blockItemChange = False
        except Exception as e:
            self.info.err(e)

    def cellClick(self, currentRow, currentColumn):  # save
        try:
            if currentRow is None or self.cboFeat.currentData() is None:  # from restore?
                return
            if self.debug: self.info.log("cellClick", currentRow, currentColumn)
            self.blockGeometryChanged = True
            if not self.layer.isEditable(): self.layer.startEditing()
            self.layer.beginEditCommand("Feature change vertex")

            self.tblCoords.setCurrentCell(currentRow, 0)
            x, y = self.xyMap()

            feat = self.layer.getFeature(self.cboFeat.currentData())
            geo = feat.geometry()
            geo.moveVertex(x, y, currentRow)
            self.layer.changeGeometry(feat.id(), geo)
            # feat.setGeometry(geo)
            self.layer.endEditCommand()
            # update real vertex in table
            itemXr = QTableWidgetItem(str(x))
            self.tblCoords.setItem(currentRow, 3, itemXr)
            itemYr = QTableWidgetItem(str(y))
            self.tblCoords.setItem(currentRow, 4, itemYr)
            # edit button
            btn = self.sender()
            btn.setEnabled(False)
            # update canvas
            self.updateMap(currentRow, x, y, geo)
            self.blockGeometryChanged = False
        except Exception as e:
            self.layer.destroyEditCommand()
            self.info.err(e)

    def layer_geometryChanged(self, fid, geometry=None):  # if geometry ouside changed
        try:
            if self.debug: self.info.log("layer_geometryChanged")
            if not self.blockGeometryChanged:
                if self.cboFeat.currentData() and self.cboFeat.currentData() == fid:
                    self.fillTable()
        except Exception as e:
            self.info.err(e)

    def getRealXY(self, currentRow):
        try:
            if self.debug: self.info.log("getRealXY")
            if currentRow is None:
                currentRow = self.tblCoords.currentRow()
            itemX = self.tblCoords.item(currentRow, 3)
            x = float(itemX.data(Qt.EditRole))
            itemY = self.tblCoords.item(currentRow, 4)
            y = float(itemY.data(Qt.EditRole))
            if self.debug: self.info.log("getRealXY", x, "/", y, "role", Qt.EditRole)
            return x, y
        except Exception as e:
            self.info.err(e)

    def xyMap(self, currentRow=None):
        try:
            if self.debug: self.info.log("xyMap")
            if self.cboFeat.currentData() is not None:
                if currentRow is None:
                    currentRow = self.tblCoords.currentRow()
                itemX = self.tblCoords.item(currentRow, 0)
                x = float(itemX.data(0))
                itemY = self.tblCoords.item(currentRow, 1)
                y = float(itemY.data(0))
                destCrs = self.crsLay
                crs = self.cboCoordSystems.currentData()
                tr = QgsCoordinateTransform(self.crs, destCrs, self.prj)
                mapPoint = tr.transform(QgsPointXY(x, y))
                if self.debug:
                    self.info.log("point:", x, "/", y)
                    self.info.log("tr:", mapPoint.x(), "/", mapPoint.y())
                return mapPoint.x(), mapPoint.y()
            else:
                return 0, 0
        except Exception as e:
            self.info.err(e)

    def updateMap(self, currentRow, x, y, geo):
        try:
            if self.debug: self.info.log("updateMap", currentRow, x, y)

            self.canvas.scene().removeItem(self.markedVertex)
            self.markedVertex = self.helper.markVertex(x, y)

            self.canvas.scene().removeItem(self.markedFeature)
            self.markedFeature = self.helper.markFeature(self.layer, geo)

            self.setRubber()
            self.canvas.refresh()
        except Exception as e:
            self.info.err(e)

    def getFeatureDisplayName(self, layer, feature):
        try:
            name = "ID:" + str(feature.id())
            if layer.labelsEnabled():
                labeling = layer.labeling()
                palyr = labeling.settings()
                expression = QgsExpression(palyr.fieldName)
                context = QgsExpressionContext()
                context.setFeature(feature)
                expression.prepare(context)
                value = expression.evaluate(context)
                name = name + " (" + expression.formatPreviewString(value, True) + ")"
            return name
        except Exception as e:
            self.info.err(e)

    def setRubber(self):
        try:
            if self.debug: self.info.log("setRubber")
            if self.rubber:
                self.canvas.scene().removeItem(self.rubber)
                self.rubber = None
            if self.layer.geometryType() == QgsWkbTypes.GeometryType.PointGeometry: return
            self.rubber = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
            self.rubber.setLineStyle(Qt.PenStyle(Qt.DashDotLine))
            self.rubber.setWidth(2)
            self.rubber.setColor(self.colorNewVertex)
            color = QColor()
            color.setAlpha(10)
            self.rubber.setFillColor(color)
            points = []
            for row in range(0, self.tblCoords.rowCount()):
                x, y = self.xyMap(row)
                xy = QgsPointXY(x, y)
                points.append(QgsPoint(xy))
            # close line????
            if self.layer.geometryType() == QgsWkbTypes.GeometryType.PolygonGeometry:
                row = 0
                x, y = self.xyMap(row)
                xy = QgsPointXY(x, y)
                points.append(QgsPoint(xy))
            geom = QgsGeometry.fromPolyline(points)
            self.rubber.setToGeometry(geom, self.layer)
            self.canvas.refresh()
        except Exception as e:
            self.info.err(e)

    def closeEvent(self, event):
        if self.debug: self.info.log("closeEvent")
        self.reset()

    def hideEvent(self, a0):
        if self.debug: self.info.log("hideEvent: visible:", self.isVisible())
        self.reset()  # also raises when docking!
        QTimer.singleShot(100, self.restore)

    def restore(self):
        if self.debug: self.info.log("restore: visible:", self.isVisible())
        if self.isVisible():
            self.currentCellChanged(self.tblCoords.currentRow(), 0, 0, 0)


class MyButton(QLabel):
    click = pyqtSignal()

    def __init__(self, gtoMain, parent=None):
        super(MyButton, self).__init__(parent)
        self.gtomain = gtoMain
        self.icon = None
        self.pm = None
        self.setContentsMargins(0, 0, 0, 0)
        self.setMargin(0)

    # @ pyqtSlot()
    # def on_click(self,*args):
    #     self.click.emit()

    def setIcon(self, icon, size=24):
        self.icon = icon
        self.pm = self.icon.pixmap(self.icon.actualSize(QSize(size, size)))
        self.setPixmap(self.pm)

    def mouseReleaseEvent(self, MouseEvent):
        if MouseEvent.button() == Qt.LeftButton and self.isEnabled(): self.click.emit()

    def resizeEvent(self, a0):
        self.setIcon(self.icon, a0.size().height() - 5)
