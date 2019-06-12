#!/usr/bin/python
# -*- coding: utf-8 -*-

from builtins import str
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QAction

import os.path
import json
import io
from .gto_info import gtoInfo
from .gto_tool import gtoTool
import webbrowser
from .gto_touchZoom import TouchZoom
#from .gto_helper import *

class gtoTools(QObject):
    def __init__(self,gtomain):
        super(gtoTools,self).__init__()
        self.setObjectName(__name__)
        #references
        self.gtomain = gtomain
        self.iface = gtomain.iface
        self.info = gtoInfo(self)
        self.debug = gtomain.debug

        #default action
        self.defaultAction = QAction('GeoTaskOrganizer@ms.gis',self)
        self.defaultAction.setObjectName('mActionGTOmsgis')
        self.defaultAction.setIcon(QIcon(self.gtomain.gtoplugin.plugin_dir + "/icon.png"))
        self.defaultAction.triggered.connect(self.runGTOdefault)
        self.TouchZoom =QAction('TouchZoom')
        self.TouchZoom.setObjectName('mActionGTOtouchZoom')
        self.TouchZoom.triggered.connect(self.runTouchZoom)

    def getGTOaction(self, path):
        try:
            if self.debug: self.info.log('getGTOaction')
            gtoactions = []
            gtoactions.append(self.defaultAction)
            gtoactions.append(self.TouchZoom)
            for f in os.listdir(path):
                if f.lower().endswith(".json"):
                    actionname = f.replace('.json','')
                    ext = f.split(".")[-1]
                    if ext.lower() == "json":
                        data = None
                        # read data
                        try:
                            filename = os.path.join(path,f)
                            f = io.open(filename, encoding='utf-8')
                            data = json.load(f)
                            f.close()
                        except:
                            if self.debug: self.info.log(filename,"not found!")
                        if data is not None:# build actions
                            for tool in data['tools']:
                                caption = tool['caption']
                                config = tool['config']
                                icontext = tool['icontext']
                                statustip = tool['statustip']
                                tooltip = tool['tooltip']
                                whatsthis = tool['whatsthis']
                                visible = True
                                try:
                                   visible = tool['visible']
                                except:
                                    pass
                                id = tool['id']
                                icon = None
                                try:
                                    icon = tool['icon']
                                except:
                                    pass
                                action = QAction(caption, self)

                                objname = actionname + str(id)
                                action.setObjectName(objname)
                                # visible:
                                action.setVisible(visible)
                                # icon
                                if icon is None or icon == '':
                                    icon = actionname.lower() + ".png"
                                iconfile = os.path.join(self.gtomain.path_icons, icon)
                                if os.path.exists(iconfile):
                                    action.setIcon(QIcon(iconfile))
                                if icontext is None: icontext = ' '
                                action.setIconText(icontext)

                                if statustip is not None:  action.setStatusTip(statustip)
                                if whatsthis is not None:  action.setWhatsThis(whatsthis)
                                if tooltip is not None:  action.setToolTip(tooltip)

                                #action.setData(config)
                                action.triggered.connect(self.rungtotool)
                                gtoactions.append(action)
            return gtoactions
        except Exception as e:
            self.info.err(e)

    def rungtotool(self):
        if self.debug: self.info.log('runGTOtool')
        caller = self.sender()
        try:
            if self.debug: self.info.log('rungtotool::import module')
            module_name=self.gtomain.helper.getName(caller.objectName())
            if self.debug: self.info.log('runGTOtool',module_name)
            if module_name == "":
                pass
            else:
                obj = gtoTool(self.gtomain, module_name)
                if obj is not None:
                    if self.debug: self.info.log('runGTOtool:','trigger')
                    obj.triggered(caller)
        except Exception as  e:
            self.info.err(e)

    def runGTOdefault(self):
        try:
            if self.debug:
                webbrowser.open('http://msgis.com/')
            else:
                webbrowser.open('http://msgis.com/')
        except Exception as e:
            self.info.err(e)

    def runTouchZoom(self):
        try:
            self.iface.mapCanvas().setMapTool(TouchZoom(self.iface.mapCanvas(),self.gtomain))
        except Exception as e:
            self.info.err(e)