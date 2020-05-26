#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from qgis.core import QgsProject, QgsExpressionContext, QgsExpressionContextScope, QgsExpression, \
    QgsExpressionContextUtils, QgsVectorLayer
from qgis.gui import QgsQueryBuilder
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QCloseEvent, QFocusEvent
from PyQt5.QtWidgets import QWidget, QMainWindow, QHBoxLayout, QToolButton, QInputDialog, QComboBox, QDialogButtonBox, \
    QVBoxLayout, \
    QFrame, QSizePolicy, QLabel, QListWidget, QListWidgetItem, QToolBar, QDialog, QMessageBox
from PyQt5 import uic


class run(object):
    def __init__(self, id, gtoTool, config, debug):
        super(run, self).__init__()
        try:
            # references
            self.result = None
            self.debug = debug
            self.id = id
            self.config = config
            self.info = gtoTool.info
            self.gtomain = gtoTool.gtomain
            self.helper = self.gtomain.helper
            self.metadata = self.gtomain.metadata
            self.iface = self.gtomain.iface

            self.prj = QgsProject.instance()

            # tool data
            self.toolbar_dock = self.config.get("toolbar_dock", None)
            self.expr = self.config.get('expression', '')
            self.targetlayer = self.config.get('targetlayer', 'Layer not defined')
            self.tools = self.config.get('tools', [])
            # init
            if id > 0:  # fixed query
                self.EvalExpr(self.targetlayer, self.expr)
                self.gtomain.runcmd(self.tools)
            else:
                # widget
                self.toolbar = None
                self.wid = Widget(self, self.iface.mainWindow())
                if self.toolbar_dock != None:
                    # load toolbar
                    objName = "gtoTB_" + gtoTool.action.objectName()
                    self.toolbar = self.gtomain.helper.findToolbar(self.iface, objName)
                    if self.toolbar is None:
                        if self.debug: self.info.log("load", objName)
                        self.toolbar = self.helper.getToolBar(self, self.objName, u'GTO Expression Manager',
                                                              self.iface.mainWindow())
                        self.iface.mainWindow().addToolBarBreak(self.toolbar_dock)
                        self.iface.addToolBar(self.toolbar, self.toolbar_dock)
                    else:
                        self.toolbar.clear()
                        self.toolbar.setHidden(False)
                else:
                    self.toolbar = self.gtomain.gtotb
                self.toolbar.addWidget(self.wid)
                self.wid.setIconSizes(self.iface.iconSize(False))
                self.toolbar.setIconSize(self.iface.iconSize(False))
                if self.config.get("show_hide_button", False): self.helper.addToolbarClose(self.toolbar)
                self.toolbar.visibilityChanged.connect(self.reset)
        except Exception as e:
            self.info.err(e)

    def reset(self, *args):  # from (gto)toolbar hidden/shown
        try:
            if self.debug: self.info.log("gtoAction reset")
            self.wid.reset()
        except Exception as e:
            self.info.err(e)

    def EvalExpr(self, layername, expr):
        try:
            layer = self.prj.mapLayersByName(layername)[0]
            context = QgsExpressionContext()
            scope = QgsExpressionContextScope()
            context.appendScope(scope)
            listOfResults = []
            features = [feat for feat in layer.getFeatures()]
            for feat in features:
                scope.setFeature(feat)
                exp = QgsExpression(expr)
                if exp.evaluate(context):
                    listOfResults.append(feat.id())
            if len(listOfResults) == 0:
                self.info.msg('Kein Ergebnis!')
            else:
                layer.selectByIds(listOfResults)
                self.iface.setActiveLayer(layer)
                self.gtomain.runcmd(self.tools)
        except Exception as e:
            self.info.err(e)


