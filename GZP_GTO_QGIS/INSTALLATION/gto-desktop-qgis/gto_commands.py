#!/usr/bin/python
# -*- coding: utf-8 -*-

from builtins import str
from PyQt5.QtWidgets import QMessageBox, QDockWidget, QPlainTextEdit, QStackedWidget, QToolBar, QInputDialog, QLineEdit
from qgis.core import QgsProject, QgsDataSourceUri,QgsRectangle

import os
import io

def gto_test(gtoTool,debug,*args,**kwargs):
    info=gtoTool.info
    #info.log(type(gtoObj))
    info.msg("TESTCOMMAND!")
    info.log("parameters =",args)
    info.log("settings =", kwargs)
    #=======================
    #gtoTool.gtomain.runcmd('mActionGTOcomposer2')
    LoadMapSettings(gtoTool,True)
    SaveMapSettings(gtoTool,True)


def SaveMapSettings(gtoTool, debug, *args,**kwargs):
    try:
        import json
        iface = gtoTool.iface
        info = gtoTool.info
        dirSettings = os.path.join(gtoTool.metadata.dirAppData,'mapsettings')
        if debug: info.log ('Pfad',dirSettings)
        if not os.path.exists(dirSettings):
            os.mkdir(dirSettings)
        file = os.path.basename(QgsProject.instance().fileName())
        file = os.path.join (dirSettings, file + '.json')
        #get layer visibility
        layers_data ={}
        prj = QgsProject.instance()
        for layer in prj.layerTreeRoot().findLayers():#QgsLayerTreeLayer
            if not layer.name() in layers_data:
                layers_data[layer.name()] = layer.itemVisibilityChecked()
        #get group visibilty
        groups_data ={}
        # get group visibility
        for group in prj.layerTreeRoot().findGroups():#QgsLayerTreeGroup
            if not group.name() in groups_data:
                groups_data[group.name()] = group.itemVisibilityChecked()
            getGroups(group,groups_data)

        #map extent
        rec = iface.mapCanvas().extent()  # QgsRectangle
        mapextent = (rec.xMinimum(), rec.yMinimum(), rec.xMaximum(), rec.yMaximum())
        #save metadata
        jdata = {'Extent':mapextent,'Layers': layers_data,'Groups':groups_data}
        with open(file, 'w', encoding='utf8') as outfile:
            sort = True
            json.dump(jdata, outfile, ensure_ascii=False, sort_keys=sort, indent=4)

    except Exception as e:
        info.err(e)

def getGroups(ParentNode,groups_data):
    for node in ParentNode.children ():#QgsLayerTreeNode
        if node.nodeType() == 0:#is group
            if not node.name() in groups_data:
                groups_data[node.name()] = node.itemVisibilityChecked()
            getGroups(node,groups_data)

def LoadMapSettings(gtoTool, debug, *args,**kwargs):
    try:
        import json
        iface = gtoTool.iface
        info = gtoTool.info
        dirSettings = os.path.join(gtoTool.metadata.dirAppData,'mapsettings')
        file = os.path.basename(QgsProject.instance().fileName())
        file = os.path.join (dirSettings, file + '.json')

        #read metadata
        jdata =None
        with open(file, 'r', encoding='utf8') as infile:
            jdata = json.load(infile)

        layer_data = jdata.get('Layers',{})
        group_data =jdata.get('Groups',{})
        mapextent = jdata.get('Extent',[])

        #set the map
        prj = QgsProject.instance()
        #layers
        for key in layer_data:
            try:
                layer = prj.mapLayersByName(key)[0]
                visible = layer_data[key]
                prj.layerTreeRoot().findLayer(layer.id()).setItemVisibilityChecked(visible)
            except Exception as e:
                if debug: info.err(e)
        #groups
        for key in group_data:
            visible = group_data[key]
            prj.layerTreeRoot().findGroup(key).setItemVisibilityChecked(visible)
        #extent
        rec = QgsRectangle(mapextent[0], mapextent[1], mapextent[2], mapextent[3])
        iface.mapCanvas().setExtent(rec)
        iface.mapCanvas().refresh()
    except Exception as e:
        info.err(e)

