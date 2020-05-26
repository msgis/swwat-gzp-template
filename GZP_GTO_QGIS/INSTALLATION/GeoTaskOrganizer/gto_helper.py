# -*- coding: utf-8 -*-

from __future__ import print_function

import os
from builtins import str

from PyQt5.QtCore import Qt, QObject, QTimer, QSettings
from PyQt5.QtGui import QIcon, QColor, QContextMenuEvent, QMouseEvent, QFocusEvent
from PyQt5.QtWidgets import QApplication, QAction, QWidget, QToolButton, QMenu, QLabel, QSizePolicy, QToolBar, \
    QComboBox, QPushButton

from qgis.core import QgsPointXY
from qgis.gui import QgsHighlight, QgsVertexMarker

from .gto_info import gtoInfo
from .gto_widgets import *
from .gto_tools import gtoAction, gtoWidgetAction

import importlib.util
import sys
import time
import win32clipboard
import json


class gtoHelper(QObject):
    def __init__(self, gtomain):
        super(gtoHelper, self).__init__()
        self.setObjectName(__name__)
        self.gtomain = gtomain
        self.iface = self.gtomain.iface
        self.metadata = self.gtomain.metadata
        self.info = gtoInfo(self)
        self.debug = self.gtomain.gtoplugin.debug

    def getName(self, value):
        try:
            result = []
            for c in value:
                if not c.isdigit():
                    result.append(c)
            return ''.join(result)
        except Exception as e:
            return ''

    def checkFileExists(self, file, ordner=None):
        try:
            if os.path.isfile(file):
                return file
            if ordner is not None:
                file = os.path.join(ordner, file)
                file = os.path.abspath(file)
                if os.path.isfile(file):
                    return file
        except Exception as e:
            return None

    def getFilePath(self, filepath, createPath=False):
        try:
            filepath = filepath.replace('%APPDATA%', os.environ.get('APPDATA'))
            filedir = os.path.dirname(filepath)
            filedir = os.path.abspath(filedir)
            if createPath and not os.path.exists(filedir):
                os.makedirs(filedir)
            return filepath
        except Exception as e:
            return 'getFilePath' + e.args[0]

    def getTableName(self, layer):
        try:
            uri = layer.dataProvider().dataSourceUri()
            start = uri.find("table=")
            if start == -1:
                start = uri.find("tablename=")
            if start == -1:
                start = uri.find("layername=")
            part = uri[start:-1]
            end = part.find("|")
            if end == -1:
                end = part.find(" ")
            tablename = part[:end]
            val = tablename.split("=")
            tablename = val[1].strip()
            return tablename
        except Exception as e:
            self.info.err(e)

    def timestamp(self, ):
        try:
            ts = time.gmtime()
            return str(time.strftime("%Y%m%d#%H%M%S", ts))

        except Exception as e:
            self.info.err(e)

    def importModule(self, modulename, filepath=None):
        module = None
        if filepath is None: filepath = os.path.dirname(__file__)
        if self.debug: self.info.log("try to import:", modulename, 'from', self.shortDisplayText(filepath))
        try:
            if modulename in sys.modules:
                module = sys.modules[modulename]
                if self.debug: self.info.log("sys.modules:", module.__name__)
                return module
        except Exception as e:
            if self.debug: self.info.err(e)
        try:
            if filepath == os.path.dirname(__file__):  # gto, not working with external pathes
                package_module = os.path.basename(filepath) + "." + modulename
                module = __import__(package_module)  # python path or assumed sys.path.append(plugin_dir)
                # self.info.log(sys.modules)
                if self.debug: self.info.log("package__import__:", sys.modules[package_module].__name__)
                return sys.modules[package_module]
        except Exception as e:
            if self.debug: self.info.err(e)
        try:
            module = __import__(modulename)  # python path or assumed sys.path.append(plugin_dir)
            if self.debug: self.info.log("__import__:", module.__name__)
            return module
        except Exception as e:
            if self.debug: self.info.err(e)
        try:
            spec = importlib.util.spec_from_file_location(modulename, filepath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            # Optional; only necessary if you want to be able to import the module
            # by name later.
            sys.modules[modulename] = module
            if self.debug: self.info.log("SUCCESS:", "importlib:", module.__name__)
            return module
        except Exception as e:
            if self.debug: self.info.err(e)
        return module

    def shortDisplayText(self, text, length=45):
        x = text
        try:
            if len(x) > (2 * length):
                x = text[:length] + "..." + text[len(text) - length:]
        except:
            pass
        return x

    def getIcon(self, iconname, default='icon.png'):
        try:
            dir_icons = os.path.join(self.metadata.path_plugin, "icons")
            icon = os.path.join(dir_icons, iconname)
            # self.info.log("icon", icon)
            if not os.path.isfile(icon):
                icon = os.path.join(dir_icons, iconname.split('.')[0] + '.png')
                # self.info.log("icon", icon)
                if not os.path.isfile(icon):
                    icon = os.path.join(dir_icons, iconname.split('.')[0] + '.svg')
                    # self.info.log("icon", icon)
            if os.path.isfile(icon):
                return QIcon(icon)
            icon_default = os.path.join(self.metadata.path_plugin, default)
            if self.debug: self.info.log("icon not found:", icon)
            return QIcon(icon_default)
        except Exception as e:
            self.info.err(e)

    def copyToClipboard(self, text):
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(text, win32clipboard.CF_TEXT)
            win32clipboard.CloseClipboard()
        except Exception as e:
            self.info.err(e)

    def writeText(self, file, text):
        try:
            if not os.path.exists(file):
                with open(file, 'w', encoding='utf8') as f:
                    f.write(text)
        except Exception as e:
            if self.debug: self.info.log("gto_helper:writeText:", file, " text:", text)
            self.info.err(e)

    def writeHTML(self, file, text):
        try:
            html = '<!DOCTYPE html><html><head>\n'
            html = html + '<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">\n'
            html = html + '</head><body>\n'
            html = html + text.replace("\n", "<br>\n")
            html = html + '\n</body></html>'
            self.writeText(file, html)
        except Exception as e:
            self.info.err(e)

    def readJson(self, jfile):
        try:
            if os.path.isfile(jfile):
                with open(jfile, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if self.debug: self.info.log("readJson:", jfile)
                return data
        except Exception as e:
            self.info.err(e)

    def writeJson(self, file, data):
        try:
            if not os.path.exists(file):
                with open(file, 'w', encoding='utf8') as f:
                    json.dump(data, f, ensure_ascii=False, sort_keys=True, indent=4)
        except Exception as e:
            self.info.err(e)

    def openApp(self, app, *args):
        try:
            import subprocess
            subprocess.call(app, args)
        except Exception as e:
            self.info.err(e)

    def markFeature(self, lay, feat):
        try:
            color = QColor(Qt.red)
            highlight = QgsHighlight(self.iface.mapCanvas(), feat, lay)
            highlight.setColor(color)
            color.setAlpha(50)
            highlight.setFillColor(color)
            highlight.show()
            return highlight
        except Exception as e:
            self.info.err(e)

    def markVertexPoint(self, point, color=Qt.red):
        return self.markVertex(point.x(), point.y(), color)

    def markVertex(self, x, y, color=Qt.red):
        try:
            #self.info.err(None,"markVertex",self.sender().objectName())
            marker = QgsVertexMarker(self.iface.mapCanvas())
            marker.setCenter(QgsPointXY(x, y))
            marker.setColor(color)
            marker.setIconSize(7)
            marker.setIconType(
                QgsVertexMarker.ICON_BOX)  # See the enum IconType from http://www.qgis.org/api/classQgsVertexMarker.html
            marker.setPenWidth(3)
            marker.show()
            return marker
        except Exception as e:
            self.info.err(e)

    def getGTOversion(self):
        return self.gtomain.gtoplugin.get_version()

    def splitStringNummeric(self, text):
        try:
            puretext = ''
            number = ''
            for c in text:
                if c.isdigit():
                    number = number + c
                else:
                    puretext = puretext + c
            return puretext, number
        except Exception as e:
            self.info.err(e)

    def addToolbarClose(self, toolbar):
        try:
            if self.findChild(QAction, 'dummy') is None:
                dummy = QAction()
                dummy.setObjectName('dummy')
                toolbar.addAction(dummy)
                spacer = QWidget()
                spacer.setObjectName('spacer')
                spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                spacer.setStyleSheet("QWidget{background: transparent;}")
                toolbar.addWidget(spacer)
                toolbar.addAction(toolbar.toggleViewAction())
                return toolbar.toggleViewAction()
        except Exception as e:
            self.info.err(e)

    def findToolbar(self, iface, objName):
        return self.iface.mainWindow().findChild(QToolBar, objName)

    def getToolBar(self, gtoObj, objName, title, parent=None):
        try:
            toolbar = self.iface.mainWindow().findChild(QToolBar, objName)
            if toolbar is None and title is not None:
                toolbar = GtoToolbar(gtoObj, objName, title, parent)
            return toolbar
        except Exception as e:
            self.info.err(e)

    def addTools(self, widget, tools, parent=None):
        try:
            if tools is not None:
                for tool in tools:
                    self.addAction(widget, tool, parent)
        except Exception as e:
            self.info.err(e)

    def addAction(self, widget, actionNameOrList, parent=None):
        try:
            if isinstance(actionNameOrList, str):
                tname = actionNameOrList.lower()
                if tname == "separator" or tname == 'seperator' or tname == "|":
                    widget.addSeparator()
                else:
                    action = self.gtomain.findAction(actionNameOrList)
                    if action is not None:
                        if isinstance(action, gtoWidgetAction) or isinstance(action, gtoAction):
                            if self.debug: self.info.log("addAction:gtoWidgetAction", action.objectName())
                            widget.addAction(action)
                            action.added(widget)
                            tooldata = action.data()  # gtoTool-data
                            checked = tooldata.get("checked", False)  # if true, run action e.g mActionGTOfilter
                            if checked:
                                if self.debug: self.info.dl("addAction:gtoWidgetAction", action.objectName())
                                action.setCheckable(True)
                                action.setChecked(checked)
                                action.trigger()
                        else:
                            widget.addAction(action)
                    else:
                        widget.addWidget(QLabel(actionNameOrList))
            elif isinstance(actionNameOrList, list):
                tb = self.createToolButton(actionNameOrList, self.iface.mainWindow())
                if tb is not None:
                    widget.addWidget(tb)
        except Exception as e:
            self.info.err(e)

    def createToolButton(self, actionNamesList, parent=None):
        try:
            if len(actionNamesList) == 0: return
            if actionNamesList[0].lower() == 'combo:':
                del actionNamesList[0]
                return GtoToolCombo(self.gtomain, actionNamesList, None)
            menu = QMenu(parent)
            for an in actionNamesList:
                self.addAction(menu, an, parent)
                actions = [a for a in menu.actions()]
            tb = QToolButton()
            tb.setDefaultAction(actions[0])
            tb.setMenu(menu)
            tb.setPopupMode(QToolButton.MenuButtonPopup)
            menu.triggered.connect(tb.setDefaultAction)
            return tb
        except Exception as e:
            self.info.err(e)

    def setSetting(self, key, value):
        try:
            settings = QSettings()
            prefix = 'GeoTaskOrganizer/' + self.gtomain.gto_name + "/"
            key = prefix + key
            settings.setValue(key, value)
        except Exception as e:
            self.info.err(e)

    def getSetting(self, key, default=None):
        try:
            settings = QSettings()
            prefix = 'GeoTaskOrganizer/' + self.gtomain.gto_name + "/"
            key = prefix + key
            return settings.value(key, default)
        except Exception as e:
            self.info.err(e)

    def setGlobalSetting(self, key, value):
        try:
            settings = QSettings()
            prefix = 'GeoTaskOrganizer/'
            key = prefix + key
            settings.setValue(key, value)
        except Exception as e:
            self.info.err(e)

    def getGlobalSetting(self, key, default=None):
        try:
            settings = QSettings()
            prefix = 'GeoTaskOrganizer/'
            key = prefix + key
            return settings.value(key, default)
        except Exception as e:
            self.info.err(e)

    def showGtoAttributeTable(self, checked):
        try:
            dw = self.iface.mainWindow().findChild(QDockWidget, 'GtoAttributeTable')
            if dw is not None:
                dw.setFloating(False)
                dw.reload()
            else:
                dw = GtoDockWidgetAttributeTable(self.gtomain, self.iface.mainWindow())
                dw.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea)
                self.iface.addDockWidget(Qt.TopDockWidgetArea, dw)
            dw.setHidden(not checked)
        except Exception as e:
            self.info.err(e)

    def showQgisFeatureForm(self, layer, feat):
        try:
            dlg = self.iface.getFeatureForm(layer, feat)
            dlg.show()
        except Exception as e:
            self.info.err(e)

    def refreshLayer(self, layer):
        try:
            if layer is not None and self.iface.mapCanvas().isCachingEnabled():
                layer.triggerRepaint()
            else:
                self.iface.mapCanvas().refresh()
        except Exception as e:
            self.info.err(e)

    def getDockWidgetFeaturesFlags(self, settings):
        try:
            flags = QDockWidget.NoDockWidgetFeatures
            for i in settings:
                if i == 1:
                    flags = flags | QDockWidget.DockWidgetClosable
                elif i == 2:
                    flags = flags | QDockWidget.DockWidgetMovable
                elif i == 4:
                    flags = flags | QDockWidget.DockWidgetFloatable
                elif i == 7:
                    flags = QDockWidget.AllDockWidgetFeatures
                    break
            return flags
        except Exception as e:
            self.info.err(e)

    def get_ui_file(self, ui_file, default):
        try:
            if ui_file is None:
                file = os.path.join(self.gtomain.gtoplugin.plugin_dir, default)
                self.info.err(None, "ui is null, using default!".format(file))
            else:
                file = os.path.join(self.metadata.dirForms, ui_file)  # customized
                # if self.debug: self.info.err(None, "ui customized:", file)
                if not os.path.isfile(file):  # user
                    file = os.path.join(self.gtomain.gtoplugin.plugin_dir, ui_file)  # files in gto plugin folder
                    # if self.debug: self.info.err(None, "ui user:", file)
                if not os.path.isfile(file):  # default
                    self.info.err(None, "ui <{0}> not found, using default!".format(file))
                    file = os.path.join(self.gtomain.gtoplugin.plugin_dir, default)
            if self.debug: self.info.log("loading ui:", os.path.abspath(file))
            return file
        except Exception as e:
            self.info.err(e)
