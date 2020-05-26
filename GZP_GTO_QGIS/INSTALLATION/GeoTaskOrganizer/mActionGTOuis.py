#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5.QtGui import *
from PyQt5.QtWidgets import QToolBar,QDockWidget

def run(id, gtotool, config, debug):
    try:
        #read config
        toolbars_hideall = config.get('toolbars_hideall',False)
        toolbars = config.get('toolbars',[])
        menus_hideall = config.get('menus_hideall',False)
        menus= config.get('menus',[])
        panels_hideall = config.get('panels_hideall',False)
        panels = config.get('panels',[])
        showstatusbar=True
        try:
            showstatusbar = config.get('showstatusbar',True)
        except:
            pass
        #references
        info = gtotool.info
        iface = gtotool.iface

        #toolbars
        qtoolbars = iface.mainWindow().findChildren(QToolBar)
        for toolbar in qtoolbars:
            objName = toolbar.objectName()
            if debug: info.log("toolbar:", objName,"title:",toolbar.windowTitle())
            if objName in toolbars:
                toolbar.setHidden(False)
            else:
                if toolbars_hideall and objName !='mGTOtoolbar': toolbar.setHidden(True)

            if objName == 'gtoTB_debug': toolbar.setHidden(False)
        #panels
        qpanels = iface.mainWindow().findChildren(QDockWidget)
        for panel in qpanels:
            objName = panel.objectName()
            if debug: info.log("panel:",objName)
            if objName in panels:
                panel.setHidden(False)
            else:
                if panels_hideall and objName != 'GTODockWidget': panel.setHidden(True)
            #restor toolbars in panels
            toolbars = panel.findChildren(QToolBar)
            for t in toolbars:
                t.setHidden(False)
                if debug: info.log("toolbar restored:",  t.objectName())
        #menus
        qmenubar = iface.mainWindow().menuBar()
        for action in qmenubar.actions():
            objName= action.menu().objectName()
            if debug: info.log("menu:",objName)
            if objName in menus:
                action.setVisible(True)
            else:
                if menus_hideall: action.setVisible(False)
        #statusbar
        iface.mainWindow().statusBar().setHidden(not showstatusbar)
    except Exception as e:
        gtotool.info.err(e)

