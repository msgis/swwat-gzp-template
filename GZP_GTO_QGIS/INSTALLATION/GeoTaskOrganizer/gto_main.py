# -*- coding: utf-8 -*-

from PyQt5.QtCore import QFile, QTextStream, QStandardPaths, QByteArray, QSaveFile, QIODevice, QFile, QSettings, QUrl, \
    QEvent
from PyQt5.QtGui import QIcon, QPixmap, QFont, QBrush, QColor, QMouseEvent
from PyQt5.QtWidgets import QTreeWidgetItem, QSplashScreen, QTreeWidget, QPushButton, QWidget, QTreeWidgetItemIterator, \
    QTextBrowser, QSplitter, QMenu
from PyQt5 import uic

import os.path
import json
import shutil

from qgis.core import Qgis, QgsProject, QgsApplication
from qgis import utils

from .gto_metadata import gtoMetadata
from .gto_remote import gtoRemote
from .gto_commands import *
from .gto_debug import *
from .gto_helper import gtoHelper
from .gto_tools import gtoTools
from .gto_actions import *
from .gto_gps import GPS, GtoWidgetGpsPort
from .gto_widgets import GTOtextBrowser
from .gto_coordinate import GTOCoordinatesDockWidget
from .gto_qgis import gtoQgis


class gtoMain(QObject):
    def __init__(self, gtoplugin, parent=None):
        super(gtoMain, self).__init__(parent)
        self.setObjectName(__name__)
        # references
        self.gtomain = self  # if unknown if gtoObj is gtomain or not
        self.gto_loaded = False
        self.gtoplugin = gtoplugin
        self.metadata = gtoMetadata()
        self.iface = self.gtoplugin.iface
        self.prj = QgsProject.instance()
        self.info = gtoInfo(self)
        self.info.log("GTO loaded")  # this text is detected in clearMessageLog
        self.debug = self.info.debug
        self.helper = gtoHelper(self)
        self.info.log("log file:", self.helper.shortDisplayText(self.info.getlogfile()))
        self.gtotools = gtoTools(self)
        self.qgis = gtoQgis(self)
        # status vars
        self.splasher = None
        self.home_path = ''
        self.gtoactions = []
        self.lastnode = None
        self.remote = None
        self.gps = GPS(self)
        self.activeItem = None
        self.gto_name = None
        # status vars settings
        self.settings = {}
        # "GTO Widget": {
        self.gto_ui = None
        self.gto_plugins = []
        self.unload_plugins = []
        self.gto_startuptools = []
        self.gto_startuptools_2 = []  # obsolete - compatible
        self.gto_dock = 1
        self.gto_features = [7]  # all widget features
        # "GTO Toolbar": {
        self.toolbar_style = 0
        self.toolbar_dock = 8
        self.toolbar_height = None
        self.toolbar_moveable = True
        self.toolbar_no_tools = ['mActionGTOversion']

        # "GTO Tree": {]
        self.tree_expand = 0
        self.tree_single_click = False
        self.tree_indentation = None
        # self.tree_showIndicator = 2
        # "QGIS":{}
        self.qgis_stylefile = None
        self.qgis_icon = None
        self.qgis_title = "QGIS powered by ms.GIS"
        self.qgis_statusbar = False
        self.qgis_menu = False
        # "Remote": {}
        self.remote_file = None
        self.remote_app_file = None
        self.remote_watch_file = None
        self.remote_app_title = None
        # toolbar
        self.gtotb = self.helper.getToolBar(self, "mGTOtoolbar", "GTO Toolbar", self.iface.mainWindow())
        # GTO widgets and ui mapping
        self.dockwidget = self.gtoplugin.dockwidget

        # tree
        self.tree = QTreeWidget()
        self.textBrowser = QTextBrowser()
        self.labelPicture = QLabel()

        # install default gto-actions
        self.internalActions = self.getInternalActions()

        # init (generic) gto widgets (only dockwids/toolbars)
        self.gtowids = [GTOCoordinatesDockWidget(self, self.iface.mainWindow())]

        # add toolbars
        self.debugObj = gtoDebug(self)
        self.actionsWatched = []

    def set_gto_ui(self, ui_file):
        try:
            file = self.helper.get_ui_file(ui_file, 'gto.ui')
            wid = uic.loadUi(file)
            self.dockwidget.setWidget(wid)
            # tree
            self.tree = wid.treeWidget
            self.tree.setHeaderHidden(True)
            self.tree.setItemsExpandable(True)
            self.tree.setColumnCount(1)
            self.tree.clear()
            self.tree.itemClicked.connect(self.node_onclick)

            self.textBrowser = GTOtextBrowser(self)
            self.textBrowser.setMaximumHeight(wid.textBrowser.maximumHeight())
            self.textBrowser.setMinimumHeight(wid.textBrowser.minimumHeight())
            self.textBrowser.setSizePolicy(wid.textBrowser.sizePolicy())
            # find parent
            res = wid.findChildren(QSplitter)
            if len(res) > 0:
                splitter = res[0]
                splitter.replaceWidget(splitter.indexOf(wid.textBrowser), self.textBrowser)
            else:
                wid.textBrowser.parentWidget().layout().replaceWidget(wid.textBrowser, self.textBrowser)
            wid.layout().update()
            self.textBrowser.setHidden(True)

            self.labelPicture = wid.labelPicture
            self.labelPicture.clear()
            self.labelPicture.setHidden(True)
        except Exception as e:
            self.info.err(e)

    def reset(self, standardUI=True):
        try:
            self.debugObj.unlock_qgis_gui()
            if self.debugObj.toolbar is not None:
                self.debugObj.toolbar.setHidden(True)
            self.unloadgto()
            self.gto_loaded = False
            self.home_path = ''
            self.activeItem = None
            self.tree.clear()
            self.labelPicture.setHidden(True)
            self.textBrowser.setHidden(True)
            self.gtotb.clear()
            self.gtotb.setHidden(True)
            if standardUI:
                if self.debug: self.info.log('reset: restore QGIS UI', standardUI)
                self.qgis.restoreQGISui()
        except Exception as e:
            self.info.err(e)

    def unloadgto(self):
        try:
            if self.remote is not None:
                self.remote.unload()
            if self.gps is not None:
                self.gps.deactivate()
        except Exception as e:
            self.info.err(e)

    def storeGTOui(self):
        try:
            res = self.info.gtoQuestion(
                "GTO UI speichern?", title='GeoTaskOrganizer',
                btns=QMessageBox.Yes | QMessageBox.No,
                parent=self.iface.mainWindow())
            if res == QMessageBox.Yes:
                # layout
                file = os.path.join(self.metadata.dirConfig, 'gto_ui.bin')
                if self.debug: self.info.log("storeGTOui:", self.helper.shortDisplayText(file))
                f = QSaveFile(file)
                f.open(QIODevice.WriteOnly)
                f.write(self.iface.mainWindow().saveState())
                f.commit()
                # # json:
                # # toolbars
                # toolbars = []
                # qtbs = self.iface.mainWindow().findChildren(QToolBar)
                # for tb in qtbs:
                #     objName = tb.objectName()
                #     if not tb.isHidden() and objName != '':
                #         toolbars.append(objName)
                # qdws = self.iface.mainWindow().findChildren(QDockWidget)
                # # pannels
                # pannels = []
                # for dw in qdws:
                #     objName = dw.objectName()
                #     if not dw.isHidden() and objName != '':
                #         pannels.append(objName)
                # # menus
                # menus = []
                # qmenubar = self.iface.mainWindow().menuBar()
                # for action in qmenubar.actions():
                #     objName = action.menu().objectName()
                #     if action.isVisible():
                #         menus.append(objName)
                # # statusbar
                # statusbar = []
                # qstat = self.iface.statusBarIface()  # QgsStatusBar
                # for wid in qstat.findChildren(QWidget):
                #     objName = wid.objectName()
                #     if not wid.isHidden() and objName != '':
                #         statusbar.append(objName)
                # # "Normal and Permanent messages are displayed by creating a small widget (QLabel, QProgressBar or even QToolButton) and then "
                # # "adding it to the status bar using the addWidget() or the addPermanentWidget() function. "
                # # "Use the removeWidget() function to remove such messages from the status bar."
                # # statusbar = self.iface.mainWindow().statusBar().isHidden()
                #
                # # write json
                # data = {"menus": menus, "toolbars": toolbars, "pannels": pannels, "statusbar": statusbar}
                # file = os.path.join(self.metadata.dirConfig, "gto_ui.json")
                # if os.path.isfile(file): os.remove(file)
                # with open(file, 'w', encoding='utf8') as f:
                #     json.dump(data, f, ensure_ascii=False, sort_keys=False, indent=4)
        except Exception as e:
            self.info.err(e)

    def restoreGTOui(self):
        try:
            if self.debug: self.info.log("restoreGTOui")
            # file = os.path.join(self.metadata.dirConfig, "gto_ui.json")
            # if os.path.isfile(file):
            #     with open(file, 'r', encoding='utf-8') as f:
            #         data = json.load(f)
            #         # menus
            #         menus = data.get("menus", [])
            #         qmenubar = self.iface.mainWindow().menuBar()
            #         for action in qmenubar.actions():
            #             objName = action.menu().objectName()
            #             visible = objName in menus
            #             action.setVisible(visible)
            #             # self.info.err(None, objName, visible)
            #         if len(menus) == 0:
            #             qmenubar.setHidden(True)
            #         else:
            #             qmenubar.setHidden(False)
            #         # toolbars
            #         toolbars = data.get("toolbars", [])
            #         qtbs = self.iface.mainWindow().findChildren(QToolBar)
            #         for tb in qtbs:
            #             objName = tb.objectName()
            #             hide = not (objName in toolbars)
            #             tb.setHidden(hide)
            #             # self.info.err(None, objName, hide)
            #         # panels
            #         pannels = data.get("pannels", [])
            #         qdws = self.iface.mainWindow().findChildren(QDockWidget)
            #         for dw in qdws:
            #             hide = not (dw.objectName() in pannels)
            #             dw.setHidden(hide)
            #             # self.info.err(None, objName, hide)
            #         # statusbar
            #         statusbar = data.get("statusbar", [])
            #         qstat = self.iface.statusBarIface()  # QgsStatusBar
            #         for wid in qstat.findChildren(QWidget):
            #             hide = not (wid.objectName() in statusbar)
            #             wid.setHidden(hide)
            #             # self.info.err(None, objName, hide)
            #         if len(statusbar) == 0:
            #             qstat.setHidden(True)
            #         else:
            #             qstat.setHidden(False)
            file = os.path.join(self.metadata.dirConfig, 'gto_ui.bin')
            if os.path.isfile(file):
                if self.debug: self.info.log("restoreGTOui:", self.helper.shortDisplayText(file))
                f = QFile(file)
                f.open(QIODevice.ReadOnly)
                data = f.readAll()
                f.close()
                self.iface.mainWindow().restoreState(data)
            self.iface.mainWindow().statusBar().setHidden(not self.qgis_statusbar)
            self.iface.mainWindow().menuBar().setHidden(not self.qgis_menu)
        except Exception as e:
            self.info.err(e)

    def loadgto(self, force=False):
        try:
            if self.debug: self.info.log("loadgto: force:", force)
            if self.debug: self.info.log("homepath", self.prj.homePath())
            if self.prj.homePath() == '':
                if self.debug: self.info.log("loadgto - aborted")
            if self.remote is not None:
                self.remote.unload()
            if self.gps is not None:
                self.gps.deactivate()
            # set pathes
            if not self.metadata.initProject(self.prj.homePath()):
                return
            if self.home_path == self.prj.homePath() and not force:
                if self.debug: self.info.log("loadgto - aborted")
                return
            self.home_path = self.prj.homePath()
        except Exception as e:
            self.info.err(e)
            self.reset(True)
            return
        self.reset(False)
        # check if gto config exists
        try:
            self.settings = {}
            filename = os.path.join(self.metadata.dirConfig, "settings.json")
            if os.path.isfile(filename):
                if self.debug: self.info.log('read settings:', filename)
                f = io.open(filename, encoding='utf-8')
                self.settings = json.load(f)
                f.close()
            else:
                if not self.debug:
                    return
        except Exception as e:
            if self.debug: self.info.err(e)
            return
        # start gto
        self.splasher = GtoSplasher(self.info)
        self.splasher.log('Lade QGIS-GeoTaskOrganizer {0}...'.format(self.helper.getGTOversion()))
        try:
            self.gto_name = os.path.basename(self.prj.fileName())
            # settings
            if "GTO Widget" in self.settings:
                dic = self.settings["GTO Widget"]
            else:
                dic = self.settings  # compatible
            self.gto_ui = dic.get("gto_ui", self.gto_ui)
            self.gto_plugins = dic.get("gto_plugins", self.gto_plugins)
            self.unload_plugins = dic.get("unload_plugins", self.unload_plugins)
            self.gto_startuptools = dic.get("gto_startuptools", self.gto_startuptools)
            self.gto_startuptools_2 = dic.get("gto_startuptools_2", self.gto_startuptools_2)  # compatible
            self.gto_dock = dic.get("gto_dock", self.gto_dock)
            self.gto_features = dic.get("gto_features", self.gto_features)

            if "GTO Toolbar" in self.settings:
                dic = self.settings["GTO Toolbar"]
            else:
                dic = self.settings
            self.toolbar_style = dic.get("toolbar_style", self.toolbar_style)
            self.toolbar_dock = dic.get("toolbar_dock", self.toolbar_dock)
            self.toolbar_height = dic.get("toolbar_height", self.toolbar_height)
            self.toolbar_moveable = dic.get("toolbar_moveable", self.toolbar_moveable)
            self.toolbar_no_tools = dic.get('toolbar_no_tools', self.toolbar_no_tools)

            if "GTO Tree" in self.settings:
                dic = self.settings["GTO Tree"]
            else:
                dic = self.settings
            self.tree_expand = dic.get("tree_expand", self.tree_expand)
            self.tree_single_click = dic.get("tree_single_click", self.tree_single_click)
            self.tree_indentation = dic.get('tree_indentation', self.tree_indentation)
            # self.tree_showIndicator = dic.get('tree_showIndicator', 2)
            # QTreeWidgetItem::DontShowIndicator=1/ShowIndicator=0/DontShowIndicatorWhenChildless=2

            if "QGIS" in self.settings:
                dic = self.settings["QGIS"]
            else:
                dic = self.settings
            self.qgis_stylefile = dic.get("qgis_stylefile", self.qgis_stylefile)
            self.qgis_icon = dic.get("qgis_icon", self.qgis_icon)
            self.qgis_title = dic.get("qgis_title", self.qgis_title)
            self.qgis_statusbar = dic.get("qgis_statusbar", self.qgis_statusbar)
            self.qgis_menu = dic.get("qgis_menu", self.qgis_menu)

            if "Remote" in self.settings:
                dic = self.settings["Remote"]
            else:
                dic = self.settings
            self.remote_file = dic.get("remote_file", self.remote_file)  # "%APPDATA%/ms.GIS/IProxy4_APG/IProxy4_QGIS.json"
            self.remote_watch_file = dic.get("remote_watch_file", self.remote_watch_file)  # "%APPDATA%/ms.GIS/IProxy4_APG/IProxy4_ACCESS.json"
            self.remote_app_file = dic.get("remote_app_file", self.remote_app_file)  # "C:/WLK/wlk.mdb"
            self.remote_app_title = dic.get("remote_app_title", self.remote_app_title)  # "WLKGIS"if searching for remote app by window title
        except Exception as e:
            self.info.err(e)
            self.splasher.close()
            return
        # "####################################"
        self.set_gto_ui(self.gto_ui)
        # self.iface.statusBarIface().setHidden(not self.qgis_statusbar)# we could use the empty statusbar?
        if self.debug:
            try:
                # run example.py
                run_command(self.gtomain, self.gtomain, "example.py", "run_script")
                # copy sample
                dest = filename
                src = os.path.join(self.metadata.dirPlugin, "settings.json")
                if not os.path.isfile(dest):
                    shutil.copyfile(src, dest)
                    os.startfile(dest)
                src = os.path.join(self.metadata.dirPlugin, "tree.json")
                dest = os.path.join(self.metadata.dirConfig, "tree.json")
                if not os.path.isfile(dest):
                    shutil.copyfile(src, dest)
                    os.startfile(dest)
                # src = os.path.join(self.metadata.dirPlugin, "logo.png")
                # dest = os.path.join(self.metadata.dirHelp, "logo.png")
                # if not os.path.isfile(dest):
                #     shutil.copyfile(src, dest)
            except Exception as e:
                self.info.err(e)
        # style QGIS
        self.splasher.log("QGIS style wird geladen...")
        self.styleQGIS()
        # load requiered plugins
        self.splasher.log("Lade benötigte plugins...")
        self.load_plugins()
        # create gtoActions
        self.splasher.log("Generiere GTO-Tools...")
        self.gtoactions = []
        self.gtoactions.extend(self.gtotools.getGTOaction(self.metadata.dirTools))
        # build gto tree
        self.tree.clear()
        self.tree.setFont(self.iface.mainWindow().font())  # maybe overwritten by tree_style.json (if exists)
        self.splasher.log('Generiere GTO-Baum...')
        file = os.path.join(self.metadata.dirConfig, 'tree.json')
        if os.path.isfile(file):
            f = io.open(file, encoding='utf-8')
            data = json.load(f)
            f.close()
            self.buildtree(None, data, -1, self.getTreeStyle())
            if self.debug: self.check_nodenames()
            self.set_tree_visibilty(self.iface.activeLayer())
        # startuptools - maybe they design the QGIS gui
        self.splasher.log("GTO-Startup Tools werden ausgeführt...")
        self.runcmd(self.gto_startuptools)
        self.runcmd(self.gto_startuptools_2)
        # gui stuff
        self.splasher.log("GTO-Tree wird angepasst...")
        self.setGTOtree()
        self.splasher.log("GTO-Toolbar wird angepasst...")
        self.setGTOtoolbar()
        self.splasher.log("GTO-Widget wird angepasst...")
        self.setGTOwidget()
        # tab all widgets (gto_commands)
        self.splasher.log("QGIS UI wird angepasst...")
        TabWidget(self, self.debug, self.dockwidget)
        # remote proxy
        self.splasher.log("GTO-remote wird installiert...")
        self.remote = gtoRemote(self)
        self.splasher.log("GTO-Listener wird installiert...")
        self.iface.mapCanvas().selectionChanged.connect(self.set_tree_visibilty)
        # gps
        self.splasher.log("GTO-gps wird installiert...")
        self.gps.init()
        if self.debug:
            self.splasher.log("GTO-Debug Tools werden installiert...")
            self.watched_actions()
            self.debugObj.start_debug()
            self.debugObj.ShowMessageLog()
        self.splasher.log("GTO-layout wird finalisiert...")
        self.restoreGTOui()
        self.splasher.log("GTO bereit!")  # Show the result
        self.dockwidget.show()
        # close splasher
        self.splasher.close()
        # self.iface.mainWindow().showFullScreen()
        self.iface.mainWindow().showMaximized()
        # self.iface.mainWindow().setHidden(False)
        self.iface.mainWindow().isActiveWindow()
        self.iface.mainWindow().raise_()
        self.gto_loaded = True
        # QTimer.singleShot(500, self.QgisInitCompleted)

    def node_onclick(self, item, Index):  # QTreeWidgetItem
        QApplication.setOverrideCursor(Qt.WaitCursor)
        if self.debug: self.info.log('node_onclick')
        # on exit support
        try:
            if self.lastnode is not None:
                items = self.tree.findItems(self.lastnode, Qt.MatchExactly | Qt.MatchRecursive)
                if items is not None:
                    if len(items) > 0:
                        lastitem = items[0]
                        if lastitem.text(0) != item.text(0):
                            if self.debug: self.info.log("Last node: ", lastitem.text(0), "=> new node: ", item.text(0))
                            tools_onExit = lastitem.data(3, 0)
                            if self.debug: self.info.log('on_exit:', tools_onExit)
                            self.runcmd(tools_onExit)
        except Exception as e:
            self.info.err(e)
        try:
            self.lastnode = item.text(0)
            if self.debug: self.info.log('node_onclick:', self.lastnode)
            # helptext
            helptext = item.data(4, 0)
            self.ShowHelpText(helptext)

            if self.debug: self.info.log('set toolbar')
            self.gtotb.setHidden(False)  # safty
            for w in self.gtotb.findChildren(QWidget):
                try:
                    if hasattr(w, 'reset'):
                        w.reset()
                except Exception as e:
                    if self.debug: self.info.err(e)
            tools = item.data(2, 0)

            # active toolbar
            self.activeItem = item
            tools = self.getItemTools(item)
            self.gtotb.addTools(tools)

            if not self.gtotb.hasTools():
                self.gtotb.addTools(self.toolbar_no_tools)
            if self.tree_single_click:
                if self.debug: self.info.log("tree_single_click", self.tree_single_click)
                parent = item.parent()
                if parent is not None:
                    child_count = parent.childCount()
                    for i in range(child_count):
                        it = parent.child(i)
                        it.setExpanded(False)
                    for i in range(item.childCount()):
                        it = item.child(i)
                        it.setExpanded(False)
                else:  # root node
                    self.tree.collapseAll()
                item.setExpanded(True)

            # run tool(s)
            cmd = item.data(1, 0)
            QTimer.singleShot(50, lambda: self.runcmd(cmd))
        except Exception as e:
            self.info.err(e)
        finally:
            QApplication.restoreOverrideCursor()

    def ShowHelpText(self, helptext):
        try:
            self.labelPicture.clear()
            self.labelPicture.setHidden(True)
            self.textBrowser.clear()
            self.textBrowser.setHidden(True)
            if helptext is not None:
                if self.debug: self.info.log("helptext:", helptext)
                # check if its a  file
                helpfile = self.helper.checkFileExists(helptext, self.metadata.dirHelp)
                if self.debug: self.info.log("helpfile:", helpfile)
                if helpfile is not None:  # its a file, load the content
                    if helpfile.lower().endswith(".png"):
                        img = QPixmap(helpfile)
                        self.labelPicture.setPixmap(img)
                        self.labelPicture.setHidden(False)
                    elif helpfile.lower().endswith(".json"):
                        dic = self.helper.readJson(helpfile)
                        js = json.dumps(dic, indent=4, sort_keys=True)
                        self.textBrowser.setText(js, helpfile)
                        self.textBrowser.setHidden(False)
                    else:
                        self.textBrowser.setSource(QUrl.fromLocalFile(helpfile))
                        self.textBrowser.setHidden(False)
                else:
                    self.textBrowser.setText(helptext)
                    self.textBrowser.setHidden(False)
        except Exception as e:
            self.info.err(e)

    def runcmd(self, value):
        result = False
        try:
            if self.debug: self.info.log('runcmd', value)
            if value is None: return False
            if isinstance(value, str):
                value = [value]
            if isinstance(value, list):
                cmds = value
                for cmd in cmds:
                    if len(cmd) > 0:
                        action = self.findAction(cmd)
                        if action is not None:
                            action.trigger()
                            if self.debug: self.info.log("runcmd:", cmd)
                            result = True
            else:
                if self.debug: self.info.log('runcmd: no string or list')
        except Exception as e:
            self.info.err(e)
        finally:
            return result

    def findAction(self, objName):
        try:
            action = self.iface.mainWindow().findChild(QAction, objName)
            if action is not None: return action
            # if self.debug: self.info.log('findAction', objName)
            found = None
            for action in self.gtoactions:
                if action.objectName().lower() == objName.lower():
                    found = action
                    break
            if not found:
                found = self.findActionByObjectName(objName)
            if not found:
                found = self.findActionByLabel(objName)
            if self.debug and not found: self.info.log('findAction: ', objName, 'not found!')
            return found
        except Exception as e:
            self.info.err(e)

    def findActionByObjectName(self, objname):
        try:
            # toolbars
            toolbars = self.iface.mainWindow().findChildren(QToolBar)
            for toolbar in toolbars:
                for action in toolbar.actions():
                    if action.objectName():
                        if action.objectName().lower() == objname.lower(): return action
                    if action.actionGroup() is not None:
                        for a in action.actionGroup().actions():
                            if a.objectName():
                                if a.objectName().lower() == objname.lower(): return a
            # menus
            menubar = self.iface.mainWindow().menuBar()
            for action in menubar.actions():
                if action.menu() is not None:
                    for action in action.menu().actions():
                        if action.menu():
                            for a in action.menu().actions():
                                if a.objectName():
                                    if a.objectName().lower() == objname.lower(): return a
                        else:
                            if action.objectName():
                                if action.objectName().lower() == objname.lower(): return action
                else:
                    if action.objectName():
                        if action.objectName().lower() == objname.lower(): return action
        except Exception as e:
            self.info.err(e)

    def findActionByLabel(self, label):
        try:
            label = label.lower()
            toolbars = self.iface.mainWindow().findChildren(QToolBar)
            for toolbar in toolbars:
                for action in toolbar.actions():
                    if action.text():
                        if action.text().lower() == label: return action
                    if action.actionGroup() is not None:
                        for a in action.actionGroup().actions():
                            if a.text():
                                if a.text().lower() == label: return a
            menubar = self.iface.mainWindow().menuBar()
            for action in menubar.actions():
                if action.menu():
                    for action in action.menu().actions():
                        if action.menu():
                            for a in action.menu().actions():
                                if a.text():
                                    if a.text().lower() == label: return a
                        else:
                            if action.text():
                                if action.text().lower() == label: return action
                else:
                    if action.text():
                        if action.text().lower() == label: return action
        except Exception as e:
            self.info.err(e)

    def check_nodenames(self):
        try:
            iterator = QTreeWidgetItemIterator(self.tree)
            while iterator.value():
                item = iterator.value()
                nodename = item.text(0)
                items = self.tree.findItems(nodename, Qt.MatchExactly | Qt.MatchRecursive)
                if len(items) > 1:
                    self.info.err(None, "More as one node found!", nodename)
                iterator += 1
        except Exception as e:
            self.info.err(e)

    def runNode(self, nodename, expand=False, selected=True, excecute=True):
        try:
            items = self.tree.findItems(nodename, Qt.MatchExactly | Qt.MatchRecursive)
            if items is not None:
                if len(items) == 1:
                    item = items[0]
                    parent = item.parent()
                    while parent is not None:
                        parent.setExpanded(True)
                        parent = parent.parent()
                    if selected: self.tree.clearSelection()
                    item.setSelected(selected)
                    item.setExpanded(expand)
                    if excecute: self.node_onclick(item, 0)
                else:
                    self.info.err(None, "More as one node found!", nodename)
            else:
                self.info.log("node not found:", nodename)
        except Exception as e:
            self.info.err(e)

    def buildtree(self, parent, data, level, style):
        try:
            treefont = self.tree.font()  # default or set with qss
            # if self.debug: self.info.log('buildtree')
            if not data is None:
                if isinstance(data, list):
                    for d in data:
                        self.buildtree(None, d, level, style)
                else:
                    level = level + 1
                    visible = data.get('visible', True)
                    caption = data.get('caption', 'No Caption!')
                    icon = data.get('icon', None)
                    on_enter = data.get('on_enter', None)
                    on_exit = data.get('on_exit', None)
                    tools = data.get('tools', [])
                    children = data.get('children', [])
                    helptext = data.get('helptext', None)
                    if helptext is not None:
                        if helptext == "":
                            helptext = caption + ".htm"
                            if self.debug:
                                file = os.path.join(self.metadata.dirHelp, helptext)
                                text = 'Im tree.json Knoten "caption":{0} : "helptext":null setzen oder Datei editieren!'
                                text = text.format(caption)
                                self.helper.writeHTML(file, text)
                        else:
                            if not helptext.lower().endswith(".png"):
                                file = os.path.join(self.metadata.dirHelp, helptext)
                                if not os.path.exists(file):
                                    if self.debug:
                                        file = os.path.join(self.metadata.dirHelp, caption + ".htm")
                                        self.helper.writeHTML(file, helptext)
                                    helptext = caption + ".htm"
                            else:
                                if self.debug:  # copy *.png from gto/config
                                    src = os.path.join(self.metadata.dirConfig, helptext)
                                    if os.path.isfile(src):
                                        dest = os.path.join(self.metadata.dirHelp, helptext)
                                        shutil.copyfile(src, dest)
                    visibility = data.get('visibilty', {})
                    layer = data.get('layer', None)
                    tools_0 = data.get('tools_0', None)
                    tools_1 = data.get('tools_1', None)
                    twnode = QTreeWidgetItem()
                    # if self.debug:
                    #     twnode.setText(0, str(level) + "-" + caption)
                    # else:
                    #     twnode.setText(0, caption)
                    twnode.setText(0, caption)
                    # font
                    if style is not None:
                        try:
                            if children is None or len(children) == 0:  # workflow
                                level_style = style.get("workflow", None)
                            else:  # hierarachy
                                level_style = style.get("level" + str(level), None)
                            if level_style is None:
                                level_style = style.get("level" + str(level), None)
                            if level_style is not None:
                                family = level_style.get('family', treefont.family())
                                if family is None: family = treefont.family()
                                size = level_style.get('size', treefont.pointSize())
                                if size is None: size = treefont.pointSize()
                                weight = level_style.get('weight', treefont.weight())
                                if weight is None: weight = treefont.weight()
                                italic = level_style.get('italic', treefont.italic())
                                if italic is None: italic = treefont.italic()
                                bold = level_style.get('bold', treefont.bold())
                                if bold is None: bold = False
                                underline = level_style.get('underline', treefont.underline())
                                if underline is None: underline = False
                                # if self.debug: self.info.log(family, "/", size, "/", weight, "/", italic, "/", bold, "/", underline)
                                fo = QFont(family, size, weight, italic)
                                fo.setUnderline(underline)
                                fo.setBold(bold)
                                twnode.setFont(0, fo)
                                foreground = level_style.get('foreground', None)
                                background = level_style.get('background', None)
                                if foreground is not None: twnode.setForeground(0, QBrush(QColor(foreground)))
                                if background is not None: twnode.setBackground(0, QBrush(QColor(background)))
                        except Exception as e:
                            self.info.err(e)
                    # icon
                    iconfile = None
                    if icon == '':
                        icon = caption.lower() + ".ico"
                        iconfile = os.path.join(self.metadata.dirConfig)
                    else:
                        if icon is not None:
                            iconfile = os.path.join(self.metadata.dirConfig, icon)
                    # if self.debug: self.info.log("icon:", iconfile)
                    if iconfile is not None and os.path.exists(iconfile):
                        twnode.setIcon(0, QIcon(iconfile))

                    twnode.setData(1, 0, on_enter)
                    twnode.setData(2, 0, tools)
                    twnode.setData(3, 0, on_exit)
                    twnode.setData(4, 0, helptext)
                    twnode.setData(5, 0, visibility)
                    twnode.setData(6, 0, layer)
                    twnode.setData(7, 0, tools_0)
                    twnode.setData(8, 0, tools_1)
                    twnode.setData(9, 0, visible)
                    if parent is None:
                        self.tree.addTopLevelItem(twnode)
                    else:
                        parent.addChild(twnode)
                    # twnode.setHidden(not visible)  # must be already in view!
                    # if visible:
                    #     res = self.check_visibilty(visibility)
                    #     if res is not None:
                    #         twnode.setHidden(not res)
                    for child in children:
                        self.buildtree(twnode, child, level, style)
        except Exception as e:
            self.info.err(e)
            return

    def getInfoObject(self, logObject):
        return gtoInfo(logObject)

    def getTreeStyle(self):
        treestyle = None
        try:
            # read metadata
            file = os.path.join(self.metadata.dirConfig, 'tree_style.json')
            if os.path.isfile(file):
                f = io.open(file, encoding='utf-8')
                treestyle = json.load(f)
                f.close()
        except Exception as e:
            self.info.err(e)
        finally:
            return treestyle

    def styleQGIS(self):
        # QGIS style
        try:
            if self.qgis_stylefile is not None:
                file = os.path.join(self.metadata.dirStyles, self.qgis_stylefile)
                if self.debug: self.info.log("QGIS style file:", file)
                if os.path.isfile(file):
                    self.loadstyle(file)
        except Exception as e:
            self.info.err(e)
        # QGIS title
        try:
            if self.qgis_title is not None:
                title = self.qgis_title.replace('@version', Qgis.QGIS_VERSION)
                title = title.replace('@file', self.prj.absoluteFilePath())
                self.iface.mainWindow().setWindowTitle(self.qgis_title)
        except Exception as e:
            self.info.err(e)
        # QGIS icon
        try:
            if self.qgis_icon is not None:
                file = os.path.join(self.metadata.dirToolIcons, self.qgis_icon)
                if os.path.isfile(file):
                    icon = QIcon(file)
                    self.iface.mainWindow().setWindowIcon(icon)
        except Exception as e:
            self.info.err(e)

    def loadstyle(self, file):
        try:
            if file is not None:
                if os.path.isfile(file):
                    app = QApplication.instance()
                    f = open(file, "r")
                    qss_style = f.read()
                    f.close()
                    app.setStyleSheet(qss_style)
        except Exception as e:
            self.info.err(e)

    def setGTOtoolbar(self):
        if self.debug: self.info.log('setGTOtoolbar')
        self.gtotb.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.gtotb.setToolButtonStyle(self.toolbar_style)
        if self.toolbar_height is not None:
            self.gtotb.setMaximumHeight(self.toolbar_height)
            self.gtotb.setMinimumHeight(self.toolbar_height)
        else:
            self.gtotb.setMaximumHeight(100)
            self.gtotb.setMinimumHeight(0)
        try:
            self.iface.mainWindow().addToolBarBreak(self.toolbar_dock)  # default:  Qt::TopToolBarArea
            self.iface.addToolBar(self.gtotb, self.toolbar_dock)
            self.iface.mainWindow().addToolBarBreak(self.toolbar_dock)
            self.gtotb.setHidden(False)
            self.gtotb.setMovable(self.toolbar_moveable)
        except Exception as e:
            self.info.err(e)

    def setGTOwidget(self):
        try:
            # NoDockWidgetArea = 0
            # LeftDockWidgetArea = 1
            # RightDockWidgetArea = 2
            if self.dockwidget.isFloating():
                self.dockwidget.setFloating(False)
            self.iface.addDockWidget(self.gto_dock, self.dockwidget)
            flags = self.helper.getDockWidgetFeaturesFlags(self.gto_features)
            self.dockwidget.setFeatures(flags)
        except Exception as e:
            self.info.err(e)

    def setGTOtree(self):
        try:
            if self.tree_expand == 0:  # false
                pass
            elif self.tree_expand == 1:  # True
                self.tree.expandAll()
            elif self.tree_expand == -1:
                if self.tree.topLevelItemCount() == 1:
                    root = self.tree.topLevelItem(0)
                else:
                    root = self.tree.invisibleRootItem()
                child_count = root.childCount()
                for i in range(child_count):
                    item = root.child(i)
                    item.setExpanded(True)
            # iterator = QTreeWidgetItemIterator(self.tree)
            # while iterator.value():
            #     item = iterator.value()
            #     # item.setChildIndicatorPolicy(self.tree_showIndicator)
            #     iterator += 1

            # iface.iconSize(self, dockedToolbar: bool = False) → QSize
            # Returns the toolbar icon size. If dockedToolbar is true, the icon size for toolbars contained within docks is returned.
            self.tree.setIconSize(self.iface.iconSize(False))
            # if self.debug: self.info.err(None, "setGTOtree:iconsize:", self.tree.iconSize().width())

            if self.tree_indentation is not None:
                self.tree.setIndentation(self.tree_indentation)  # default: 20
        except Exception as e:
            self.info.err(e)

    def getInternalActions(self):  # create actions for some gto_commands
        actions = []  # list only for debug combo, actions are public
        try:
            mw = self.iface.mainWindow()  # parent of actions

            # for gto config
            act = QAction('mActionGTO' + 'addToolBarBreakTop', mw)
            act.setObjectName(act.text())
            act.setToolTip('Fügt Zeienumbruch für nächste Toolbar oben ein')
            act.triggered.connect(lambda: addToolBarBreakTop(self.gtomain, self.gtomain.debug))
            actions.append(act)

            act = QAction('mActionGTO' + 'addToolBarBreakBottom', mw)
            act.setObjectName(act.text())
            act.setToolTip('Fügt Zeienumbruch für nächste Toolbar unten ein')
            act.triggered.connect(lambda: addToolBarBreakBottom(self.gtomain, self.gtomain.debug))
            actions.append(act)

            # gps
            actgps = mw.findChild(QAction, 'mActionGTOgpsToggle')
            if actgps is not None:
                act = QAction("GPS activate", mw)
                act.setObjectName('mActionGTOgpsStart')
                act.setToolTip('GPS activate')
                act.triggered.connect(lambda: actgps.setChecked(True))
                actions.append(act)
                # ==
                act = QAction("GPS deactivate", mw)
                act.setObjectName('mActionGTOgpsStop')
                act.setToolTip('GPS deactivate')
                act.triggered.connect(lambda: actgps.setChecked(False))
                actions.append(act)

            act = mw.findChild(QAction, 'mActionGTOgpsAddPoint')
            if act is not None:
                actions.append(act)
            act = mw.findChild(QAction, 'mActionGTOgpsAddcPoint')
            if act is not None:
                actions.append(act)
            act = mw.findChild(QAction, 'mActionGTOgpsStream')
            if act is not None:
                actions.append(act)
            act = mw.findChild(QAction, 'mActionGTOgpsSave')
            if act is not None:
                actions.append(act)
            act = mw.findChild(QAction, 'GtoWidgetGpsPort')
            if act is not None:
                actions.append(act)
                act = mw.findChild(QAction, 'GtoWidgetGpsLog')
                if act is not None:
                    actions.append(act)
            act = mw.findChild(QAction, 'mActionGTOgpsAddVertexTool')
            if act is not None:
                actions.append(act)

            act = mw.findChild(QAction, 'mActionGTOgpsCenter')
            if act is not None:
                actions.append(act)

            # for users:
            act = QAction("GTO Oberfläche", mw)
            act.setObjectName('mActionGTOrestoreGTOui')
            act.setToolTip('GTO Oberfläche wieder herstellen')
            act.setIcon(self.gtomain.helper.getIcon('mActionGTOrestoreGTOui.png'))
            act.triggered.connect(self.restoreGTOui)
            actions.append(act)

            act = QAction("Attributetabellen schliessen", mw)
            act.setObjectName('mActionGTO' + 'closeQgisTabels')
            act.setIcon(self.gtomain.helper.getIcon('mActionGTOcloseQisTabels.png'))
            act.setToolTip('Alle QGIS Attributetabellen schliessen')
            act.triggered.connect(lambda: ClosePanel(self.gtomain, self.gtomain.debug, *['AttributeTable']))
            actions.append(act)

            act = QAction('Kartenansicht speichern', mw)
            act.setObjectName('mActionGTO' + 'saveMapSettings')
            act.setIcon(self.gtomain.helper.getIcon('mActionGTOsaveMapSettings.png'))
            act.setToolTip(act.text())
            act.triggered.connect(lambda: SaveMapSettings(self.gtomain, self.gtomain.debug))
            actions.append(act)

            act = QAction('Kartemansicht laden', mw)
            act.setObjectName('mActionGTO' + 'loadMapSettings')
            act.setIcon(self.gtomain.helper.getIcon('mActionGTOloadMapSettings.png'))
            act.setToolTip(act.text())
            act.triggered.connect(lambda: LoadMapSettings(self.gtomain, self.gtomain.debug))
            actions.append(act)

            act = QAction('Layerfilter', mw)
            act.setObjectName('mActionGTO' + 'showQueryBuilder')
            act.setIcon(self.gtomain.helper.getIcon('mActionGTOshowQueryBuilder.png'))
            act.setToolTip(act.text())
            act.triggered.connect(lambda: showQueryBuilder(self.gtomain, self.gtomain.debug))
            actions.append(act)

            act = QAction('Selektiere Kartenauschnitt', mw)
            act.setObjectName('mActionGTO' + 'selectByMapExtent')
            act.setToolTip(act.text())
            act.setIcon(self.helper.getIcon('mActionSelectFeaturesExtent.png'))
            act.triggered.connect(
                lambda: selectByMapExtent(self.gtomain, self.gtomain.debug, *[self.gtomain.iface.activeLayer().name()],
                                          **{}))
            actions.append(act)

            act = QAction('QGIS Attributetabelle', mw)
            act.setObjectName('mActionGTOopenQgisTable')
            act.setToolTip(act.text())
            act.setIcon(self.gtomain.helper.getIcon('mActionOpenTable.png'))
            act.triggered.connect(lambda: openAttributeTable(self.gtomain, self.gtomain.debug))
            actions.append(act)

            act = QAction('GTO Selektionstabelle', mw)
            act.setObjectName('mActionGTO' + 'openGtoTable')
            act.setToolTip(act.text())
            act.setIcon(self.gtomain.helper.getIcon('mActionGTOopenGtoTable.png'))
            act.setCheckable(True)
            act.toggled.connect(lambda *args: self.gtomain.helper.showGtoAttributeTable(args[0]))
            actions.append(act)

            # default gto-widgetactions

            act = GtoActionActiveLayer(self, mw)
            act.setToolTip('WidgetAction: Zeigt immer aktiven Layer an')
            actions.append(act)

            act = GtoActionLayerCombo(self, mw)
            act.setToolTip('WidgetAction: Zeigt/setzt aktiven Layer')
            actions.append(act)

            act = GtoActionVersion(self, mw)
            act.setToolTip('WidgetAction: Zeigt aktuelle GTO version')
            actions.append(act)

            act = GtoActionQgisVersion(self, mw)
            act.setToolTip('WidgetAction: Zeigt aktuelle QGIS version')
            actions.append(act)

            act = GtoActionHomepage(self, mw)
            act.setToolTip('WidgetAction: öffnet ms.GIS homepage')
            actions.append(act)

            act = GtoActionScale(self, mw)
            act.setToolTip('WidgetAction: Scale')
            actions.append(act)

            act = GtoActionProjectionSelection(self, mw)
            act.setToolTip('WidgetAction: Projection System')
            actions.append(act)

            act = GtoActionSpacer(self, mw)
            act.setToolTip('WidgetAction: Abstandshalter')
            actions.append(act)

            act = GtoActionQgisFile(self, mw)
            actions.append(act)
        except Exception as e:
            self.info.err(e)
        finally:
            return actions

    def watched_actions(self):
        try:
            # self.actionsWatched = []
            for a in self.iface.mainWindow().findChildren(QAction):
                try:
                    if not a in self.actionsWatched:
                        self.actionsWatched.append(a)
                        a.triggered.connect(self.debugObj.showTriggeredAction)
                except Exception as e:
                    self.info.err(e)
            for t in self.iface.mainWindow().findChildren(QToolBar):
                for w in t.findChildren(QToolButton):
                    try:
                        if w.defaultAction():
                            a = w.defaultAction()
                            if not a in self.actionsWatched:
                                self.actionsWatched.append(a)
                                a.triggered.connect(self.debugObj.showTriggeredAction)
                    except Exception as e:
                        self.info.err(e)
            for a in self.gtomain.gtoactions:
                if not a in self.actionsWatched:
                    self.actionsWatched.append(a)
                    a.triggered.connect(self.debugObj.showTriggeredAction)
        except Exception as e:
            self.info.err(e)

    def load_plugins(self):
        try:
            if self.debug:
                self.info.log("load_plugins:", self.gto_plugins)
                self.info.log("avasilable plugins:", utils.available_plugins)
            for plugin in utils.available_plugins:
                try:
                    if plugin in self.unload_plugins:
                        if plugin in utils.active_plugins:
                            # activate plugin
                            s = QSettings()
                            s.setValue("PythonPlugins/{0}".format(plugin), False)
                        if utils.isPluginLoaded(plugin):
                            utils.unloadPlugin(plugin)
                            self.info.log("unloaded plugin:", plugin)
                except Exception as e:
                    self.info.err(e)
                try:
                    if plugin in self.gto_plugins:
                        if self.debug: self.info.log("loading:", plugin)
                        if not plugin in utils.active_plugins:
                            # activate plugin
                            s = QSettings()
                            s.setValue("PythonPlugins/{0}".format(plugin), True)
                        if not utils.isPluginLoaded(plugin):
                            utils.loadPlugin(plugin)
                            utils.startPlugin(plugin)

                        # utils.startPlugin(plugin)
                        if self.debug: self.info.log("loaded:", plugin, utils.isPluginLoaded(plugin))
                except Exception as e:
                    self.info.err(e)
            utils.updateAvailablePlugins()
        except Exception as e:
            self.info.err(e)

    def set_tree_visibilty(self, layer):
        try:
            if self.debug: self.info.log('set_tree_visibilty:toolbars')
            if self.activeItem is not None:
                tools = self.getItemTools(self.activeItem)
                self.gtotb.addTools(tools)  # critical because of selection changed, but tollbar should not load again
                if not self.gtotb.hasTools():
                    self.gtotb.addTools(self.toolbar_no_tools)
            if self.debug: self.info.log('set_tree_visibilty:items visiblity')
            iterator = QTreeWidgetItemIterator(self.tree)
            while iterator.value():
                item = iterator.value()
                visible = item.data(9, 0)  # node should not be visible!
                if visible:
                    data = item.data(5, 0)  # "visibilty":{layername:-1/0/1}
                    res = self.check_visibilty(data, layer)
                    if res is not None:
                        item.setHidden(not res)
                else:
                    if self.debug: self.info.log("Knoten unsichtbar:", item.text(0))
                    item.setHidden(True)
                iterator += 1
        except Exception as e:
            self.info.err(e)

    def check_visibilty(self, visibilty, layer=None):
        try:
            if not visibilty: return  # empty dict
            if layer is None:
                key = next(iter(visibilty))
                layer = self.prj.mapLayersByName(key)[0]
            else:
                key = layer.name()
            if key in visibilty.keys():
                condition = visibilty[key]
                if self.debug: self.info.log("check_visibilty:condition:", condition)
                if condition == 0 and layer.selectedFeatureCount() == 0:
                    return True
                elif condition == 1 and layer.selectedFeatureCount() == 1:
                    return True
                elif condition == -1 and layer.selectedFeatureCount() > 1:
                    return True
                return False
        except Exception as e:
            self.info.err(e)

    def getItemTools(self, twnode=None):
        try:
            if twnode is None:
                twnode = self.activeItem
            tools = twnode.data(2, 0)
            layer = twnode.data(6, 0)

            if layer is not None:
                if self.debug: self.info.log("getItemTools:")
                try:
                    layer = self.prj.mapLayersByName(layer)[0]
                    tools_0 = twnode.data(7, 0)
                    tools_1 = twnode.data(8, 0)
                    if tools_0 is not None and layer.selectedFeatureCount() == 0:
                        return tools_0
                    elif tools_1 is not None and layer.selectedFeatureCount() == 1:
                        return tools_1
                except Exception as e:
                    self.info.err(e)
            return tools
        except Exception as e:
            self.info.err(e)
