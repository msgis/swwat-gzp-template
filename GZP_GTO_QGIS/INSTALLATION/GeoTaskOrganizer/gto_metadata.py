# -*- coding: utf-8 -*-

import os
import sys
import shutil
from PyQt5.QtCore import QSettings

from .gto_info import gtoInfo


class gtoMetadata(object):
    def __init__(self):
        # system
        self.path_plugin = os.path.dirname(__file__)
        self.info = gtoInfo(self)
        self.debug = self.info.debug

    def initProject(self, path_qgs):
        # project
        self.path_qgs = path_qgs
        self.path_gto = os.path.join(self.path_qgs, "gto")
        if os.path.isabs(self.path_gto):
            self.path_config = self.makePath(os.path.join(self.path_gto, "config"))
            self.path_tools = self.makePath(os.path.join(self.path_gto, "tools"))
            self.path_icons = self.makePath(os.path.join(self.path_gto, "icons"))
            self.path_printlayouts = self.makePath(os.path.join(self.path_gto, "layouts"))
            self.path_scripts = self.makePath(os.path.join(self.path_gto, "scripts"), True)
            self.path_forms = self.makePath(os.path.join(self.path_gto, "forms"), True)
            self.path_styles = self.makePath(os.path.join(self.path_gto, "styles"))
            self.path_pictures = self.makePath(os.path.join(self.path_gto, "pictures"))
            self.path_help = self.makePath(os.path.join(self.path_gto, "help"))
            # system
            UserAppDataMsGIS = self.makePath(os.path.join(os.environ.get('APPDATA'), 'ms.GIS'))
            self.path_userAppData = self.makePath(os.path.join(UserAppDataMsGIS, 'gto'))
            try:
                if not os.path.exists(UserAppDataMsGIS):
                    os.mkdir(UserAppDataMsGIS)
                if not os.path.exists(self.path_userAppData):
                    os.mkdir(self.path_userAppData)
            except:
                pass
            s = QSettings()
            s.setValue('UI/ComposerManager/templatePath', self.path_printlayouts)
            s.setValue("pythonConsole/lastDirPath", self.path_scripts)
            try:
                src = os.path.join(self.path_plugin, "gto_script.py")
                dest = os.path.join(self.path_scripts, "example.py")
                if not os.path.isfile(dest):
                    shutil.copyfile(src, dest)
            except:
                pass
            return True
        return False

    def makePath(self, path, register=False):
        try:
            if not os.path.exists(path):
                os.mkdir(path)
            if register and not path in sys.path:
                sys.path.append(path)
            return path
        except:
            pass

    def get_path_gto(self):
        return self.path_gto

    def get_path_config(self):
        return self.path_config

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

    def get_path_forms(self):
        return self.path_forms

    def get_path_styles(self):
        return self.path_styles

    def get_path_pictures(self):
        return self.path_pictures

    def get_path_help(self):
        return self.path_help

    def get_path_userAppData(self):
        return self.path_userAppData

    dirPlugin = property(get_path_plugin)
    dirConfig = property(get_path_config)
    dirGTO = property(get_path_gto)
    dirTools = property(get_path_tools)
    dirToolIcons = property(get_path_icons)
    dirPrintLayouts = property(get_path_printlayouts)
    dirScripts = property(get_path_scripts)
    dirForms = property(get_path_forms)
    dirStyles = property(get_path_styles)
    dirPictures=property(get_path_pictures)
    dirHelp=property(get_path_help)
    dirUserAppData = property(get_path_userAppData)
