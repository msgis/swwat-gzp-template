#!/usr/bin/python
# -*- coding: utf-8 -*-

from builtins import str

from PyQt5.QtCore import Qt, QObject, QSettings, QSize, QTimer
from PyQt5.QtWidgets import QApplication, QWidget, QToolBar, QAction, QDockWidget, QToolButton, QSizePolicy, QComboBox, \
    QCheckBox, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog, QMainWindow
from PyQt5.QtGui import QKeySequence

from qgis.core import Qgis, QgsDataSourceUri, QgsProject

from .gto_commands import FindLayer, TabWidget
from .gto_info import gtoInfo
from .gto_qsettings import GtoQgisSettingsDialog
from .mActionGTOcommands import *
from .mActionGTOgui import run as mActionGTOunlockUI
from .gto_actions import GtoActionLayerCombo

import os


class gtoDebug(QObject):
    def __init__(self, gtomain):
        super(gtoDebug, self).__init__()
        self.setObjectName(__name__)
        # references
        self.debug = True
        self.gtomain = gtomain
        self.metadata = gtomain.metadata
        self.info = gtoInfo(self)

        self.iface = gtomain.iface
        self.helper = self.gtomain.helper
        self.objName = "gtoTB_debug"
        self.caption = "GTO " + self.gtomain.helper.getGTOversion()
        self.timer = QTimer()
        # references
        self.caller = None
        self.actionClicked = None
        self.actionsWatched = []
        self.settings = QSettings()
        # toolbar
        self.toolbar_style = Qt.ToolButtonIconOnly
        self.toolbar_dock = Qt.TopToolBarArea
        self.toolbar = None
        self.actionCombo = None
        self.ComboShowClicked = None

    def start_debug(self):
        try:
            self.info.log("createDebugTB")
            # load toolbar
            self.toolbar = self.helper.findToolbar(self.iface, self.objName)
            if self.toolbar is not None:
                self.toolbar = None
            if self.toolbar is None:
                self.toolbar = self.helper.getToolBar(self, self.objName, self.caption, self.iface.mainWindow())
                self.iface.mainWindow().addToolBarBreak(self.toolbar_dock)  # default:  Qt::TopToolBarArea
                self.iface.addToolBar(self.toolbar, self.toolbar_dock)
                self.iface.mainWindow().addToolBarBreak(self.toolbar_dock)
            self.toolbar.setHidden(False)
            self.toolbar.clear()
            # add tools
            self.actionCombo = GtoActionCombo(self)
            self.toolbar.addWidget(self.actionCombo)

            self.actionClicked = self.addAction('Copy clicked +', None,
                                                self.helper.getIcon('copy.png'))  # self.showClicked)
            self.actionClicked.setCheckable(True)
            # self.watched_actions()

            self.ComboShowClicked = QCheckBox()
            self.ComboShowClicked.setIcon(self.helper.getIcon('json.png'))
            self.ComboShowClicked.setIconSize(self.toolbar.iconSize())
            self.toolbar.addWidget(self.ComboShowClicked)

            self.addAction('Reload GTO ' + self.helper.getGTOversion(), self.reloadGTO, self.helper.getIcon('gto.png'))
            self.addAction('Save GTO UI', self.gtomain.storeGTOui, self.helper.getIcon('mActionGTOsaveGUI.png'))
            self.addAction('Standard UI QGIS ' + Qgis.QGIS_VERSION, self.restore_debug_qgis,
                           self.helper.getIcon('qgis.png'))
            self.addAction('Python ' + sys.version, self.showPythonConsole, self.helper.getIcon('mActionShowPythonDialog.png'))
            self.addAction('Log', self.ShowMessageLog, self.helper.getIcon('mActionGTOmessagelogShow.png'))
            self.addAction('Cear log', lambda: run_command(self.gtomain, self.gtomain, None, 'ClearMessageLog'),
                           self.helper.getIcon('mActionGTOmessagelogClear.png'))

            act = self.addAction('Find layer', lambda: FindLayer(self, True), self.helper.getIcon('findlayer.png'))
            self.addAction('Qgis Settings', lambda: GtoQgisSettingsDialog(self.gtomain, self.iface.mainWindow()).show(),
                           self.helper.getIcon('settings.png'))
            self.addAction('Connection info active layer', self.show_dbcon_activelayer,
                           self.helper.getIcon('daatabaseconnection.png'))
            self.addAction('Qgis Style', self.loadQGISstyle, self.helper.getIcon('css.png'))

            self.toolbar.addAction(GtoActionLayerCombo(self, self.iface.mainWindow()))
            self.toolbar.addAction(self.iface.actionSelect())
            act = self.addAction("run ./gto/scripts/example.py",
                                 lambda: run_command(self.gtomain, self.gtomain, "example.py", "run_script"),
                                 self.helper.getIcon('execute.png'))
            act = self.addAction('Unlock UI', None,
                                 self.helper.getIcon(
                                     'mActionGTOunlockUI.png'))
            act.setCheckable(True)
            act.setObjectName('mActionGTOlockUI_toggle')
            if self.gtomain.dockwidget.features() != QDockWidget.AllDockWidgetFeatures:
                act.setChecked(True)
                act.setIcon(self.helper.getIcon('mActionGTOlockUI.png'))
            act.toggled.connect(self.unlock_gui)
            self.iface.mainWindow().addAction(act)
            act = self.gtomain.findAction("mActionQGISversion")
            act = self.toolbar.addAction(act)
            # spacer = QWidget()
            # spacer.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Expanding)
            # spacer.setStyleSheet("QWidget{background: transparent;}")
            act = self.helper.addToolbarClose(self.toolbar)
            act.setToolTip("toggle (F9)")
            # act.setShortcut(Qt.Key_F9)
            # act.setShortcut(QKeySequence('Ctrl+F9'))
            act.setShortcut(QKeySequence('F9'))
            self.iface.mainWindow().addAction(act)
            self.toolbar.setToolButtonStyle(self.toolbar_style)
            self.toolbar.setVisible(True)
            self.ShowMessageLog()
            # self.watched_actions()
        except Exception as e:
            self.info.err(e)

    def restore_debug_qgis(self):
        try:
            self.gtomain.qgis.restoreQGISui(True)
            self.iface.mainWindow().addToolBarBreak(self.toolbar_dock)
            self.iface.addToolBar(self.toolbar, self.toolbar_dock)
            self.iface.mainWindow().addToolBarBreak(self.toolbar_dock)
        except Exception as e:
            self.info.err(e)

    def unlock_qgis_gui(self):
        try:
            mActionGTOunlockUI(0, self, {}, self.debug)
            # == mActionGTOgui, 0=dummy, no config =>default (all unlock)
        except Exception as e:
            self.info.err(e)

    def unlock_gui(self):
        try:
            act = self.sender()
            if not act.isChecked():  # lock=>unlock
                if self.debug: self.info.log('unlock_gui:', act.isChecked())
                self.unlock_qgis_gui()
                act.setIcon(self.helper.getIcon('mActionGTOunlockUI.png'))
            else:  # unlock=>lock
                if self.debug: self.info.log('unlock_gui:', act.isChecked())
                if self.gtomain.runcmd('mActionGTOgui1'):
                    act.setIcon(self.helper.getIcon('mActionGTOlockUI.png'))
                else:
                    act.setChecked(False)
        except Exception as e:
            self.info.err(e)
        finally:
            if self.debug: self.info.log('unlock_gui: finally:', act.isChecked())

    def addAction(self, caption, callback, icon=None):
        action = QAction(self.gtomain)
        action.setText(caption)
        if icon is not None:
            action.setToolTip(caption)
            action.setIcon(icon)
        action.setObjectName('mActionGTOdebug' + str(id))
        if callback is not None: action.triggered.connect(callback)
        self.toolbar.addSeparator()
        self.toolbar.addAction(action)
        return action

    def watched_actions(self):
        try:
            return
            for a in self.iface.mainWindow().findChildren(QAction):
                if a.parent() != self.toolbar:
                    try:
                        if not a in self.actionsWatched:
                            self.actionsWatched.append(a)
                            a.triggered.connect(self.showTriggeredAction)
                    except Exception as e:
                        self.info.err(e)
            for t in self.iface.mainWindow().findChildren(QToolBar):
                if not (t == self.toolbar):
                    for w in t.findChildren(QToolButton):
                        try:
                            if w.defaultAction():
                                a = w.defaultAction()
                                if not a in self.actionsWatched:
                                    self.actionsWatched.append(a)
                                    a.triggered.connect(self.showTriggeredAction)
                        except Exception as e:
                            self.info.err(e)
            for a in self.gtomain.gtoactions:
                if not a in self.actionsWatched:
                    if not a in self.actionsWatched:
                        self.actionsWatched.append(a)
                        a.triggered.connect(self.showTriggeredAction)
        except Exception as e:
            self.info.err(e)

    def showTriggeredAction(self, action=None):
        try:
            action = self.sender()
            obj_name = "None"
            obj_text = "None"
            try:
                obj_name = action.objectName()
            except:
                pass
            try:
                obj_text = action.text()
            except:
                pass
            self.info.log("Triggered action: object name:", obj_name, "caption:", obj_text)
            if action.objectName() and self.actionClicked.isChecked():  # not self.actionClicked.isEnabled():
                self.helper.copyToClipboard(',"{0}"'.format(action.objectName()))
                text, number = self.helper.splitStringNummeric(action.objectName())
                file = os.path.join(self.metadata.path_tools, text + ".json")
                self.info.log("action config:", self.helper.shortDisplayText(file))
                if os.path.isfile(file) and self.ComboShowClicked.isChecked(): os.startfile(file)
                if action.icon() is not None:
                    icon = action.icon()
                    pixmap = icon.pixmap(icon.actualSize(QSize(1024, 1024)))

                    path = os.path.join(os.path.dirname(__file__), "icons_copy_clicked")
                    if not os.path.exists(path): os.mkdir(path)

                    # objName, number = self.helper.splitStringNummeric(action.objectName())
                    objName = action.objectName()
                    file = os.path.join(path, objName)

                    savefile = file + ".svg"
                    if not os.path.isfile(savefile):
                        if pixmap.save(savefile):
                            self.info.log("icon saved:", self.helper.shortDisplayText(file))
                        else:
                            savefile = file + ".png"
                            if not os.path.isfile(savefile):
                                if pixmap.save(savefile):
                                    self.info.log("icon saved:", self.helper.shortDisplayText(file))
            # self.actionClicked.setEnabled(True)
        except Exception as e:
            self.info.err(e)

    def reloadGTO(self):
        try:
            run_command(self.gtomain, self.gtomain, None, 'ClearMessageLog')
            self.toolbar = None
            self.gtomain.info.do_backup()
            self.gtomain.loadgto(True)
            self.iface.mainWindow().addToolBarBreak()  # default:  Qt::TopToolBarArea
        except Exception as e:
            self.info.err(e)
        finally:
            QApplication.restoreOverrideCursor()

    def loadQGISstyle(self):
        try:
            dlg = QFileDialog()
            # dlg.setFileMode(QFileDialog.ExistingFile)
            # dlg.setFilter("Style sheets (*.qss)")
            file, filefilter = dlg.getOpenFileName(self.iface.mainWindow(), 'Load QGIS style sheet',
                                                   directory=self.metadata.dirStyles,
                                                   filter="Style sheets (*.qss)")
            self.info.log("loadQGISstyle:", file)
            QApplication.setOverrideCursor(Qt.CrossCursor)
            self.gtomain.loadstyle(file)
            QApplication.restoreOverrideCursor()
        except Exception as e:
            self.info.err(e)

    def ShowMessageLog(self):
        try:
            self.iface.openMessageLog()
            mdw = self.iface.mainWindow().findChild(QDockWidget, 'MessageLog')
            mdw.setHidden(False)
            pdw = self.iface.mainWindow().findChild(QDockWidget, 'PythonConsole')
            if pdw is not None and pdw.isVisible():
                TabWidget(self, self.debug, [mdw, pdw])
                for tb in pdw.findChildren(QToolBar):
                    tb.setHidden(False)
        except Exception as e:
            self.info.err(e)

    def showPythonConsole(self):
        try:
            pdw = self.iface.mainWindow().findChild(QDockWidget, 'PythonConsole')
            if pdw is None:
                self.iface.actionShowPythonDialog().trigger()
            pdw = self.iface.mainWindow().findChild(QDockWidget, 'PythonConsole')
            pdw.setHidden(False)
            for tb in pdw.findChildren(QToolBar):
                tb.setHidden(False)
        except Exception as e:
            self.info.err(e)

    def show_dbcon_activelayer(self):
        try:
            # rdbms = self.helper.importModule('mActionGTOrdbms').run( 0, self, {}, True)
            layer = self.iface.activeLayer()
            provider = layer.dataProvider()
            provider_name = provider.name()
            uri = QgsDataSourceUri(provider.dataSourceUri())
            text = "Layer <{0}> connection info:\n\n".format(layer.name())
            text = text + "provider name: " + provider_name + "\n"
            text = text + "host: " + str(uri.host()) + "\n"
            text = text + "database name: " + str(uri.database()) + "\n"
            text = text + "port: " + str(uri.port()) + "\n"
            text = text + "user name: " + str(uri.username()) + "\n"
            text = text + "user password: " + str(uri.password())
            # db, sql = rdbms.getDatabase(provider_name, "procedure")
            # db.setHostName(uri.host())
            # db.setDatabaseName(uri.database())
            # try:  # uri.port could be ''
            #     db.setPort(int(uri.port()))
            # except Exception as e:
            #     self.info.err(e, 'Invalid port number')
            # db.setUserName(uri.username())
            # db.setPassword(uri.password())
            # text = rdbms.con_info()
            self.info.msg(text, parent=self.iface.mainWindow())
        except Exception as e:
            self.info.err(e)


