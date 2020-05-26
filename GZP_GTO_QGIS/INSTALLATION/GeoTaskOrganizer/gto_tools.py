#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QAction, QWidgetAction, QLabel

import os.path
import json

from .gto_info import gtoInfo
from .gto_tool import gtoTool
from .gto_commands import *


class gtoTools(QObject):
    def __init__(self, gtomain):
        super(gtoTools, self).__init__()
        self.setObjectName(__name__)
        # references
        self.gtomain = gtomain
        self.helper = self.gtomain.helper
        self.metadata = self.gtomain.metadata
        self.iface = gtomain.iface
        self.info = gtoInfo(self)
        self.debug = gtomain.debug
        self.gtoactions = []
        self.gtoactions_default = None

    def getGTOaction(self, path):
        try:
            if self.debug: self.info.log('getGTOaction')
            self.gtoactions = []
            for f in os.listdir(path):
                if f.lower().endswith(".json"):
                    actionname = f.replace('.json', '')
                    ext = f.split(".")[-1]
                    if ext.lower() == "json":
                        if self.debug: self.info.log("loading:", f)
                        data = None
                        # read data
                        try:
                            filename = os.path.join(path, f)
                            f = io.open(filename, encoding='utf-8')
                            data = json.load(f)
                            f.close()
                        except Exception as e:
                            msg = '{0} is not a valid json file!'.format(filename)
                            self.info.err(e, msg)  # None = warning

                        if data:  # build actions
                            tools_data = data.get('tools', [])
                            if self.debug: self.info.log(tools_data)
                            if not tools_data:  # empty
                                msg = 'Could not find {0} in {1}'.format('[tools]', filename)
                                self.info.err(None, msg)  # None = warning
                            for tool in tools_data:  # MUST!
                                if tool.get("is_widgetaction", False):
                                    action = gtoWidgetAction(self)
                                else:
                                    action = gtoAction(self,self.iface.mainWindow())  # QAction(self)
                                # objectname
                                ToolID = tool['id']
                                objname = actionname + str(ToolID)
                                action.setObjectName(objname)
                                # tooldata
                                action.setData(tool)
                                # misc
                                caption = tool.get('caption', objname)
                                icon = tool.get('icon', None)
                                icontext = tool.get('icontext', None)
                                statustip = tool.get('statustip', None)
                                tooltip = tool.get('tooltip', None)
                                checked = tool.get('checked', None)
                                visible = tool.get('visible', True)
                                whatsthis = tool.get('whatsthis', None)
                                shortcut = tool.get('shortcut', None)
                                # set properties
                                # caption
                                action.setText(caption)
                                # icon
                                if icon is None or icon == '':  # for all sub-tools
                                    icon = actionname.lower() + ".png"
                                    iconfile = os.path.join(self.metadata.dirToolIcons, icon)
                                    if not os.path.isfile(iconfile):
                                        icon = actionname.lower() + ".svg"
                                        iconfile = os.path.join(self.metadata.dirToolIcons, icon)
                                else:
                                    iconfile = os.path.join(self.metadata.dirToolIcons, icon)
                                # if self.debug: self.info.log("tool icon: ", actionname, ":", iconfile)
                                if os.path.exists(iconfile):
                                    action.setIcon(QIcon(iconfile))
                                # else:
                                #     action.setIcon(self.helper.getIcon('noActionIcon.png'))
                                if icontext is not None and not icontext == '':
                                    action.setIconText(icontext)
                                if visible is not None: action.setVisible(visible)
                                if statustip is not None:  action.setStatusTip(statustip)
                                if whatsthis is not None:  action.setWhatsThis(whatsthis)
                                if tooltip is not None:  action.setToolTip(tooltip)
                                if shortcut is not None: action.setShortcut(QKeySequence(shortcut))

                                if checked is not None and checked:  # activate on add to gto toolbar!
                                    action.setCheckable(True)
                                    action.setChecked(checked)
                                # finally
                                action.triggered.connect(self.rungtotool)
                                self.gtoactions.append(action)
            if self.debug: self.info.log("gto actions:", len(self.gtoactions))
            return self.gtoactions
        except Exception as e:
            self.info.err(e)

    def rungtotool(self):
        if self.debug: self.info.log('runGTOtool')
        caller = self.sender()
        try:
            if self.debug: self.info.log('rungtotool::import module')
            module_name = self.gtomain.helper.getName(caller.objectName())
            if self.debug: self.info.log('runGTOtool', module_name)
            if module_name == "":
                pass
            else:
                obj = gtoTool(self.gtomain, module_name)
                if obj is not None:
                    if self.debug: self.info.log('runGTOtool:', 'trigger')
                    obj.triggered(caller)
        except Exception as  e:
            self.info.err(e)