def ShowAttributeTableSelectedFeatures(gtoObj, debug, *args,**kwargs):
    expr = ''
    iface = gtoObj.iface
    layers = QgsProject.instance().mapLayersByName(kwargs['layer'])
    legend = iface.legendInterface()
    if layers:
        layer = layers[0]  # duplicte names => take the first
        provider = layer.dataProvider()
        uri = QgsDataSourceUri(provider.dataSourceUri())
        ID_name = uri.keyColumn()
        if ID_name == '': ID_name = 'ID'
        for id in layer.selectedFeaturesIds():
            expr = expr + '%i,' % id
        expr = '"%s"' % ID_name + ' IN (' + expr[:-1] + ')'
        gtoObj.iface.showAttributeTable(layer, expr)

def TabWidget(gtoObj, debug, *args,**kwargs):
    iface = gtoObj.iface
    parent=args[0]
    if isinstance(parent,str):
        parent =  iface.mainWindow().findChild(QDockWidget,parent)
    if isinstance(parent, QDockWidget):
        if not parent.isFloating():
            dockstate = iface.mainWindow().dockWidgetArea(parent)
            dws = iface.mainWindow().findChildren(QDockWidget)
            for d in dws:
                if d is not parent:
                    if iface.mainWindow().dockWidgetArea(d) == dockstate and d.isHidden() == False:
                        iface.mainWindow().tabifyDockWidget(parent, d)
            parent.raise_()

def TabPanels(gtoObj, debug, *args,**kwargs):
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

def ClosePanel(gtoObj, debug, *args,**kwargs):
    iface = gtoObj.iface
    dws =  iface.mainWindow().findChildren(QDockWidget)
    objname= args[0]
    for d in dws:
        if objname == d.objectName():
            d.close()

def WriteActions(gtoObj, debug, *args,**kwargs):
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
        if QMessageBox.question(iface.mainWindow(), 'Datei', 'Datei \n%s\nextistiert.\n' % path + u'Überschreiben?', QMessageBox.Yes | QMessageBox.No) == QMessageBox.No:
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

def ClearMessageLog(gtoObj, debug, *args,**kwargs):
    iface = gtoObj.iface
    panelName = args[0]
    msgQDW = iface.mainWindow().findChild(QDockWidget, 'MessageLog')
    stackW =  msgQDW.findChild(QStackedWidget,'qt_tabwidget_stackedwidget')
    for c in stackW.children():
        if isinstance(c, QPlainTextEdit):
            if c.toPlainText().find('gto_plugin'):
                c.clear()

def SetStandardUI(gtoObj, debug, *args,**kwargs):
    try:
        #QSettings().setValue('/UI/Customization/enabled', False)
        #QSettings("QGIS", "QGIS2").remove("/UI/state")
        #QSettings("QGIS", "QGIS2").remove("/ComposerUI/state")
        #caller.gtomain.runcmd("mActionExit")

        #read config
        toolbars = ["mFileToolBar","mLayerToolBar","mDigitizeToolBar","mMapNavToolBar","mAttributesToolBar","mPluginToolBar","mHelpToolBar","mLabelToolBar","mVectorToolBar","mWebToolBar","mBookmarkToolbar","mBrowserToolbar"]
        panels = ["Layers","Browser"]#""LayerOrder"]
        menus = ["mProjectMenu","mEditMenu","mViewMenu","mLayerMenu","mSettingsMenu","mPluginMenu","mVectorMenu","mRasterMenu","mDatabaseMenu","mWebMenu","processing","mHelpMenu"]

        #references
        info = gtoObj.info
        iface = gtoObj.iface

        #toolbars
        qtoolbars = iface.mainWindow().findChildren(QToolBar)
        for toolbar in qtoolbars:
            toolbar.setHidden(True)
            objName = toolbar.objectName()
            if debug: info.log("toolbar:", objName)
            if objName in toolbars or len(toolbars) == 0: toolbar.setHidden(False)

        #panels
        qpanels = iface.mainWindow().findChildren(QDockWidget)
        for panel in qpanels:
            objName = panel.objectName()
            if debug: info.log("panel:", objName)
            if objName != 'GTODockWidgetBase': panel.setHidden(True)
            if objName in panels or len(panels) == 0: panel.setHidden(False)

        #menus
        qmenubar = iface.mainWindow().menuBar()
        for action in qmenubar.actions():
            action.setVisible(False)
            objName= action.menu().objectName()
            if debug: info.log("menu:", objName)
            if objName in menus or len(menus) == 0: action.setVisible(True)
        # statusbar
        iface.mainWindow().statusBar().setHidden(False)
    except Exception as e:
        gtoObj.info.gtoWarning(e.args)