class GtoActionCombo(QComboBox):
    def __init__(self, gtoObj, parent=None):
        super(GtoActionCombo, self).__init__(parent)
        self.gtoObj = gtoObj
        self.gtomain = self.gtoObj.gtomain
        self.helper = self.gtoObj.helper
        self.info = self.gtoObj.info
        self.key_lastcmd = "debug/lastcmd"
        self.debug = self.gtomain.debug

        try:
            self.setEditable(True)
            self.setInsertPolicy(self.NoInsert)
            self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            self.setMinimumContentsLength(25)
            self.setToolTip('Default GTO actions')
            self.lineEdit().setPlaceholderText("ActionObjectName + [enter]")
            # init
            index = 0
            for action in self.gtomain.internalActions:
                self.addItem(action.objectName())
                tooltip = action.toolTip()
                if action.toolTip() is None or action.toolTip() == '':
                    tooltip = action.text()
                self.setItemData(index, tooltip, Qt.ToolTipRole)
                index = index + 1
            self.model().sort(0, Qt.AscendingOrder)
            self.setCurrentIndex(-1)
            # self.currentIndexChanged.connect(self.runAction)
            self.activated.connect(self.runAction)
            self.setCurrentText(self.helper.getSetting(self.key_lastcmd))
        except Exception as e:
            self.info.err(e)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Return:
            self.runAction()
        else:
            QComboBox.keyPressEvent(self, e)

    def runAction(self):
        try:
            text = self.currentText()
            if text == '':
                self.open_tree_config()
            else:
                text = text.replace(",", '')
                text = text.replace('"', '')
                res = self.gtomain.runcmd(text)
                if res:
                    self.helper.copyToClipboard(',"{0}"'.format(text))
                    if self.findText(text, Qt.MatchExactly) == -1:
                        self.helper.setSetting(self.key_lastcmd, text)
                else:
                    self.info.msg("{0} not found!".format(text))
                    self.open_tree_config()
        except Exception as e:
            self.info.err(e)

    def open_tree_config(self):
        try:
            path = os.path.join(QgsProject.instance().absolutePath(), self.gtomain.metadata.dirConfig)
            file = os.path.join(path, "tree.json")
            # if self.debug: self.info.err(None, file)
            os.startfile(file)
        except Exception as e:
            self.info.err(e)
