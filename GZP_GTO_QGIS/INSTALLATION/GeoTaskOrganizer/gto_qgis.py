# -*- coding: utf-8 -*-

from PyQt5.QtCore import QSaveFile, QIODevice, QStandardPaths, QFile
from PyQt5.QtWidgets import QMenu

import os.path

from .gto_debug import *
from .mActionGTOgui import run as mActionGTOunlockUI


class gtoQgis(QObject):
    def __init__(self, gtomain, parent=None):
        super(gtoQgis, self).__init__(parent)
        self.setObjectName(__name__)
        # references
        self.gtomain = gtomain
        self.metadata = self.gtomain.metadata
        self.iface = self.gtomain.iface
        self.info = self.gtomain.info
        self.debug = self.info.debug
        self.helper = self.gtomain.helper

    def storeQGISui(self,force =False):
        try:
            # store current QGIS ui
            # layout
            qgisAppDataPath = QStandardPaths.standardLocations(QStandardPaths.AppDataLocation)[0]
            file = os.path.join(qgisAppDataPath, 'qgis_ui.bin')
            if not os.path.isfile(file) or force:
                if self.debug: self.info.log("storeQGISui:", self.helper.shortDisplayText(file))
                f = QSaveFile(file)
                f.open(QIODevice.WriteOnly)
                f.write(self.iface.mainWindow().saveState())
                f.commit()
        except Exception as e:
            self.info.err(e)

    def restoreQGISui(self,msg = False):
        try:
            try:
                if self.iface.mainWindow() is None: return  # dummy
            except:
                # prevent: ERROR:  <class 'RuntimeError'> gto_gps.py | line: 240 | ('wrapped C/C++ object of type QgisInterface has been deleted',)
                # because QGIS is already closing
                return
            iface = self.iface
            mActionGTOunlockUI(0, self, {}, self.debug)  # unlocks ui
            qgisAppDataPath = QStandardPaths.standardLocations(QStandardPaths.AppDataLocation)[0]
            file = os.path.join(qgisAppDataPath, 'qgis_ui.bin')
            if os.path.isfile(file):
                if self.debug: self.info.log("restoreGTOui:", self.helper.shortDisplayText(file))
                f = QFile(file)
                f.open(QIODevice.ReadOnly)
                data = f.readAll()
                f.close()
                self.iface.mainWindow().restoreState(data)
            else:
                if msg:
                    self.info.msg("Datei <{0}> nicht gefunden!".format(file))
            # make sure menu and statusbar are shown, worst case after restart qgis
            # menus
            menubar = iface.mainWindow().menuBar()
            menubar.setHidden(False)
            menus = menubar.findChildren(QMenu)
            for menu in menus:
                menubar.removeAction(menu.menuAction())
            menus = [iface.projectMenu(), iface.editMenu(), iface.viewMenu(), iface.layerMenu(), iface.settingsMenu(), iface.pluginMenu(), iface.vectorMenu(), iface.rasterMenu(), iface.databaseMenu(), iface.firstRightStandardMenu(), iface.helpMenu()]
            for menu in menus:
                menubar.addAction(menu.menuAction())
                menu.menuAction().setVisible(True)
            menubar.setHidden(False)
            # statusbar
            qstat = iface.statusBarIface()  # QgsStatusBar
            qstat.setHidden(False)
            for wid in qstat.findChildren(QWidget):
                if wid.objectName() != '':
                    wid.setHidden(False)
            qstat.setHidden(False)
            iface.mainWindow().statusBar().setHidden(False)
        except Exception as e:
            self.info.err(e)
