# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt, QFile, QTextStream, QStandardPaths, QTimer
from PyQt5.QtGui import QIcon, QPixmap, QFont, QBrush, QColor
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QAction, QWidgetAction, QDockWidget, QTreeWidgetItem, \
    QSplashScreen, \
    QHBoxLayout, QLabel, QToolButton, QComboBox, QSizePolicy, QToolBar, QHeaderView, QVBoxLayout, QTableView, \
    QTextBrowser, QWidgetItem

from PyQt5 import uic

from qgis.core import QgsProject, QgsMapLayerProxyModel, QgsVectorLayerCache, QgsFeatureRequest, QgsVectorLayer
from qgis.gui import QgsMapLayerComboBox, QgsAttributeTableView, QgsAttributeTableModel, QgsAttributeTableFilterModel, \
    QgsMapToolIdentifyFeature, QgsScaleRangeWidget, QgsScaleComboBox, QgsScaleWidget, QgsProjectionSelectionWidget

# import qgis  # QgsVectorLayerSelectionManager not in gui or core?

import os
import webbrowser
from .gto_tools import gtoAction


class GtoSplasher:
    def __init__(self, info):
        try:
            self.info = info
            self.splasher = None
            self.info.iface.mainWindow().showMinimized()
            qgisAppDataPath = QStandardPaths.standardLocations(QStandardPaths.AppDataLocation)[0]
            file = os.path.join(qgisAppDataPath, "splash.png")
            if not os.path.isfile(file):
                file = os.path.join(os.path.dirname(__file__), "splash.png")
            if os.path.isfile(file):
                pixmap = QPixmap(file)
                self.splasher = QSplashScreen(pixmap, Qt.WindowStaysOnTopHint)
                self.splasher.setPixmap(pixmap)
                self.splasher.show()
        except Exception as e:
            self.info.err(e)

    def log(self, msg):
        try:
            if self.splasher is not None:
                self.splasher.show()
                self.splasher.showMessage(msg, Qt.AlignCenter | Qt.AlignBottom)
                QApplication.instance().processEvents()
            self.info.log('Splasher:', msg)
        except Exception as e:
            self.info.err(e)

    def close(self):
        if self.splasher is not None:
            self.splasher.close()


class GtoToolCombo(QComboBox):  # alternative to ToolButton with menu
    def __init__(self, gtomain, actionNamesList, parent=None):
        super(GtoToolCombo, self).__init__(parent)
        self.gtomain = gtomain
        self.info = self.gtomain.getInfoObject(self)
        self.setEditable(False)
        try:
            self.actions = []
            for tool in actionNamesList:
                if isinstance(tool, str):
                    action = self.gtomain.findAction(tool)
                    if action is not None:
                        self.actions.append(action)
                elif isinstance(tool, QAction):
                    self.actions.append(tool)
            for action in self.actions:
                self.addItem(action.icon(), action.text())
            # self.currentIndexChanged.connect(self.runAction)
            self.activated.connect(self.runAction)
        except Exception as e:
            self.info.err(e)

    def runAction(self, index):
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            if index != -1:
                self.setEnabled(False)
                QApplication.processEvents()
                action = self.actions[index]
                action.trigger()
        except Exception as e:
            self.info.err(e)
        finally:
            self.setEnabled(True)
            QApplication.restoreOverrideCursor()


class GtoToolbar(QToolBar):
    def __init__(self, gtoObj, objName, title, parent=None):
        super(GtoToolbar, self).__init__(parent)
        self.setObjectName(objName)
        self.setWindowTitle(title)
        self.init = True
        self.gtomain = gtoObj.gtomain
        self.info = self.gtomain.getInfoObject(self)
        self.debug = self.info.debug
        self.helper = self.gtomain.helper
        self.tools = None
        self._hasTools = False
        allowed_areas = Qt.TopToolBarArea | Qt.BottomToolBarArea
        self.setAllowedAreas(allowed_areas)

    def hasTools(self):
        return self._hasTools  # for gto toolbar

    def addTools(self, tools, hide_button=False):  # for gto toolbar
        try:
            if self.tools != tools:
                self.tools = tools
                self.clear()
                count = len(self.findChildren(QWidget))  # hidden default QWidgets
                self._hasTools = False
                # add tools, maybe just executed?
                self.helper.addTools(self, tools, self)
                # check again, if really visible tools are added
                if count != len(self.findChildren(QWidget)):
                    self._hasTools = True
                if hide_button: self.helper.addToolbarClose()
        except Exception as e:
            self.info.err(e)