class Widget(QWidget):

    def __init__(self, gtoAction, parent=None):
        super(Widget, self).__init__(parent)
        # from gtoAction
        self.gtomain = gtoAction.gtomain
        self.info = gtoAction.info
        self.debug = gtoAction.debug
        try:
            # from main
            self.helper = self.gtomain.helper
            self.iface = self.gtomain.iface
            self.metadata = self.gtomain.metadata
            self.prj = self.gtomain.prj
            self.canvas = self.iface.mapCanvas()
            # tooldata
            self.config = gtoAction.config
            self.tools = gtoAction.tools
            self.layers = self.config.get('layers', None)

            # load ui
            uic.loadUi(os.path.join(os.path.dirname(__file__), 'gto_expression.ui'), self)
            self.btnOk.clicked.connect(lambda: self.EvalExpr(self.lblLayer.text(), self.lblExpr.text()))
            self.btnDelete.clicked.connect(self.deleteEntry)
            self.btnNew.clicked.connect(self.newEntry)

            self.cboQuieries.currentIndexChanged.connect(self.setData)

            self.loadData()
            self.setData()

        except Exception as e:
            self.info.err(e)

    def setIconSizes(self, toolbar):
        try:
            btns = self.findChildren(QToolButton)
            for btn in btns:
                btn.setIconSize(self.iface.iconSize())
        except Exception as e:
            self.info.err(e)

    def reset(self, *args):  # from gtotoolbar before cleared
        try:
            if self.debug: self.info.log("widget reset")
        except Exception as e:
            self.info.err(e)

    def newEntry(self):
        try:
            if self.selectLayer() == QDialog.Accepted:
                ok, sql = self.showQueryBuilder(self.iface.activeLayer(), False)
                if ok and sql:
                    newName, ok = QInputDialog().getText(self, 'Neue Abfrage', "Name:")
                    if newName and ok:
                        if not self.cboQuieries.findText(newName, Qt.MatchExactly):
                            self.info("Abfrage <%s> existiert bereits!" % newName)
                        else:
                            self.cboQuieries.addItem(newName, [sql, self.iface.activeLayer().name()])
                            self.cboQuieries.setCurrentIndex(self.cboQuieries.findText(newName, Qt.MatchExactly))
                            if self.debug: self.info.log(self.cboQuieries.currentData())
                            self.saveData()
        except Exception as e:
            self.info.err(e)

    def loadData(self):
        try:
            file = os.path.join(self.metadata.dirGTO, 'expressions.txt')
            if self.debug: self.info.log("Data file:", file)
            if os.path.isfile(file):
                f = open(file, 'r')
                content = f.readlines()
                for line in content:
                    try:
                        data = line.split('|')
                        self.cboQuieries.addItem(data[0], [data[1], data[2]])
                    except Exception as e:
                        self.info.err(e)
                f.close()
                os.remove(file)
                if self.debug: self.info.log("File data:", content)
            else:
                # json
                file = os.path.join(self.metadata.dirGTO, 'expressions.json')
                data = self.helper.readJson(file)
                if data is not None:
                    for k in data.keys():
                        v = data[k]
                        if self.debug: self.info.log(k, v)
                        self.cboQuieries.addItem(k, [v["expression"], v["layer"]])
            self.cboQuieries.repaint()
        except Exception as e:
            self.info.err(e)

    def deleteEntry(self):
        try:
            if self.info.gtoQuestion('Abfrage <{0}> löschen?'.format(self.cboQuieries.currentText()),
                                     "Abfrage löschen") == QMessageBox.Yes:
                self.cboQuieries.removeItem(self.cboQuieries.currentIndex())
                if self.cboQuieries.count() == 0:
                    self.lblLayer.setText('')
                    self.lblExpr.setText('')
                self.saveData()
        except Exception as e:
            self.info.err(e)

    def saveData(self):
        try:
            file = os.path.join(self.metadata.dirGTO, 'expressions.json')
            if self.debug: self.info.log("saveData:", file)
            data = {}
            for i in range(self.cboQuieries.count()):
                idata = self.cboQuieries.itemData(i)
                data[self.cboQuieries.itemText(i)] = {"layer": idata[1], "expression": idata[0]}
            if self.debug: self.info.log("saveData", data)
            if os.path.isfile(file): os.remove(file)
            self.helper.writeJson(file, data)
        except Exception as e:
            self.info.err(e)

    def setData(self):
        try:
            data = self.cboQuieries.currentData()
            if data:
                expr = data[0]
                layname = data[1]
                self.lblLayer.setText(layname)
                self.lblExpr.setText(expr)
        except Exception as e:
            self.info.err(e)

    def EvalExpr(self, layername, expr):
        try:
            index =self.cboQuieries.currentIndex()
            layer = self.prj.mapLayersByName(layername)[0]
            context = QgsExpressionContext()
            scope = QgsExpressionContextScope()
            context.appendScope(scope)
            listOfResults = []
            features = [feat for feat in layer.getFeatures()]
            for feat in features:
                scope.setFeature(feat)
                exp = QgsExpression(expr)
                if exp.evaluate(context):
                    listOfResults.append(feat.id())
            if len(listOfResults) == 0:
                self.info.msg('Kein Ergebnis!')
            else:
                layer.selectByIds(listOfResults)
                self.iface.setActiveLayer(layer)
                self.gtomain.runcmd(self.tools)
            self.cboQuieries.setCurrentIndex(index)
        except Exception as e:
            self.info.err(e)

    def showQueryBuilder(self, layer, filter, sql=None):
        try:
            if not layer: layer = self.iface.activeLayer()
            self.query_builder = QgsQueryBuilder(layer, self.iface.mainWindow())
            if sql: self.query_builder.setSql(sql)
            self.query_builder.accept()
            result = self.query_builder.exec_()
            if self.debug:  self.info.log("QueryBuilder", self.query_builder.sql(), result, layer.subsetString())
            if not filter: layer.setSubsetString(None)
            return result, self.query_builder.sql()
        except Exception as e:
            self.info.err(e)

    def selectLayer(self, editable=False):
        try:
            self.dlgLayers = QDialog(self.iface.mainWindow())
            self.dlgLayers.setWindowTitle('Neue Abfrage')
            self.lay = QVBoxLayout(self.dlgLayers)
            self.lay.addWidget(QLabel("Layerauswahl:"))
            self.LayerList = QListWidget()
            self.lay.addWidget(self.LayerList)
            self.btnBox = QDialogButtonBox(self.dlgLayers)
            self.btnBox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
            self.lay.addWidget(self.btnBox)
            if self.layers != None:
                for ml in self.layers:
                    try:
                        lay = self.prj.mapLayersByName(ml)[0]
                        item = QListWidgetItem(lay.name())
                        self.LayerList.addItem(item)
                    except:
                        pass
            else:
                vectorLayers = [layer for layer in self.iface.mapCanvas().layers()]
                for ml in vectorLayers:
                    self.info.log(type(ml))
                    if isinstance(ml, QgsVectorLayer):
                        item = QListWidgetItem(ml.name())
                        self.LayerList.addItem(item)
            if self.iface.activeLayer():
                items = self.LayerList.findItems(self.iface.activeLayer().name(), Qt.MatchExactly)
                if len(items) > 0:
                    self.LayerList.setCurrentItem(items[0])
            self.btnBox.accepted.connect(self.setActiveLayer)
            self.btnBox.rejected.connect(self.dlgLayers.reject)
            return self.dlgLayers.exec_()
        except Exception as e:
            self.info.err((e))

    def setActiveLayer(self):
        try:
            lay = self.LayerList.currentItem().text()
            lay = self.prj.mapLayersByName(lay)[0]
            self.iface.setActiveLayer(lay)
            self.dlgLayers.accept()
        except Exception as e:
            self.info.err((e))
