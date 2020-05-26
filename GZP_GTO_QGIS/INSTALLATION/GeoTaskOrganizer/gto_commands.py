#!/usr/bin/python
# -*- coding: utf-8 -*-

from builtins import str
from PyQt5.QtWidgets import QMessageBox, QDockWidget, QPlainTextEdit, QStackedWidget, QToolBar, QInputDialog, QLineEdit, \
    QToolButton
from PyQt5.QtCore import Qt

from qgis.core import QgsProject, QgsDataSourceUri, QgsRectangle, QgsPointXY, QgsGeometry
from qgis.gui import QgsQueryBuilder, QgsDualView

import os
import io
import webbrowser
import json
import time

def gto_test(gtoTool, debug, *args, **kwargs):
    info = gtoTool.info
    # info.log(type(gtoObj))
    info.msg("TESTCOMMAND!")
    info.log("parameters =", args)
    info.log("settings =", kwargs)
    LoadMapSettings(gtoTool, True)
    SaveMapSettings(gtoTool, True)


def SaveMapSettings(gtoTool, debug, *args, **kwargs):
    try:
        iface = gtoTool.iface
        info = gtoTool.info
        dirSettings = os.path.join(gtoTool.metadata.dirUserAppData, 'mapsettings')
        if debug: info.log('Pfad', dirSettings)
        if not os.path.exists(dirSettings):
            os.mkdir(dirSettings)
        file = os.path.basename(QgsProject.instance().fileName())
        file = os.path.join(dirSettings, file + '.json')
        # get layer visibility
        layers_data = {}
        prj = QgsProject.instance()
        for layer in prj.layerTreeRoot().findLayers():  # QgsLayerTreeLayer
            if not layer.name() in layers_data:
                layers_data[layer.name()] = layer.itemVisibilityChecked()
        # get group visibilty
        groups_data = {}
        # get group visibility
        for group in prj.layerTreeRoot().findGroups():  # QgsLayerTreeGroup
            if not group.name() in groups_data:
                groups_data[group.name()] = group.itemVisibilityChecked()
            getGroups(group, groups_data)

        # map extent
        rec = iface.mapCanvas().extent()  # QgsRectangle
        mapextent = (rec.xMinimum(), rec.yMinimum(), rec.xMaximum(), rec.yMaximum())
        # save metadata
        jdata = {'Extent': mapextent, 'Layers': layers_data, 'Groups': groups_data}
        with open(file, 'w', encoding='utf8') as outfile:
            sort = True
            json.dump(jdata, outfile, ensure_ascii=False, sort_keys=sort, indent=4)

    except Exception as e:
        info.err(e)


def getGroups(ParentNode, groups_data):
    for node in ParentNode.children():  # QgsLayerTreeNode
        if node.nodeType() == 0:  # is group
            if not node.name() in groups_data:
                groups_data[node.name()] = node.itemVisibilityChecked()
            getGroups(node, groups_data)


def LoadMapSettings(gtoTool, debug, *args, **kwargs):
    try:
        iface = gtoTool.iface
        info = gtoTool.info
        dirSettings = os.path.join(gtoTool.metadata.dirUserAppData, 'mapsettings')
        file = os.path.basename(QgsProject.instance().fileName())
        file = os.path.join(dirSettings, file + '.json')

        # read metadata
        jdata = None
        with open(file, 'r', encoding='utf8') as infile:
            jdata = json.load(infile)

        layer_data = jdata.get('Layers', {})
        group_data = jdata.get('Groups', {})
        mapextent = jdata.get('Extent', [])

        # set the map
        prj = QgsProject.instance()
        # layers
        for key in layer_data:
            try:
                layer = prj.mapLayersByName(key)[0]
                visible = layer_data[key]
                prj.layerTreeRoot().findLayer(layer.id()).setItemVisibilityChecked(visible)
            except Exception as e:
                if debug: info.err(e)
        # groups
        for key in group_data:
            visible = group_data[key]
            prj.layerTreeRoot().findGroup(key).setItemVisibilityChecked(visible)
        # extent
        rec = QgsRectangle(mapextent[0], mapextent[1], mapextent[2], mapextent[3])
        iface.mapCanvas().setExtent(rec)
        iface.mapCanvas().refresh()
    except Exception as e:
        info.err(e)