class GtoDockWidgetAttributeTable(QDockWidget):
    def __init__(self, gtomain, parent=None):
        super(GtoDockWidgetAttributeTable, self).__init__(parent)

        self.gtomain = gtomain
        self.info = gtomain.info
        self.debug = gtomain.debug
        self.iface = gtomain.iface
        self.layer = self.iface.activeLayer()
        self.canvas = self.iface.mapCanvas()
        self.canvas.currentLayerChanged.connect(self.reload)
        self.setObjectName('GtoAttributeTable')  # layout
        self.dockWidgetContents = QWidget()
        self.view = QgsAttributeTableView()
        try:
            self.layout = QVBoxLayout(self)
            path = os.path.dirname(__file__)
            btn_wid = uic.loadUi(os.path.join(path, 'mActionGTOopenGtoTable.ui'))
            self.btnSelect = btn_wid.btnReload
            self.btnSelect.clicked.connect(self.reload)
            self.btnSelectAll = btn_wid.btnSelectAll
            self.btnSelectAll.clicked.connect(self.select_all)
            self.btnClose = btn_wid.btnClose
            self.btnClose.clicked.connect(lambda: self.setHidden(True))
            # layout
            self.layout.addWidget(btn_wid)
            self.layout.addWidget(self.view)
            self.dockWidgetContents.setLayout(self.layout)
            self.setWidget(self.dockWidgetContents)
            # start
            self.reload()
        except Exception as e:
            self.info.err(e)

    def select_all(self):
        try:
            self.layer.selectByIds(self.attribute_table_filter_model.filteredFeatures())
        except Exception as e:
            self.info.err(e)

    def reload(self, *args):
        try:
            # the table
            self.layer = self.iface.activeLayer()
            self.setWindowTitle(
                self.iface.activeLayer().name() + ":: Ursprünglich selektierte Objekte: {0}".format(
                    self.layer.selectedFeatureCount()))
            self.vector_layer_cache = QgsVectorLayerCache(self.layer, 10000)
            self.attribute_table_model = QgsAttributeTableModel(self.vector_layer_cache)
            self.attribute_table_model.loadLayer()
            self.attribute_table_filter_model = QgsAttributeTableFilterModel(self.canvas, self.attribute_table_model)
            # filter
            self.attribute_table_filter_model.setFilterMode(QgsAttributeTableFilterModel.ShowFilteredList)
            self.attribute_table_filter_model.setFilteredFeatures(self.layer.selectedFeatureIds())

            self.view.setModel(self.attribute_table_filter_model)
            self.view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

            for f in self.layer.fields():
                # if self.debug: self.info.log("editorWidgetSetup:",f.name(),f.editorWidgetSetup().type())
                if f.editorWidgetSetup().type() == 'Hidden' and not self.debug:
                    self.view.horizontalHeader().setSectionHidden(self.layer.fields().indexOf(f.name()), True)
            # only follow selection on the map
            # self.selectionManager = qgis.QgsVectorLayerSelectionManager(self.layer, self.attribute_table_filter_model)
            # self.view.setFeatureSelectionManager(self.selectionManager)

            self.layer.selectionChanged.connect(self._selectionChanged)
        except Exception as e:
            self.info.err(e)

    def _selectionChanged(self, *args):
        if self.isVisible():
            self.gtomain.runcmd("mActionZoomToSelected")