class gtoAction(QAction):
    def __init__(self, gtomain, parent=None):
        super(gtoAction, self).__init__(parent)
        self.gtoMain = gtomain
        self.debug = gtomain.debug
        self.info = gtomain.info
        self.iface = gtomain.iface
        self.prj = QgsProject.instance()
        self.iface.mapCanvas().currentLayerChanged.connect(self.layer_changed)
        self.iface.mapCanvas().selectionChanged.connect(lambda: self.layer_changed(self.iface.activeLayer()))
        self.toolData = {}
        self.config = {}
        self.enabled_config = {}

    def setData(self, tooldata):
        self.toolData = tooldata
        self.config = self.toolData.get("config", {})
        self.enabled_config = self.config.get("enabled", {})
        QAction.setData(self, tooldata)

    def layer_changed(self, layer):
        try:
            if layer is not None and self.isVisible():
                if "active_layer" in self.enabled_config:
                    res = self.enabled_config.get("active_layer") == layer.name()
                    self.set_enabled(res)
                if "selection" in self.enabled_config:
                    res = self.enabled_config.get("selection")
                    self.check_selection(layer, res)
                if "layer_selection" in self.enabled_config:
                    config = self.enabled_config.get("layer_selection")
                    lyr = config.get("layer")
                    res = config.get("selection")
                    lyr = self.prj.mapLayersByName(lyr)[0]
                    self.check_selection(lyr, res)
        except Exception as  e:
            self.info.err(e)

    def setChecked(self, a0):
        #self.info.err(None,"gtoAction:",a0)
        QAction.setChecked(self,a0)

    def set_enabled(self, res):
        try:
            if self.isEnabled() != res:
                self.setEnabled(res)
        except Exception as  e:
            self.info.err(e)

    def check_selection(self, layer, count):
        try:
            res = layer.selectedFeatureCount() == count
            if layer.selectedFeatureCount() > 0 and count == -1:
                res = True
            self.set_enabled(res)
            if self.debug: self.info.log("check_selection:", layer.name(), "res:", res)
        except Exception as  e:
            self.info.err(e)

    def added(self, widget):
        try:
            self.layer_changed(self.iface.activeLayer())
        except Exception as  e:
            self.info.err(e)


class gtoWidgetAction(QWidgetAction, gtoAction):
    def __init__(self, gtomain, parent=None):
        super(gtoWidgetAction, self).__init__(gtomain, parent=parent)

        self.gtomain = gtomain
        self.info = self.gtomain.info
        self.debug = self.gtomain.debug
        self.widget = None

    def setObjectName(self, name):
        try:
            if self.debug: self.info.log("gtoWidgetAction:setObjectName", name)
            if name.startswith("mActionGTOpoint"):
                from .gto_point import GTOPointWidget
                self.widget = GTOPointWidget(self.gtomain)
                self.setDefaultWidget(QLabel(name))
        except Exception as  e:
            self.info.err(e)
        finally:
            gtoAction.setObjectName(self, name)

    def setChecked(self, a0):
        #self.info.err(None, self.objectName(),":checked:", a0)
        gtoAction.setChecked(self, a0)

    def createWidget(self, parent):
        try:
            if self.objectName().startswith("mActionGTOpoint"):
                # var1
                from .gto_point import GTOPointWidget
                self.widget = GTOPointWidget(self.gtomain, parent)
                tooldata = self.data()
                config = tooldata.get("config", {})
                self.widget.setConfig(config)
                # var2
                # self.widget.setParent(parent)
                if self.debug: self.info.log("gtoWidgetAction:createWidget", self.widget)
                return self.widget
        except Exception as  e:
            self.info.err(e)

    def setData(self, tooldata):
        try:
            if self.debug: self.info.log("gtoWidgetAction:setData", tooldata)
            if self.widget is not None:
                config = tooldata.get("config", {})
                self.widget.setConfig(config)
        except Exception as  e:
            self.info.err(e)
        finally:
            gtoAction.setData(self, tooldata)

    def added(self, widget):
        try:
            if self.debug: self.info.log("added:gtoWidgetAction:", widget.objectName())
            if self.widget is not None:
                self.widget.added()
        except Exception as  e:
            self.info.err(e)
        finally:
            gtoAction.added(self, widget)