def openAttributeTable(gtoObj, debug, *args, **kwargs):
    try:
        info = gtoObj.info
        ClosePanel(gtoObj, debug, *['AttributeTable'])
        time.sleep(0.1)
        # layer = gtoObj.iface.activeLayer()
        # gtoObj.iface.showAttributeTable (layer)#shows all features, indepent from qgis settings :S
        # ShowAttributeTableSelectedFeatures(gtoObj, debug, *[], **{"layer": layer})
        act = gtoObj.gtomain.findAction("mActionOpenTable")
        if act is not None: act.trigger()
        # dws = gtoObj.iface.mainWindow().findChildren(QDockWidget)
        # for dw in dws:
        #     if dw.objectName() == 'AttributeTable' and dw.isHidden()==False:
        #         for toolbar in dw.findChildren(QToolBar):
        #             toolbar.setIconSize(gtoObj.gtomain.gtotb.iconSize())
    except Exception as e:
        info.err(e)

def ShowAttributeTableSelectedFeatures(gtoObj, debug, *args, **kwargs):
    try:
        info = gtoObj.info
        expr = ''
        iface = gtoObj.iface
        layers = QgsProject.instance().mapLayersByName(kwargs['layer'])
        if layers:
            layer = layers[0]  # duplicte names => take the first
        else:
            layer = iface.activeLayer()
        if layer:
            provider = layer.dataProvider()
            uri = QgsDataSourceUri(provider.dataSourceUri())
            ID_name = uri.keyColumn()
            if ID_name == '': ID_name = 'fid'
            for f in layer.getSelectedFeatures():
                expr = expr + '%i,' % f.id()
            expr = '"%s"' % ID_name + ' IN (' + expr[:-1] + ')'
            if debug: gtoObj.info.log("ShowAttributeTableSelectedFeatures:", "expression:", expr)
            gtoObj.iface.showAttributeTable(layer, expr)
    except Exception as e:
        info.err(e)

def TabWidget(gtoObj, debug, *args, **kwargs):
    iface = gtoObj.iface
    parent = args[0]
    if isinstance(parent, str):
        parent = iface.mainWindow().findChild(QDockWidget, parent)
    if isinstance(parent, QDockWidget):
        if not parent.isFloating():
            dockstate = iface.mainWindow().dockWidgetArea(parent)
            dws = iface.mainWindow().findChildren(QDockWidget)
            for d in dws:
                if d is not parent:
                    if iface.mainWindow().dockWidgetArea(d) == dockstate and d.isHidden() == False:
                        iface.mainWindow().tabifyDockWidget(parent, d)
            parent.raise_()


def TabPanels(gtoObj, debug, *args, **kwargs):
    iface = gtoObj.iface
    dockstate = args[0]
    parent = None
    dws = iface.mainWindow().findChildren(QDockWidget)
    for d in dws:
        if d is not parent:
            if iface.mainWindow().dockWidgetArea(d) == dockstate and d.isHidden() == False:
                if parent is None:
                    parent = d
                else:
                    iface.mainWindow().tabifyDockWidget(parent, d)


def ClosePanel(gtoObj, debug, *args, **kwargs):
    iface = gtoObj.iface
    dws = iface.mainWindow().findChildren(QDockWidget)
    objname = args[0]
    for d in dws:
        if objname == d.objectName():
            d.close()


