#!/usr/bin/python
# -*- coding: utf-8 -*-

from qgis.core import QgsProject, QgsVectorLayer, QgsVectorLayerCache, QgsAttributeTableConfig, QgsFeatureRequest
from qgis.gui import QgsAttributeTableModel, QgsAttributeTableView, QgsAttributeTableFilterModel, QgsAttributeEditorContext
from PyQt5.QtCore import Qt, QObject, QSortFilterProxyModel, pyqtSignal, QCoreApplication
from PyQt5.QtWidgets import QDockWidget, QLabel, QComboBox, QToolBar, QHeaderView, QVBoxLayout, QScrollArea, QLayout, QHBoxLayout, QWidget, QPushButton, QCompleter, QListView
import qgis.core


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

            # tool data widegt
            self.toolbar_dock = self.config.get("toolbar_dock", None)
            # widget
            self.toolbar = None
            self.wid = Widget(self, self.iface.mainWindow())
            if self.toolbar_dock is not None:
                # load toolbar
                objName = "gtoTB_" + gtoTool.action.objectName()
                self.toolbar = self.gtomain.helper.findToolbar(self.iface, objName)
                if self.toolbar is None:
                    if self.debug: self.info.log("load", objName)
                    self.toolbar = QToolBar()
                    self.toolbar.setObjectName(objName)
                    self.toolbar.setWindowTitle(u'GTO Suche')
                    self.toolbar.setAllowedAreas(Qt.BottomToolBarArea | Qt.TopToolBarArea)
                    self.iface.mainWindow().addToolBarBreak(self.toolbar_dock)
                    self.iface.addToolBar(self.toolbar, self.toolbar_dock)
                else:
                    self.toolbar.clear()
                    self.toolbar.setHidden(False)
            else:
                self.toolbar = self.gtomain.gtotb
            self.toolbar.addWidget(self.wid)
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


class Widget(QWidget):
    def __init__(self, gtoAction, parent=None):
        super(Widget, self).__init__(parent)
        # from gtoAction
        # layout
        self.layout = QHBoxLayout(self)
        self.gtomain = gtoAction.gtomain
        self.helper = self.gtomain.helper
        self.iface = self.gtomain.iface
        self.prj = QgsProject.instance()
        self.canvas = self.iface.mapCanvas()
        # gtoAction
        self.info = gtoAction.info
        self.debug = gtoAction.debug
        try:
            # tooldata
            self.config = gtoAction.config
            self.tools = self.config.get("tools", [])

            self.layer = self.config.get('layer', None)
            self.result_fields = self.config.get('result_fields', [])
            self.queries = self.config.get('queries', [])

            # do the job
            self.layer = self.prj.mapLayersByName(self.layer)
            if self.layer is not None:
                self.layer = self.layer[0]  # if duplicate names
                self.iface.setActiveLayer(self.layer)
            else:
                self.layer = self.iface.activeLayer()
            self.prevCbo = None
            self.cbo = None
            self.index = 0
            for query in self.queries:
                if self.debug: self.info.log(query['label'])
                self.lbl = QLabel(query['label'])
                self.layout.addWidget(self.lbl)
                self.repaint()
                QCoreApplication.processEvents()
                self.cbo = ExtendedComboBox(gtoAction, self)
                self.cbo.setQuery(query)
                self.cbo.setLayer(self.layer)
                self.cbo.setObjectName('cbo' + str(self.index))
                self.layout.addWidget(self.cbo)
                if self.debug: self.info.log("prevcbo", self.prevCbo)
                if self.prevCbo is not None:  # connect to listindex changed
                    self.prevCbo.setChild(self.cbo)
                self.prevCbo = self.cbo
                self.index = self.index + 1

            self.showResult = ShowResult(gtoAction)
            if self.debug: self.layout.addWidget(self.showResult)
            self.prevCbo.setChild(self.showResult)

            self.repaint()
            QCoreApplication.processEvents()
        except Exception as e:
            self.info.err(e)

    def closeEvent(self, a0):
        self.reset()

    def reset(self):
        try:
            if self.debug: self.info.log("widget reset")
        except Exception as e:
            self.info.err(e)


