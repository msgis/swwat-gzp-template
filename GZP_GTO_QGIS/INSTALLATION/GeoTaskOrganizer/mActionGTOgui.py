#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt, QObject
from PyQt5.QtWidgets import QApplication, QDialog, QAction, QToolBar, QDockWidget, QSizePolicy
from PyQt5.QtGui import QIcon

import os


class run(QObject):
    def __init__(self, id, gtotool, config, debug):
        super(run, self).__init__()
        try:
            self.debug = debug
            self.gtotool = gtotool
            self.gtomain = gtotool.gtomain
            self.metadata = self.gtomain.metadata
            self.helper = self.gtomain.helper
            self.iface = gtotool.iface
            self.info = gtotool.info

            toolbars_moveable_all = config.get("toolbars_moveable_all", True)
            toolbars_not_moveable = config.get('toolbars_not_moveable', [])

            toolbars_contexmenu_all = config.get("toolbars_contexmenu_all", True)
            toolbars_no_contexmenu = config.get('toolbars_no_contexmenu', [])

            panels_features_all = config.get('panels_features_all', [7])
            panels_features = config.get("panels_features", {})

            panels_dock_all = config.get("panels_dock_all", True)
            panels_no_dock = config.get('panels_no_dock', [])

            panels_contexmenu_all = config.get("panels_contexmenu_all", True)
            panels_no_contexmenu = config.get('panels_nocontexmenu', [])

            panels_sizeable = config.get("panels_sizeable", True)

            actions_icons = config.get("actions_icons", {})

            widgets = QApplication.instance().allWidgets()
            for wid in widgets:
                objname = wid.objectName()
                title = wid.windowTitle()
                # if self.debug: self.info.log("widget:", objname, "/", title)
                # toolbars
                if isinstance(wid, QToolBar):
                    # moveable
                    wid.setMovable(toolbars_moveable_all)
                    # moveable exceptions
                    if objname in toolbars_not_moveable or title in toolbars_not_moveable:
                        wid.setMovable(False)
                        if self.debug: self.info.log("toolbars_not_moveable:", objname, "/", title)
                    # contexmenu
                    if not toolbars_contexmenu_all:
                        wid.setContextMenuPolicy(Qt.PreventContextMenu)
                    else:
                        wid.setContextMenuPolicy(Qt.DefaultContextMenu)
                    # contex menu exceptions
                    if objname in toolbars_no_contexmenu or title in toolbars_no_contexmenu:
                        wid.setContextMenuPolicy(Qt.PreventContextMenu)
                        if self.debug: self.info.log("toolbars_no_contexmenu:", objname, "/", title)
                    # debug
                    if objname == 'gtoTB_debug':
                        wid.setContextMenuPolicy(Qt.DefaultContextMenu)

                # panels (dockwidgets)
                if isinstance(wid, QDockWidget):
                    flags = self.helper.getDockWidgetFeaturesFlags(panels_features_all)
                    # features_all
                    wid.setFeatures(flags)
                    #if self.debug: self.info.log("DockWidget:", wid.objectName())
                    # features
                    if title in panels_features:
                        flags = self.helper.getDockWidgetFeaturesFlags(panels_features[title])
                        wid.setFeatures(flags)
                        if self.debug: self.info.log("panels_features:", "title:", title, "/flags:", wid.features())
                    # features
                    if objname in panels_features:
                        flags = self.helper.getDockWidgetFeaturesFlags(panels_features[objname])
                        wid.setFeatures(flags)
                        if self.debug: self.info.log("panels_features:", "objectname:", objname, "/flags:",
                                                     wid.features())
                    # MessageLog always enabled for debuggung
                    if objname == "MessageLog":
                        wid.setFeatures(QDockWidget.AllDockWidgetFeatures)
                    # contexmenu
                    if not panels_contexmenu_all:
                        wid.setContextMenuPolicy(Qt.PreventContextMenu)
                    else:
                        wid.setContextMenuPolicy(Qt.DefaultContextMenu)
                    # contexmenu exceptions
                    if objname in panels_no_contexmenu or title in panels_no_contexmenu:
                        wid.setContextMenuPolicy(Qt.PreventContextMenu)
                        if self.debug: self.info.log("panels_no_contexmenu:", objname, "/", title)
                    # dockable
                    if panels_dock_all:
                        wid.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
                    else:
                        wid.setAllowedAreas(Qt.NoDockWidgetArea)
                    if objname in panels_no_dock or title in panels_no_dock:
                        wid.setAllowedAreas(Qt.NoDockWidgetArea)
                        if self.debug: self.info.log("panels_no_dock:", objname, "/", title)
            # actions
            for k in actions_icons.keys():
                action = self.iface.mainWindow().findChild(QAction, k)
                try:
                    if action is not None:
                        file = os.path.join(self.metadata.dirToolIcons, actions_icons[k])
                        if os.path.isfile(file):
                            action.setIcon(QIcon(file))
                except Exception as e:
                    self.info.err(e)
        except Exception as e:
            self.info.err(e)