def WriteActions(gtoObj, debug, *args, **kwargs):
    iface = gtoObj.iface
    path = args[0]
    if path is None:
        path = gtoObj.gtomain.path_metadata
    path = os.path.join(path, "gtoActions.txt")
    actions = gtoObj.gtomain.gtoactions
    if os.path.exists(path):
        # QMessageBox.question(QWidget, QString, QString, QMessageBox.StandardButtons buttons = QMessageBox.Ok, QMessageBox.StandardButton defaultButton = QMessageBox.NoButton) -> QMessageBox.StandardButton
        # QMessageBox.question(QWidget, QString, QString, int, int button1 = 0, int button2 = 0) -> int
        # QMessageBox.question(QWidget, QString, QString, QString, QString button1Text = QString(), QString button2Text = QString(), int defaultButtonNumber = 0, int escapeButtonNumber = -1) -> int
        if QMessageBox.question(iface.mainWindow(), 'Datei', 'Datei \n%s\nextistiert.\n' % path + u'Überschreiben?',
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.No:
            return path
        else:
            os.remove(path)
    vals = {}
    i = 0
    for a in actions:
        i = +1
        key = a.objectName()
        if not key:
            key = "NoName_" + str(i)
        if key not in vals:
            if a.text():
                vals[key] = a.text()
            else:
                vals[key] = ""
    list = []
    for a, b in vals.items():
        list.append(a + "::" + b)
    slist = sorted(list)
    f = io.open(path, 'w')
    for t in slist:
        f.write(u"%s\n" % t)
    f.close()
    os.startfile(path)


def ClearMessageLog(gtoObj, debug, *args, **kwargs):
    iface = gtoObj.iface
    msgQDW = iface.mainWindow().findChild(QDockWidget, 'MessageLog')
    stackW = msgQDW.findChild(QStackedWidget, 'qt_tabwidget_stackedwidget')
    for c in stackW.children():
        if isinstance(c, QPlainTextEdit):
            if c.toPlainText().find('gto_plugin'):
                c.clear()

def wSetSelectSet(gtoObj, debug, *args, **kwargs):
    try:

        if gtoObj.gtomain.settings is not None:

            esubcommand = kwargs['esubcommand']
            layername = kwargs['objectclass']
            where = kwargs.get('whereclause')
            attribute = kwargs.get('attribute')

            iface = gtoObj.iface
            jdata = {}
            data = None

            if esubcommand == "SETSELECTSET_WHERECLAUSE":
                # jdata = {"commands": [{"ecommand": "SETSELECTSET","config": {"esubcommand": esubcommand, "objectclass": layername.encode('utf8'),"whereclause": where.('utf8')}}]}
                jdata = {"commands": [{"ecommand": "SETSELECTSET",
                                       "config": {"esubcommand": esubcommand, "objectclass": layername,
                                                  "whereclause": where}}]}
            elif esubcommand == "SETSELECTSET_ID":
                layers = QgsProject.instance().mapLayersByName(layername)
                legend = iface.layerTreeView()
                if layers:
                    layer = layers[0]  # duplicte names => take the first
                    if debug: gtoObj.info.log(type(layername))
                    # legend.setLayerVisible(layer, True)
                    # iface.legendInterface().setCurrentLayer(layer)
                    iface.setActiveLayer(layer)
                    data = gtoObj.gtomain.remote.getSelectedFeatures(gtoObj, debug, layer, attribute)
                # jdata = {"commands": [{"ecommand": "SETSELECTSET","config": {"esubcommand": esubcommand, "objectclass": layername.('utf8'),"attribute": attribute.encode('utf8'), "data": data}}]}
                jdata = {"commands": [{"ecommand": "SETSELECTSET",
                                       "config": {"esubcommand": esubcommand, "objectclass": layername,
                                                  "attribute": attribute, "data": data}}]}
            if debug:
                prefix = esubcommand + '.json'
                gtoObj.gtomain.remote.writeRemoteFile(jdata, prefix)
            gtoObj.gtomain.remote.writeRemoteFile(jdata)

    except  Exception as e:
        gtoObj.info.err(e)


def wZoomToFeatureSet(gtoObj, debug, *args, **kwargs):
    try:

        if gtoObj.gtomain.settings is not None:
            iface = gtoObj.iface
            jdata = {}

            esubcommand = kwargs['esubcommand']
            layername = kwargs['objectclass']
            attribute = kwargs.get('attribute')
            where = kwargs.get('whereclause')
            scale = kwargs.get('scale', 0)

            if debug: gtoObj.info.log(esubcommand, layername, attribute, scale)

            if esubcommand == 'ZOOMTOFEATURESET_WHERECLAUSE':
                # jdata = {"commands": [{"ecommand": "ZOOMTOFEATURESET","config": {"esubcommand": esubcommand, "objectclass": layername.encode('utf8'),"whereclause": where.encode('utf8'), "scale": scale}}]}
                jdata = {"commands": [{"ecommand": "ZOOMTOFEATURESET",
                                       "config": {"esubcommand": esubcommand, "objectclass": layername,
                                                  "whereclause": where, "scale": scale}}]}
            elif esubcommand == 'ZOOMTOFEATURESET_ID':
                prj = QgsProject.instance()
                layers = prj.mapLayersByName(layername)
                legend = iface.legendInterface()
                if layers:
                    layer = layers[0]  # duplicte names => take the first
                    iface.setActiveLayer(layer)
                    prj.layerTreeRoot().findLayer(layer.id()).setItemVisibilityCheckedParentRecursive(True)

                    data = gtoObj.gtomain.remote.getSelectedFeatures(gtoObj, debug, layer, attribute)
                # jdata={"commands":[{"ecommand": "ZOOMTOFEATURESET", "config": {"esubcommand": esubcommand,"objectclass": layername.encode('utf8'), "attribute" : attribute.('utf8'), "data": data , "scale": scale}}]}
                jdata = {"commands": [{"ecommand": "ZOOMTOFEATURESET",
                                       "config": {"esubcommand": esubcommand, "objectclass": layername,
                                                  "attribute": attribute, "data": data,
                                                  "scale": scale}}]}

            if debug:
                prefix = esubcommand + '.json'
                gtoObj.gtomain.remote.writeRemoteFile(jdata, prefix)
            gtoObj.gtomain.remote.writeRemoteFile(jdata)

    except  Exception as e:
        gtoObj.info.err(e)


def FindLayer(gtoObj, debug, *args, **kwargs):
    try:
        # init
        iface = gtoObj.iface
        qid = QInputDialog(iface.mainWindow())
        name, ok = QInputDialog.getText(qid, 'Layer name', 'Find:', QLineEdit.Normal)
        if ok:
            layers = QgsProject.instance().mapLayersByName(name)
            if layers:
                layer = layers[0]
                iface.setActiveLayer(layer)
                root = QgsProject.instance().layerTreeRoot()
                tlayer = root.findLayer(layer.id())
                group = tlayer.parent()
                while group is not None:
                    group.setExpanded(True)
                    group = group.parent()
                if len(layers) > 1:
                    gtoObj.info.msg("Found %i layers!" % len(layers))
            else:
                gtoObj.info.msg("No Layer found!")
    except  Exception as e:
        gtoObj.info.err(e)


def OpenFile(gtoObj, debug, *args, **kwargs):
    for f in args:
        try:
            gtoObj.info.log(f)
            if os.path.isfile(f):
                os.startfile(f)
            else:
                webbrowser.open(f)
        except Exception as e:
            gtoObj.info.msg(e.args)


def selectByMapExtent(gtoObj, debug, *args, **kwargs):
    try:
        iface = gtoObj.iface
        prj = QgsProject.instance()
        # layers = ['usr_punkt','usr_linie','polygon']
        ext = iface.mapCanvas().extent()
        crsPrj = prj.crs()
        p1 = QgsPointXY(ext.xMinimum(), ext.yMinimum())
        p2 = QgsPointXY(ext.xMaximum(), ext.yMaximum())
        rec = QgsRectangle(p1, p2)
        for lay in args:
            layer = QgsProject.instance().mapLayersByName(lay)[0]
            layer.selectByRect(rec)
    except Exception as e:
        gtoObj.info.err(e)


def showQueryBuilder(gtoObj, debug, *args, **kwargs):
    try:
        iface = gtoObj.iface
        info = gtoObj.info

        layer = iface.activeLayer()
        query_builder = QgsQueryBuilder(layer, iface.mainWindow())
        query_builder.show()
    except Exception as e:
        info.err(e)


def addToolBarBreakTop(gtoObj, debug, *args, **kwargs):
    try:
        iface = gtoObj.iface
        info = gtoObj.info
        iface.mainWindow().addToolBarBreak()  # default:  Qt::TopToolBarArea
    except Exception as e:
        info.err(e)


def addToolBarBreakBottom(gtoObj, debug, *args, **kwargs):
    try:
        iface = gtoObj.iface
        info = gtoObj.info
        iface.mainWindow().addToolBarBreak(Qt.BottomToolBarArea)  # default:  Qt::TopToolBarArea
    except Exception as e:
        info.err(e)
