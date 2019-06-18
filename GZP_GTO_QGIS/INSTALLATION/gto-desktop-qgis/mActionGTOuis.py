#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5.QtGui import *
from PyQt5.QtWidgets import QToolBar,QDockWidget

def run(id, gtotool, config, debug):
    try:
        #read config
        toolbars_hideall = config['toolbars_hideall']
        toolbars = config['toolbars']
        menus_hideall = config['menus_hideall']
        menus= config['menus']
        panels_hideall = config['panels_hideall']
        panels = config['panels']
        showstatusbar=True
        try:
            showstatusbar = config['showstatusbar']
        except:
            pass
        #references
        info = gtotool.info
        iface = gtotool.iface

        #toolbars
        qtoolbars = iface.mainWindow().findChildren(QToolBar)
        for toolbar in qtoolbars:
            objName = toolbar.objectName()
            if debug: info.log("toolbar:", objName)
            if objName in toolbars:
                toolbar.setHidden(False)
            else:
                if toolbars_hideall and objName !='mGTOtoolbar': toolbar.setHidden(True)
        #panels
        qpanels = iface.mainWindow().findChildren(QDockWidget)
        for panel in qpanels:
            objName = panel.objectName()
            if debug: info.log("panel:",objName)
            if objName in panels:
                panel.setHidden(False)
            else:
                if panels_hideall and objName != 'GTODockWidgetBase': panel.setHidden(True)
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
        gtotool.info.gtoWarning(e.args)

