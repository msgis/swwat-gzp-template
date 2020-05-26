# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt, QObject, QTranslator, qVersion, QCoreApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QWidget, QDockWidget, QSizePolicy, QDockWidget
from PyQt5 import uic

from qgis.core import QgsApplication, QgsProject

from .gto_main import gtoMain
from .gto_info import gtoInfo

import os
import datetime

plugin_name = 'GeoTaskOrganizer'
plugin_objectName = 'gto_plugin'  # 'mGTO'


class gtoPlugin(QObject):

    def __init__(self, iface):
        super(gtoPlugin, self).__init__()
        self.setObjectName(plugin_objectName)
        self.plugin_name = plugin_name
        self.plugin_dir = os.path.dirname(__file__)
        self.plugin_actions = []
        self.first_start = True
        # qgis interface
        self.iface = iface
        self.iface.mainWindow().showMinimized()
        # app info
        self.info = gtoInfo(self)
        # debug ?
        path = os.path.join(self.plugin_dir, 'log')
        self.debug = os.path.exists(path)
        if self.debug:
            self.info.do_backup()  # new session
            start_time = str(datetime.datetime.now()).split(".")[0]
            self.info.log("GTO version {0} loaded (UTC): ".format(self.get_version()), start_time)
            self.info.log(plugin_name, "debug:", self.debug)
        # DockWidget
        self.dockwidget = QDockWidget()
        self.dockwidget.setWindowTitle(plugin_name)
        self.dockwidget.setObjectName('GTODockWidget')
        self.dockwidget.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dockwidget)
        self.app = gtoMain(self)
        # correct settings in statusbar:S
        try:
            wids = iface.mainWindow().statusBar().findChildren(QWidget)
            for wid in wids:
                if wid.objectName() == 'mOntheFlyProjectionStatusButton' or wid.objectName() == 'mMessageLogViewerButton':
                    if not wid.isHidden():
                        wid.setMaximumHeight(16777215)
                        wid.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        except:
            pass
        # initialize locale
        locale = QgsApplication.locale()
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'plugin_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '3.0.0':
                QCoreApplication.installTranslator(self.translator)
        # run
        self.run()

    def tr(self, message):
        return QCoreApplication.translate('plugin', message)

    def add_action(
            self,
            text,
            objname,
            callback,
            icon_path=None,
            enabled_flag=True,
            add_to_menu=False,
            add_to_toolbar=False,
            status_tip=None,
            whats_this=None,
            parent=None):

        action = QAction(text)
        icon = QIcon()
        if isinstance(icon_path, QIcon):
            icon = icon_path
        else:
            if icon_path and os.path.isfile(icon_path):
                icon = QIcon(icon_path)
                # if self.debug: self.info.log(icon_path)
        action.setIcon(icon)
        action.setParent(parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)
        action.setObjectName(objname)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar or self.debug:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu or self.debug:
            self.iface.addPluginToMenu(
                self.plugin_name,
                action)

        self.plugin_actions.append(action)
        self.iface.mainWindow().addAction(action)
        return action

    def initGui(self):  # must be named like that!
        try:
            mw = self.iface.mainWindow()
            # app icon
            app_icon = os.path.join(self.plugin_dir, 'icon.png')
            # run action
            self.add_action(text="Version " + self.get_version(), objname=plugin_objectName, icon_path=app_icon,
                            callback=self.run, add_to_menu=True, add_to_toolbar=True,
                            parent=mw)
            # set app icon
            self.setPluginIcon(app_icon)
            self.first_start = False
            # add additonal plugin actions
            icon = os.path.join(self.plugin_dir, "qgis.png")
            self.add_action(text='QGIS UI speichern', objname=plugin_objectName + 'saveQGISui', icon_path=icon,
                            callback=lambda: self.app.qgis.storeQGISui(True), add_to_menu=True, add_to_toolbar=True,
                            parent=mw)
            if self.debug:
                self.add_action(text='QGIS UI laden', objname=plugin_objectName + 'loadQGISui', icon_path=icon,
                                callback=lambda :self.app.qgis.restoreQGISui(True), add_to_menu=True, add_to_toolbar=True,
                                parent=mw)
        except Exception as e:
            self.info.err(e)

    def setPluginIcon(self, app_icon):
        try:
            for action in self.iface.pluginMenu().actions():
                if action.text() == self.plugin_name:
                    action.setIcon(QIcon(app_icon))
        except Exception as e:
            self.info.err(e)

    def get_version(self):
        try:
            file = os.path.join(self.plugin_dir, 'metadata.txt')
            text = None
            msg = ''
            if os.path.isfile(file):
                f = open(file, 'r')
                text = f.readlines()
                f.close()
            for line in text:
                if "version=" in line:
                    line = line.replace('\n', '')
                    msg = msg + str.replace(line, "version=", "")
                    break
            return msg
        except Exception as e:
            self.info.err(e)

    def unload(self):
        try:
            """Removes the plugin menu item and icon from QGIS GUI."""
            for action in self.plugin_actions:
                self.iface.removePluginMenu(
                    self.tr(plugin_name),
                    action)
                self.iface.removeToolBarIcon(action)
        except Exception as e:
            self.info.err(e)
        try:  # on close iface is already gone :/ but needed if plugin is deactivated
            if not self.app is None:  # should never happen
                if self.debug: self.info.log("unload")
                self.dockwidget.setHidden(True)
                self.app.reset(True)  # true=>std ui
        except Exception as e:
            self.info.err(e)

    def run(self):
        try:
            if self.first_start:
                self.first_start = False
                self.iface.projectRead.connect(self.project_read)
                QgsProject.instance().cleared.connect(self.project_cleared)
                self.iface.initializationCompleted.connect(self.iface_initializationCompleted)
        except Exception as e:
            self.info.err(e)

    def project_read(self):
        try:
            self.app.loadgto()
        except Exception as e:
            self.info.err(e)

    def project_cleared(self):
        try:
            if self.debug: self.info.log('project_cleared')
            self.app.reset(True)
        except Exception as e:
            self.info.err(e)

    def iface_initializationCompleted(self):  # if QGIS opened (without qgs)
        try:
            if self.debug: self.info.log('iface_initializationCompleted')
            # if not self.app.gto_loaded:
            #     self.app.qgis.storeQGISui()
            # self.iface.mainWindow().showFullScreen()
            self.iface.mainWindow().showMaximized()
        except Exception as e:
            self.info.err(e)
