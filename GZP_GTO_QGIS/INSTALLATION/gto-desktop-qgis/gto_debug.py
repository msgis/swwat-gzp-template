#!/usr/bin/python
# -*- coding: utf-8 -*-

from builtins import str
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import QToolBar,QAction,QDockWidget
from .gto_helper import *
from .gto_commands import *
from .gto_info import gtoInfo
import qgis
import os
import io
import json

class createDebugTB(QObject):
    def __init__(self,gtomain):
        super(createDebugTB,self).__init__()
        self.setObjectName(__name__)
        #references
        self.gtomain = gtomain
        self.info = gtoInfo(self)
        self.iface = gtomain.iface
        objName = "gtoTB_debug"
        caption = "GTO DEBUG"
        toolbar_style = Qt.ToolButtonTextOnly
        toolbar_dock = Qt.TopToolBarArea
        self.toolbar = None
        # load toolbar
        self.toolbar= findToolbar(self.iface, objName)
        if self.toolbar is None:
            self.toolbar = QToolBar()
            self.toolbar.setObjectName(objName)
            self.toolbar.setWindowTitle(caption)
            self.iface.addToolBar(self.toolbar, toolbar_dock)
        self.toolbar.clear()
        #add tools
        self.addAction(0,"TEST")
        self.addAction(1,'Std UI')
        self.addAction(2,'Python')
        self.addAction(3,'Log')
        self.addAction(4,'Find layer')
        self.addAction(5, 'Reload style')
        self.addAction(6, 'Reload tree')
        self.toolbar.setHidden(False)
        self.toolbar.setToolButtonStyle(toolbar_style)
        self.toolbar.setVisible(True)
        self.ShowMessageLog()

    def runcmd(self):
        try:
            self.info.log('runGTOdebugtool')
            caller = self.sender()
            action = caller.objectName()
            self.info.log(action)
            if action == 'mActionGTOdebug0':
                self.test()
            elif  action == 'mActionGTOdebug1':
                SetStandardUI(self,True)
                self.toolbar.setVisible(True)
                self.ShowMessageLog()
            elif action == 'mActionGTOdebug2':
                qgis.utils.iface.actionShowPythonDialog().trigger()
            elif action == 'mActionGTOdebug3':
                self.ShowMessageLog()
            elif action == 'mActionGTOdebug4':
                FindLayer(self,True)
            elif action == 'mActionGTOdebug5':
                self.gtomain.loadstyle()
            elif action == 'mActionGTOdebug6':
                if os.path.isfile(self.gtomain.path_metadata + "/tree.json"):
                    f = io.open(self.gtomain.path_metadata + "/tree.json", encoding='utf-8')
                    data = json.load(f)
                    f.close()
                    if os.path.isfile(self.gtomain.path_metadata + "/tree_style.json"):
                        f = io.open(self.gtomain.path_metadata + "/tree_style.json", encoding='utf-8')
                        style = json.load(f)
                        f.close()
                        if self.gtomain.gtotb is not None:
                            self.gtomain.gtotb.clear()
                        self.gtomain.tree.clear()
                        self.gtomain.buildtree(None, data,-1,style)
            else:
                self.info.log('UNKNOWN TOOL')
        except Exception as e:
            self.info.err(e)

    def addAction(self,id,caption):
        action = QAction(self.gtomain)
        action.setText(caption)
        action.setObjectName('mActionGTOdebug' + str(id))
        action.triggered.connect(self.runcmd)
        self.toolbar.addAction(action)
        self.toolbar.addSeparator()

    def ShowMessageLog(self):
        try:
            # qgis.utils.iface.actionShowPythonDialog().trigger()
            # pdw = self.iface.mainWindow().findChild(QDockWidget, 'PythonConsole')
            # if not pdw.isVisible():
            #     pdw.setVisible(True)
            mdw = self.iface.mainWindow().findChild(QDockWidget, 'MessageLog')
            mdw.setAllowedAreas(Qt.BottomDockWidgetArea)
            mdw.setFloating(False)
            mdw.setVisible(True)
            mdw.show()
            # gto_commands.TabWidget(self,self.debug,[mdw,pdw])
        except Exception as e:
            self.info.err(e)

    def test(self):
        try:
            from PIL import ImageGrab
            import cv2
            import numpy as np

            img = ImageGrab.grab(bbox=(2000,500,2200,700))
            imp_np = np.array(img)
            frame =cv2.cvtColor(imp_np,cv2.COLOR_BGR2RGB)
            cv2.imshow("Screen", frame)
            #cv2.moveWindow("Screen")
            cv2.waitkey(0)
            cv2.destroyAllWindows()
            # layer = self.iface.activeLayer()
            # uri = layer.dataProvider().dataSourceUri()
            # uri = uri[uri.find("table="):]
            # uri = uri.split("=")
            # uri = uri[1]
            # uri = uri.split('"')
            # uri = uri[1]

            import time
            ts = time.gmtime()
            uri=time.strftime("%Y%m%d#%H%M%S", ts)
            # 2018-05-11 19:58:44
            self.info.msg(str(uri))

            #self.info.msg(layer.dataProvider().uri().table())
        except Exception as e:
            self.info.err(e)