class ExtendedComboBox(QComboBox):
    isHidden = pyqtSignal()

    def __init__(self, gtoAction, parent=None):
        super(ExtendedComboBox, self).__init__(parent)

        self.gtomain = gtoAction.gtomain
        self.debug = gtoAction.debug
        self.info = gtoAction.info
        self.config = gtoAction.config
        self.tools = []
        self.doQueryOnShow = False

        # speed up
        # //  For performance reasons use this policy on large models
        # // or AdjustToMinimumContentsLengthWithIcon
        self.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLength)

        #  // Improving Performance:  It is possible to give the view hints
        # // about the data it is handling in order to improve its performance
        # // when displaying large numbers of items. One approach that can be taken
        # // for views that are intended to display items with equal sizes
        # // is to set the uniformItemSizes property to true.
        self.view().setUniformItemSizes(True)
        #  // This property holds the layout mode for the items. When the mode is Batched,
        # // the items are laid out in batches of batchSize items, while processing events.
        # // This makes it possible to instantly view and interact with the visible items
        # // while the rest are being laid out.
        self.view().setLayoutMode(QListView.Batched)
        #  // batchSize : int
        # // This property holds the number of items laid out in each batch
        # // if layoutMode is set to Batched. The default value is 100."

        try:
            self.setInsertPolicy(self.NoInsert)
            self.setFocusPolicy(Qt.StrongFocus)
            self.setEditable(True)

            # add a filter model to filter matching items
            self.pFilterModel = QSortFilterProxyModel(self)
            self.pFilterModel.setFilterCaseSensitivity(Qt.CaseInsensitive)
            self.pFilterModel.setSourceModel(self.model())

            # add a completer, which uses the filter model
            self.completer = QCompleter(self.pFilterModel, self)
            # always show all (filtered) completions
            self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
            self.setCompleter(self.completer)

            # connect signals
            self.lineEdit().textEdited.connect(self.pFilterModel.setFilterFixedString)
            self.lineEdit().textEdited.connect(self.correctInput)

            # corrct qt bug:
            style = "QWidget{font-size: " + str(self.fontInfo().pointSize()) + "pt;font-family: " + self.fontInfo().family() + ";}"
            self.completer.popup().setStyleSheet(style)
            # stat vars
            self.query = None
            self.layer = None
            self.doQueryOnShow = False
            self.masterExpression = None
            self.child = None

        except Exception as e:
            self.info.err(e)

    def hideEvent(self, e):
        self.isHidden.emit()

    def showEvent(self, e):
        try:
            if self.doQueryOnShow:
                self.buildList()
        except:
            pass

    # on model change, update the models of the filter and completer as well
    def setModel(self, model):
        super(ExtendedComboBox, self).setModel(model)
        self.pFilterModel.setSourceModel(model)
        self.completer.setModel(self.pFilterModel)

    # on model column change, update the model column of the filter and completer as well
    def setModelColumn(self, column):
        self.completer.setCompletionColumn(column)
        self.pFilterModel.setFilterKeyColumn(column)
        super(ExtendedComboBox, self).setModelColumn(column)

    def setQuery(self, query):
        self.query = query
        self.tools = self.query.get('tools', [])
        self.doQueryOnShow = query.get('load', True)

    def Layer(self):
        return self.layer

    def setLayer(self, layer):
        self.layer = layer

    def Expression(self):
        return self.currentData()

    def Query(self):
        return self.query

    def setChild(self, cbo):
        try:
            self.child = cbo
        except Exception as e:
            self.info.err(e)

    # on selection of an item from the completer, select the corresponding item from combobox
    def on_completer_activated(self, text):
        try:
            if text is not None:
                index = self.findText(text, Qt.MatchContains)
                self.setCurrentIndex(index)
                if self.debug: self.info.log(self.objectName(), "index:", index)
        except Exception as e:
            self.info.err(e)

    def correctInput(self, text=None):
        try:
            if self.debug: self.info.log("correctInput", text)
            if text is not None:
                index = self.findText(text, Qt.MatchContains)
                if self.debug: self.info.log(self.objectName(), "index:", index)
                if index == -1:
                    self.setCurrentText(text[:-1])
                    self.on_completer_activated(text[:-1])
                index = self.findText(self.currentText(), Qt.MatchExactly)
                if index == -1:
                    self.resetFilter(False)
                else:
                    if index == self.currentIndex():
                        self.indexChanged(index)
                    else:
                        self.setCurrentIndex(index)
        except Exception as e:
            self.info.err(e)

    def resetFilter(self, resetSelf):
        try:
            if self.debug: self.info.log(self.objectName(), "reset")
            if resetSelf: self.setMasterExpression(None)
            if self.child: self.child.resetFilter(True)
        except Exception as e:
            self.info.err(e)

    def setMasterExpression(self, masterExpression):
        try:
            if self.debug: self.info.log(self.objectName(), "setMasterExpression", self.masterExpression, "to", masterExpression)
            self.masterExpression = masterExpression
            if self.doQueryOnShow:
                self.buildList()
            else:
                if self.masterExpression is None:
                    self.clear()
                else:
                    self.buildList()
        except Exception as e:
            self.info.err(e)

    def buildList(self):
        if self.debug: self.info.log(self.objectName(), "buildList", self.query)

        self.setCurrentText('Lade...')
        self.setEnabled(False)
        self.repaint()
        if self.debug: self.info.log(self.objectName(), "excecuteQuery")
        try:
            self.currentIndexChanged.disconnect()
        except:
            pass
        try:
            self.clear()
            req = qgis.core.QgsFeatureRequest()
            req.setFlags(qgis.core.QgsFeatureRequest.NoGeometry)
            req.setSubsetOfAttributes(self.query['fields'], self.layer.fields())
            req.addOrderBy(self.query['fields'][0], True, True)
            if self.masterExpression is not None:
                req.setFilterExpression(self.masterExpression)
            values = []
            features = self.layer.getFeatures(req)
            for feat in features:
                displayStr = ''
                expr = ''
                for fn in self.query['fields']:
                    idx = self.layer.fields().indexFromName(fn)
                    if idx != -1:
                        value = feat[fn]
                        if isinstance(value, str):
                            value = "'" + value + "'"
                        if expr == '':
                            expr = expr + '"{0}"='.format(fn) + str(value)
                        else:
                            expr = expr + ' AND ' + '"{0}"='.format(fn) + str(value)
                        displayStr = displayStr + str(feat[fn])
                    else:
                        displayStr = displayStr + str(fn)
                if not displayStr in values and displayStr.strip() != '':
                    values.append(displayStr)
                    self.addItem(displayStr, expr)
            if self.debug: self.info.log(self.objectName(), "items:", self.count())
            self.setCurrentIndex(-1)
            self.setSizeAdjustPolicy(self.AdjustToContents)
            self.setEnabled(True)
            self.completer.activated.connect(self.on_completer_activated)
            self.currentIndexChanged.connect(self.indexChanged)

            if self.masterExpression is not None:
                if self.count() == 1:
                    if self.debug: self.info.log(self.objectName(), "self.setCurrentIndex(0)", "self.masterExpression", self.masterExpression)
                    self.setCurrentIndex(0)
            else:
                self.setCurrentIndex(-1)
        except Exception as e:
            self.info.err(e)

    def indexChanged(self, index):
        try:
            expr = self.currentData()
            if self.debug: self.info.log(self.objectName(), "cbo Expr:", expr)
            if self.masterExpression is not None:
                if expr is not None:
                    expr = self.masterExpression + ' AND ' + expr
                else:
                    expr = self.masterExpression
            self.info.log(self.objectName(), "Expr:", expr)
            if expr is not None:
                self.layer.selectByExpression(expr)
                self.gtomain.runcmd(self.tools)
            if self.child is not None:
                if self.debug: self.child.objectName()
                self.child.setMasterExpression(expr)
        except Exception as e:
            self.info.err(e)


