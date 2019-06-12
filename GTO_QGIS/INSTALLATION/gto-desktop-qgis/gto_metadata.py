# -*- coding: utf-8 -*-

from builtins import object
import os
from PyQt5.QtCore import QSettings

class gtoMetadata(object):
    def __init__(self,plugindir, ):
        #system
        self.path_plugin = plugindir
        self.debug = os.path.exists(os.path.join(self.path_plugin, "debug.gto"))#platform indepentend
        self.logfile = os.environ.get('APPDATA') + '/QGIS/QGIS3/gtoError.log'#c:\Users\guenter\AppData\Roaming\QGIS\QGIS3\
        if os.path.isfile(self.logfile) and os.path.getsize(self.logfile)>10123456:
            bakfile = self.logfile + ".bak"
            if os.path.isfile(bakfile): os.remove(bakfile)
            os.rename(self.logfile,bakfile)

    def initProject(self, path_qgs):
        #project
        self.path_qgs = path_qgs
        self.path_gto = self.path_qgs + "/gto"
        self.path_metadata = self.path_gto + "/config"
        self.path_tools = self.path_gto + "/tools"
        self.path_icons = self.path_gto + "/icons"
        self.path_printlayouts = self.path_gto + "/layouts"
        self.path_scripts = self.path_gto + "/scripts"
        AppDataMsGIS = os.path.join(os.environ.get('APPDATA') ,'ms.GIS')
        self.path_appdata =os.path.join(AppDataMsGIS,'gto')
        try:
            if not os.path.exists (AppDataMsGIS):
                os.mkdir(AppDataMsGIS)
            if not os.path.exists(self.path_appdata):
                os.mkdir(self.path_appdata)
        except:
            pass
        s = QSettings()
        s.setValue('UI/ComposerManager/templatePath',  self.path_printlayouts)

    def get_path_gto(self):
        return self.path_gto

    def get_path_metadata(self) :
        return self.path_metadata

    def get_path_tools(self):
        return self.path_tools

    def get_path_icons(self):
        return self.path_icons

    def get_path_printlayouts(self):
        return self.path_printlayouts

    def get_path_plugin(self):
        return self.path_plugin

    def get_path_scripts(self):
        return self.path_scripts

    def get_path_appdata(self):
        return self.path_appdata

    dirPlugin = property(get_path_plugin)
    dirMetadata = property(get_path_metadata)
    dirGTO = property(get_path_gto)
    dirTools = property(get_path_tools)
    dirToolIcons = property(get_path_icons)
    dirPrintLayouts =property(get_path_printlayouts)
    dirScripts = property(get_path_scripts)
    dirAppData = property(get_path_appdata)