class GtoWidgetActiveLayer(QWidget):
    def __init__(self, gtomain, parent=None):
        super(GtoWidgetActiveLayer, self).__init__(parent)
        # QWidgetAction.__init__(self,parent)
        self.iface = gtomain.iface
        self.info = gtomain.info
        self.canvas = self.iface.mapCanvas()
        # ui
        lay = QHBoxLayout(self)
        self.lblCaption=QLabel('Layer:')
        self.lblCaption.setToolTip("Aktiver Layer (selected features)")
        lay.addWidget(self.lblCaption)

        self.lblLayer = QLabel()
        self.qgsLayers = QgsMapLayerComboBox()
        self.qgsLayers.setCurrentIndex(-1)
        self.qgsLayers.setFilters(QgsMapLayerProxyModel.VectorLayer)

        lay.addWidget(self.lblLayer)

        self.setLayout(lay)

        # signals
        self.canvas.currentLayerChanged.connect(self.layer_changed)
        self.canvas.selectionChanged.connect(self.selection_changed)
        # start
        self.layer_changed(self.iface.activeLayer())

    def selection_changed(self, layer):
        try:
            selcount = len(layer.selectedFeatureIds())
            self.lblLayer.setText(layer.name() + ' ({0})'.format(selcount))
        except Exception as e:
            self.info.err(e)

    def layer_changed(self, layer):
        try:
            self.selection_changed(layer)
        except Exception as e:
            self.info.err(e)


class GtoWidgetQgisLayers(QWidget):
    def __init__(self, gtoObj, parent=None):
        super(GtoWidgetQgisLayers, self).__init__(parent)
        # QWidgetAction.__init__(self,parent)
        self.gtomain = gtoObj.gtomain
        self.info = self.gtomain.info
        self.iface = self.gtomain.iface
        self.canvas = self.iface.mapCanvas()
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

        self.qgsLayers = QgsMapLayerComboBox()
        self.qgsLayers.setMinimumContentsLength(25)
        self.qgsLayers.setMinimumWidth(300)
        self.qgsLayers.setCurrentIndex(-1)
        self.qgsLayers.setFilters(QgsMapLayerProxyModel.VectorLayer)
        #signals
        self.canvas.currentLayerChanged.connect(self.qgsLayers.setLayer)
        self.qgsLayers.layerChanged.connect(self.layer_changed)
        self.canvas.selectionChanged.connect(self.selection_changed)
        # ui
        lay = QHBoxLayout(self)
        self.caption ='Layer: ({0})'
        self.lblLayer=QLabel('Layer:')
        self.lblLayer.setToolTip("Aktiver Layer (selected features)")
        lay.addWidget(self.lblLayer)
        lay.addWidget(self.qgsLayers)
        self.setLayout(lay)
        # help QgsMapLayerComboBox ..:O
        self.timer = QTimer()
        self.timer.singleShot(100, self._setLayer)

    def selection_changed(self, layer):
        try:
            selcount = len(layer.selectedFeatureIds())
            self.lblLayer.setText(self.caption.format(selcount))
        except Exception as e:
            self.info.err(e)

    def layer_changed(self, layer):
        try:
            if layer is not None:
                self.selection_changed(layer)
                self.iface.setActiveLayer(layer)
                ml = QgsProject.instance().layerTreeRoot().findLayer(layer.id())
                if ml is not None:
                    ml.setItemVisibilityCheckedParentRecursive(True)
        except Exception as e:
            self.info.err(e)

    def _setLayer(self):
        try:
            layer = self.iface.activeLayer()
            if layer is not None:
                self.qgsLayers.setLayer(layer)
        except Exception as e:
            self.info.err(e)