def wSetSelectSet(gtoObj, debug, *args,**kwargs):
    try:

        if gtoObj.gtomain.settings is not None:

            esubcommand = kwargs['esubcommand']
            layername = kwargs['objectclass']
            where = kwargs.get('whereclause')
            attribute = kwargs.get('attribute')

            iface = gtoObj.iface
            jdata ={}
            data = None

            if esubcommand =="SETSELECTSET_WHERECLAUSE":
                #jdata = {"commands": [{"ecommand": "SETSELECTSET","config": {"esubcommand": esubcommand, "objectclass": layername.encode('utf8'),"whereclause": where.('utf8')}}]}
                jdata = {"commands": [{"ecommand": "SETSELECTSET",
                                       "config": {"esubcommand": esubcommand, "objectclass": layername,
                                                  "whereclause": where}}]}
            elif esubcommand == "SETSELECTSET_ID":
                layers = QgsProject.instance().mapLayersByName(layername)
                legend = iface.layerTreeView()
                if layers:
                    layer = layers[0]  # duplicte names => take the first
                    if debug: gtoObj.info.log(type(layername))
                    #legend.setLayerVisible(layer, True)
                    #iface.legendInterface().setCurrentLayer(layer)
                    iface.setActiveLayer(layer)
                    data = gtoObj.gtomain.remote.getSelectedFeatures(gtoObj,debug,layer,attribute)
                #jdata = {"commands": [{"ecommand": "SETSELECTSET","config": {"esubcommand": esubcommand, "objectclass": layername.('utf8'),"attribute": attribute.encode('utf8'), "data": data}}]}
                jdata = {"commands": [{"ecommand": "SETSELECTSET",
                                       "config": {"esubcommand": esubcommand, "objectclass": layername,
                                                  "attribute": attribute, "data": data}}]}
            if debug:
                prefix =  esubcommand + '.json'
                gtoObj.gtomain.remote.writeRemoteFile(jdata, prefix)
            gtoObj.gtomain.remote.writeRemoteFile(jdata)

    except  Exception as e:
        gtoObj.info.err(e)


def wZoomToFeatureSet(gtoObj, debug, *args,**kwargs):
    try:

        if gtoObj.gtomain.settings is not None:
            iface = gtoObj.iface
            jdata = {}

            esubcommand = kwargs['esubcommand']
            layername = kwargs['objectclass']
            attribute = kwargs.get('attribute')
            where = kwargs.get('whereclause')
            scale = kwargs.get('scale',0)

            if debug: gtoObj.info.log(esubcommand,layername, attribute,scale)

            if esubcommand == 'ZOOMTOFEATURESET_WHERECLAUSE':
                #jdata = {"commands": [{"ecommand": "ZOOMTOFEATURESET","config": {"esubcommand": esubcommand, "objectclass": layername.encode('utf8'),"whereclause": where.encode('utf8'), "scale": scale}}]}
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
                #jdata={"commands":[{"ecommand": "ZOOMTOFEATURESET", "config": {"esubcommand": esubcommand,"objectclass": layername.encode('utf8'), "attribute" : attribute.('utf8'), "data": data , "scale": scale}}]}
                jdata = {"commands": [{"ecommand": "ZOOMTOFEATURESET",
                                       "config": {"esubcommand": esubcommand, "objectclass": layername,
                                                  "attribute": attribute, "data": data,
                                                  "scale": scale}}]}

            if debug:
                prefix =  esubcommand + '.json'
                gtoObj.gtomain.remote.writeRemoteFile(jdata, prefix)
            gtoObj.gtomain.remote.writeRemoteFile(jdata)

    except  Exception as e:
        gtoObj.info.gtoWarning(e.args)

def FindLayer(gtoObj, debug, *args,**kwargs):
    try:
        #init
        iface=  gtoObj.iface
        qid = QInputDialog()
        name, ok = QInputDialog.getText(qid,'Layer name','Find:',QLineEdit.Normal)
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
                    group =  group.parent()
                if len(layers) > 1:
                    gtoObj.info.msg("Found %i layers!" % len(layers))
            else:
                gtoObj.info.msg("No Layer found!")
    except  Exception as e:
        gtoObj.info.gtoWarning(e.args)

def OpenFile(gtoObj, debug, *args,**kwargs):
    for f in args:
        try:
            gtoObj.info.log(f)
            if os.path.isfile(f): os.startfile(f)
        except Exception as e:
            gtoObj.info.msg(e.args)