class ShowResult(QLabel):
    def __init__(self, gtoAction, parent=None):
        super(ShowResult, self).__init__()
        # from gtoAction
        self.gtomain = gtoAction.gtomain
        self.helper = self.gtomain.helper
        self.iface = self.gtomain.iface
        self.prj = QgsProject.instance()
        self.canvas = self.iface.mapCanvas()
        # gtoAction
        self.info = gtoAction.info
        self.debug = gtoAction.debug
        try:
            # tooldata
            self.config = gtoAction.config
            self.tools = self.config.get("tools", [])
        except Exception as e:
            self.info.err(e)

    def setMasterExpression(self, expr):
        try:
            if self.debug: self.info.log("ShowResult", "setMasterExpression", expr)
            self.setText(self.iface.activeLayer().name() + ":" + str(expr))
            if expr:
                # self.iface.activeLayer().selectByExpression(expr)
                self.gtomain.runcmd(self.tools)
        except Exception as e:
            self.info.err(e)

    def clear(self):  # dummy (combobox)
        pass

    def reset(self, *args):
        pass  # from gto_main line 502

    def resetFilter(self, *args):
        pass

# from PyQt5 import QtCore, QtGui, QtWidgets, uic
#
# class CompleterDelegate(QtWidgets.QStyledItemDelegate):
#     def initStyleOption(self, option, index):
#         super(CompleterDelegate, self).initStyleOption(option, index)
#         option.backgroundBrush = QtGui.QColor("red")
#         option.palette.setBrush(QtGui.QPalette.Text, QtGui.QColor("blue"))
#         option.displayAlignment = QtCore.Qt.AlignCenter
#
# class Principal(QtWidgets.QMainWindow):
#     def __init__(self):
#         super(Principal, self).__init__()
#         uic.loadUi("uno.ui",self)
#         completer = QtWidgets.QCompleter(self)
#         self.lineEdit.setCompleter(completer)
#         model = QtCore.QStringListModel()
#         completer.setModel(model)
#         delegate = CompleterDelegate(self.lineEdit)
#         completer.popup().setStyleSheet("background-color:red;")
#         completer.popup().setItemDelegate(delegate)
#         self.get_data(model)
#
#     def get_data(self,model):
#         model.setStringList(["uno","dos","tres","cuatro","este es mi nombre"])
#
# if __name__ == '__main__':
#     import sys
#     app  = QtWidgets.QApplication(sys.argv)
#     p = Principal()
#     p.show()
#     sys.exit(app.exec_())