class GTOtextBrowser(QTextBrowser):
    def __init__(self, gtoObj, parent=None):
        super(GTOtextBrowser, self).__init__(parent)

        self.info = gtoObj.info
        self.file = None

    def mouseDoubleClickEvent(self, e):
        try:
            if self.file is not None:
                os.startfile(self.file)
        except Exception as e:
            self.info.err(e)

    def setFile(self, file):
        try:
            self.file = file
            self.setToolTip('')
            if file is not None:
                if os.path.isfile(file):
                    self.setToolTip('Doppelklick um Datei <{0}> zu öffnen'.format(self.file))
                else:
                    self.setToolTip('Datei {0} nicht gefunden!'.format(self.file))
        except Exception as e:
            self.info.err(e)

    def setText(self, text, file=None):
        try:
            self.setFile(file)
            QTextBrowser.setText(self, text)
        except Exception as e:
            self.info.err(e)

    def setSource(self, name):
        try:
            file = name.path()[1:]  # name: QtCore.QUrl, web syntax! (file:)//D/...
            self.setFile(file)
            QTextBrowser.setSource(self, name)
        except Exception as e:
            self.info.err(e)


class GtoWidgetScale(QWidget):
    def __init__(self, gtomain, parent=None):
        super(GtoWidgetScale, self).__init__(parent)
        # QWidgetAction.__init__(self,parent)
        self.iface = gtomain.iface
        self.info = gtomain.info
        self.debug = gtomain.debug
        self.block = False
        try:
            self.canvas = self.iface.mapCanvas()
            # ui
            lay = QHBoxLayout(self)
            # -----
            self.lblLayer = QLabel("Maßstab:")
            lay.addWidget(self.lblLayer)
            self.wid = QgsScaleWidget(self)
            self.wid.setMinimumWidth(120)
            lay.addWidget(self.wid)
            # -----
            self.setLayout(lay)
            # signals
            self.canvas.scaleChanged.connect(self.scale_changed)
            self.wid.scaleChanged.connect(self.set_mapscale)
            # start
            self.scale_changed(self.canvas.scale())
        except Exception as e:
            self.info.err(e)

    def scale_changed(self, scale):
        try:
            # if self.debug: self.info.log("scale_changed", scale)
            # self.blockSignals(True)
            if not self.block:
                self.block = True
                self.wid.setScale(round(scale, 0))
                self.block = False
            # self.blockSignals(False)
        except Exception as e:
            self.info.err(e)

    def set_mapscale(self, scale):
        try:
            # if self.debug: self.info.log("set_mapscale", scale)
            # self.blockSignals(True)
            if not self.block:
                self.block = True
                self.canvas.zoomScale(scale)
                self.block = False
            # self.blockSignals(False)
        except Exception as e:
            self.info.err(e)


class GtoWidgetProjectionSelection(QWidget):
    def __init__(self, gtomain, parent=None):
        super(GtoWidgetProjectionSelection, self).__init__(parent)
        # QWidgetAction.__init__(self,parent)
        self.iface = gtomain.iface
        self.info = gtomain.info
        try:
            self.prj = QgsProject.instance()
            # ui
            lay = QHBoxLayout(self)
            # -----
            self.lblLayer = QLabel("Projektion:")
            lay.addWidget(self.lblLayer)
            self.wid = QgsProjectionSelectionWidget(self)
            # help the QGIS widget:/
            self.wid.setMinimumWidth(350)
            self.wid.setSizePolicy(self.lblLayer.sizePolicy())
            lay.addWidget(self.wid)
            for tb in self.wid.findChildren(QToolButton):
                tb.setIconSize(self.iface.iconSize())
            # -----
            self.setLayout(lay)
            # signals
            self.prj.crsChanged.connect(self.prj_crs_changed)
            self.wid.crsChanged.connect(self.set_prj_crs)
            # start
            self.wid.setCrs(self.prj.crs())
        except Exception as e:
            self.info.err(e)

    def prj_crs_changed(self):
        try:
            self.wid.setCrs(self.prj.crs())
        except Exception as e:
            self.info.err(e)

    def set_prj_crs(self, crs):
        try:
            self.prj.setCrs(self.wid.crs())
        except Exception as e:
            self.info.err(e)
