# -*- coding: utf-8 -*-
from builtins import str
from builtins import range
from PyQt5.QtCore import Qt, QSettings, QTranslator, qVersion, QCoreApplication, QObject, QFile, QTextStream
from PyQt5.QtGui import QIcon,QPixmap
from PyQt5.QtWidgets import QAction,QDockWidget,QToolBar,QWidgetAction,QTreeWidgetItem

import os.path
import json
from qgis.core import QgsProject
from qgis.gui import QgsMapCanvas, QgsMapToolZoom

import io

from .gto_info import gtoInfo
from .gto_tools import gtoTools
from .gto_remote import gtoRemote
from .gto_commands import *
from .gto_debug import *
from .gto_helper2 import gtoHelper
from .gto_listener import gtoListener
from .gto_identify import IdentifyTool

class gtoMain(QObject):
    def __init__(self,gtoplugin, parent = None):
        super(gtoMain,self).__init__(parent)
        self.setObjectName(__name__)

        #references
        self.gtoplugin = gtoplugin
        self.metadata = self.gtoplugin.metadata
        self.helper = gtoHelper(self)
        self.info = gtoInfo(self)
        self.info.log("GTO loaded")  # this text is detected in clearMessageLog
        self.debug = gtoplugin.debug
        self.iface = self.gtoplugin.iface
        self.gtotb = gtoplugin.gtotb
        self.indentifyTool = IdentifyTool(self.iface.mapCanvas())
        #self.touchextend = TouchExtend(self,self.iface.mapCanvas())


        try:
            if self.debug: self.info.log("__init__")
            self.gtotools = gtoTools(self)
            self.prj = qgis.core.QgsProject.instance()
            self.homepath = self.gtoplugin.plugin_dir
            self.gtoactions = []
            self.dockwidget = self.gtoplugin.dockwidget
        except Exception as e:
            self.info.err(e)

        # status vars
        try:
            self.lastnode = None
            self.remote = None
            self.gto_stylefile = None

            #Tree
            self.tree = self.dockwidget.treeWidget
            self.tree.setHeaderHidden(True)
            self.tree.setItemsExpandable(True)
            self.tree.setColumnCount(1)
            self.tree.clear()

            #logo
            self.label_info = self.dockwidget.label_Info
            self.label_info.clear()
            self.scrollArea_Info = self.dockwidget.scrollArea_Info
        except Exception as e:
            self.info.err(e)

        #gto sizing
        try:
            s = QSettings()
            iconsize = int(s.value('IconSize', 24))#fit it to qgis settings
            self.tree.setIconSize(QSize(iconsize, iconsize))
            self.dockwidget.setMinimumWidth(10 * iconsize)
            self.splitter = self.dockwidget.splitter
        except Exception as e:
            self.info.err(e)

        try:
            #signals
            self.tree.itemClicked.connect(self.node_onclick)
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)
        except Exception as e:
            self.info.err(e)

    def loadgto(self):
        try:
            if self.debug: self.info.log("loadgto")
            if self.remote is not None:
                self.remote.unload()
            #set pathes

            self.path = self.gtoplugin.plugin_dir
            if self.prj is not None:
                if self.prj.homePath() is not None:
                        self.metadata.initProject(self.prj.homePath())
                        self.homepath = self.prj.homePath()
            self.path_metadata =self.metadata.dirMetadata# self.homepath + "/gto/gto_config"
            self.path_tools=self.metadata.dirTools# self.homepath + "/gto/gtotools_config"
            self.path_icons= self.metadata.dirToolIcons # self.path_tools + "/gto/icons"
            #settings default
            tree_expand = True
            gto_startuptools = []
            treestyle = None
            #GUI stuff
            self.tree.clear()
            if self.gtotb is not None:
                self.gtotb.clear()
                if not self.debug: self.gtotb.setHidden(True)
            #get actions
            self.gtoactions[:] = []#clear list
            if os.path.exists(self.path_tools):
                self.gtoactions.extend(self.gtotools.getGTOaction(self.path_tools))
            # read metadata
            if os.path.isfile(self.path_metadata + "/tree_style.json"):
                f = io.open(self.path_metadata + "/tree_style.json", encoding='utf-8')
                treestyle = json.load(f)
                f.close()
            if os.path.isfile(self.path_metadata + "/tree.json"):
                f = io.open(self.path_metadata + "/tree.json", encoding='utf-8')
                data = json.load(f)
                f.close()
                if self.debug: self.info.log('buildtree (recursive)')
                self.buildtree(None, data, -1, treestyle)
        except Exception as e:
            self.info.err(e)
        # gui settings
        try:
            # set default:
            self.gtotb.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            if self.dockwidget.isFloating():
                self.dockwidget.setFloating(False)
            self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dockwidget)
            # self.dockwidget.setStyleSheet("QWidget {background: white;color: #004489;border: 0px solid #FDC613;border-radius: 4px;}"
            #                             "QSpliiter {border: 0px;}QScrollArea {border: 1px solid #FDC613;}"
            #                             "QTreeWidget {border: 1px solid #FDC613; font-size: 16px;font-style: bold;}"
            #                             "QTreeWidget::item:selected {background:   #004489;color: #FDC613;}"
            #                             "QLabel {border: 0px;}")
            self.label_info.clear()
        except Exception as e:
            self.info.err(e)
        try:
            self.settings = {}
            filename = self.path_metadata + "/settings.json"
            if os.path.isfile(filename):
                if self.debug: self.info.log('gui setting:', filename)
                # get settings
                f = io.open(filename, encoding='utf-8')
                self.settings = json.load(f)
                f.close()
                # start remote watch
                self.remote = gtoRemote(self)
                #start event listener
                self.listener = gtoListener(self)
                ignore = False#Kompatibiltätsgründe
                try:
                    logo_height = self.settings.get('logo_height', 200)
                    if self.debug: self.info.log("logo_height: ",logo_height)
                    if logo_height < 100:
                        self.splitter.setStretchFactor(0,logo_height)
                        #stretch is not the effective stretch factor;
                        #the effective stretch factor is calculated by taking the initial size of the widget and multiplying it with stretch.
                    else:
                        self.splitter.setSizes([logo_height,500])  # 2nd value is just dummy,because its docked'
                        # If the splitter is vertical, the height of each widget is set, from top to bottom.
                except Exception as e:
                    self.info.err(e)

                try:
                    ignore = self.settings['ignore']
                except:
                    pass
                self.gto_stylefile = checkFileExists(self.settings['gto_stylefile'],self.path_metadata)
                gto_dock = self.settings['gto_dock']
                toolbar_style = self.settings['toolbar_style']
                #gto_showlabel = settings['gto_showlabel']
                try:
                    tree_expand = self.settings['tree_expand']
                except:
                    tree_expand = True

                if ignore is None: ignore = True
                if not ignore:
                    gto_startuptools = self.settings['gto_startuptools']
                    #gto toolbar
                    # Qt.ToolButtonIconOnly = 0
                    # Qt.ToolButtonTextOnly = 1
                    # Qt.ToolButtonTextBesideIcon = =2
                    # Qt.ToolButtonTextUnderIcon = 3
                    # Qt.ToolButtonFollowStyle = 4
                    self.gtotb.setToolButtonStyle(toolbar_style)
                    try:
                        toolbar_dock = self.settings['toolbar_dock']
                        #self.gtotb.setAllowedAreas(toolbar_dock)
                        self.iface.addToolBar(self.gtotb, toolbar_dock)
                    except Exception as e:
                        self.info.err(e)
                    #gto dockwidget
                    if self.gto_stylefile is not None:
                        try:
                            if self.debug: self.info.log("stylefile:",self.gto_stylefile)
                            f = QFile(self.gto_stylefile)
                            f.open(QFile.ReadOnly | QFile.Text)
                            ts = QTextStream(f)
                            stylesheet = ts.readAll()
                            self.dockwidget.setStyleSheet(stylesheet)
                        except Exception as e:
                            if self.debug: self.log(e.args)
                    #NoDockWidgetArea = 0
                    #LeftDockWidgetArea = 1
                    #RightDockWidgetArea = 2
                    if gto_dock is None: gto_dock = 1
                    if gto_dock == 0:
                        self.dockwidget.setFloating(True)
                    else:
                        self.dockwidget.setFloating(False)
                        self.iface.addDockWidget(gto_dock, self.dockwidget)
                    #imglabel
                    #self.scrollArea_Info.setHidden(not gto_showlabel)
            else:
                pass
        except Exception as e:
            self.info.err(e)
        try:
            TabWidget(self,self.debug, self.dockwidget)
        except:
            pass

        self.ShowPicture(self.settings.get("logo",None))

        # Show the result
        self.dockwidget.show()
        if tree_expand:
            self.tree.expandAll()
        else:
            root = self.tree.invisibleRootItem()
            child_count = root.childCount()
            for i in range(child_count):
                item = root.child(i)
                if item.parent() is None: item.setExpanded(True)
        #run the startuptools
        self.runcmd(gto_startuptools)
        #debug mode
        if self.debug: self.gto_debugtb = createDebugTB(self)

    def onClosePlugin(self):
        if self.gtotb is not None:
            if not self.debug: self.gtotb.setHidden(True)

    def node_onclick(self, Item, Index):#QTreeWidgetItem
        if self.debug: self.info.log('node_onclick')
        #empty qgs
        try:
            if self.prj.homePath() == '':
                self.tree.clear()
                self.gtotb.clear()
                self.label_info.clear()
        except:
            pass
        #on exit support
        try:
            if self.lastnode is not None:
                items = self.tree.findItems(self.lastnode, Qt.MatchExactly | Qt.MatchRecursive)
                if items is not None:
                    if len(items) > 0:
                        lastitem = items[0]
                        if lastitem.text(0) != Item.text(0):
                            if self.debug:self.info.log("Last node: ", lastitem.text(0),"new node: ",Item.text(0))
                            cmd = lastitem.data(3, 0)
                            if self.debug: self.info.log('on_exit:', cmd)
                            retval = self.runcmd(cmd)
                            self.label_info.setText('')
                            if retval is not None:
                                if not retval:
                                    pass#for further ideas
        except Exception as e:
            self.info.err(e)
        try:
            self.lastnode = Item.text(0)
            if self.debug: self.info.log('node_onclick:', self.lastnode)
            #helptext
            helptext =Item.data(4, 0)
            self.label_info.clear()
            if helptext is not None:
                #if its a file, load the content
                helpfile = checkFileExists(helptext, self.path_metadata)
                if helpfile is not None:
                    try:
                        if helpfile.lower().endswith(".png"):
                            if self.debug: self.info.log(helpfile)
                            self.ShowPicture(helpfile)
                        else:
                            f = open(helpfile)
                            helptext = f.read()
                            f.close()
                            self.ShowHelpText(helptext)
                    except IOError as e:
                        self.label_info.setText(e.args)
                else:
                    self.ShowHelpText(helptext)
            else:
                self.ShowPicture(self.settings.get( "logo", None))
            # run command(s)
            cmd = Item.data(1, 0)
            self.runcmd(cmd)
            #set toolbar
            if self.debug: self.info.log('set toolbar')
            if self.gtotb is not None:#should never happen
                self.gtotb.clear()#remove all actions
                #if Item.childCount() == 0:
                tools = Item.data(2, 0)
                if len(tools) == 0:
                    #lbl = QLabel('Tools not set!')
                    #self.gtotb.addWidget(lbl)
                    action = self.findAction('mActionGTOmsgis')
                    self.gtotb.addAction(action)
                else:
                    for t in tools:
                        tname = t.lower()
                        if tname == "separator":
                            self.gtotb.addSeparator()
                            if self.debug: self.info.log('set toolbar:Add: separator')
                        else:
                            # if self.debug: self.info.log('node_onclick: search action')
                            action = self.findAction(tname)
                            if action is not None:
                                self.gtotb.addAction(action)
                self.gtotb.setHidden(False)
            else:
                self.info.gtoWarning('No GTO toolbar!')
        except Exception as e:
            self.info.err(e)

    def ShowPicture(self, path):
        try:
            if self.debug: self.info.log('ShowPicture',path)
            self.label_info.clear()
            if path is not None and os.path.isfile(path):
                if self.debug: self.info.log('ShowPicture', 'load the image')
                img = QPixmap(path)
                h = self.label_info.height()-5
                w = self.label_info.width()-5
                #self.label_info.setPixmap(img.scaled(w,h,Qt.KeepAspectRatio))
                self.label_info.setPixmap(img)
                self.label_info.setMask(img.mask())
                self.scrollArea_Info.setHidden(False)
                self.scrollArea_Info.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                self.scrollArea_Info.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            else:
                self.scrollArea_Info.setHidden(True)
                self.scrollArea_Info.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
                self.scrollArea_Info.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        except Exception as e:
            self.info.err(e)

    def ShowHelpText(self,helptext):
        self.label_info.setText("")
        try:
            self.label_info.setText(helptext)
            self.scrollArea_Info.setVisible(True)
            self.scrollArea_Info.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.scrollArea_Info.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        except Exception as e:
            self.info.err(e)

    def runcmd(self,value):
        try:
            if self.debug: self.info.log('runcmd')
            if value is None: return
            if isinstance(value, str):
                value=[value]
            if isinstance(value, list):
                cmds = value
                for cmd in cmds:
                    if len(cmd) > 0:
                        action = self.findAction(cmd)
                        if action is not None:
                            action.trigger()
            else:
                if self.debug: self.info.log('runcmd: no string or list')
        except Exception as e:
            self.info.err(e)

    def findAction(self, objName):
        try:
            if self.debug: self.info.log('findAction', objName)
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
        # try:
        #     if self.debug: self.info.log('findAction', objName)
        #     toolbars = self.iface.mainWindow().findChildren(QToolBar)
        #     found = self.findAction2(objName)
        #     if found: return found
        #     for toolbar in toolbars:
        #         for action in toolbar.actions():
        #             if isinstance(action, QWidgetAction):
        #                 if action.defaultWidget() and action.defaultWidget().actions():
        #                     dwa = action.defaultWidget().actions()
        #                     for a in dwa:
        #                         if self.IsSearchedAction(a,objName):return a
        #             else:
        #                 if self.IsSearchedAction(action, objName): return action
        #     menubar = self.iface.mainWindow().menuBar()
        #     for action in menubar.actions():
        #         if action.menu():
        #             for action in action.menu().actions():
        #                 if action.menu():
        #                     for a in action.menu().actions():
        #                         if self.IsSearchedAction(a, objName): return a
        #                 else:
        #                     if self.IsSearchedAction(action, objName): return action
        #         else:
        #             if self.IsSearchedAction(action, objName): return action
        #     for action in self.gtoactions:
        #         if self.IsSearchedAction(action, objName): return action
        #     if self.debug: self.info.log('findAction: ', objName, 'not found!' )
        #     return None
        # except Exception as e:
        #     self.info.err(e)

    def findActionByObjectName(self, objname):
        try:
            toolbars = self.iface.mainWindow().findChildren(QToolBar)
            for toolbar in toolbars:
                for action in toolbar.actions():
                    if action.objectName():
                        if action.objectName().lower() == objname.lower(): return action
                    if action.actionGroup() is not None:
                        for a in action.actionGroup().actions():
                            if a.objectName():
                                if a.objectName().lower() == objname.lower(): return a
            menubar = self.iface.mainWindow().menuBar()
            for action in menubar.actions():
                if action.menu():
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
            menubar = self. iface.mainWindow().menuBar()
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

    # def IsSearchedAction(self,action, objname):
    #     try:
    #         objname = objname.lower()
    #         caption = action.text()
    #         caption = caption.replace("&", "")
    #         caption = caption.replace(".", "")
    #         caption = caption.strip()
    #         caption= caption.lower()
    #         return action.objectName().lower() == objname or caption == objname
    #     except Exception as e:
    #         self.info.err(e)

    def runNode(self, nodename):
        try:
            items = self.tree.findItems(nodename, Qt.MatchExactly | Qt.MatchRecursive)
            if items is not None:
                if len(items) > 0:
                    item = items[0]
                    parent = item.parent()
                    while parent is not None:
                        parent.setExpanded(True)
                        parent = parent.parent()
                    item.setSelected(True)
                    self.node_onclick(item,0)
            else:
                self.info.log("node not found:", nodename)
        except Exception as e:
            self.info.err(e)

    def buildtree(self, parent, data, level, style):
        treefont = self.tree.font()#default or set with qss
        try:
            if self.debug: self.info.log('buildtree')
            if not data is None:
                if isinstance(data,list):
                    for d in data:
                        self.buildtree(None, d,level, style)
                else:
                    level = level +1
                    caption = data['caption']
                    icon = data['icon']
                    on_enter = data['on_enter']
                    on_exit = data['on_exit']
                    tools = data['tools']
                    children = data ['children']
                    helptext = None
                    try:
                        helptext = data['helptext']
                    except:
                        pass
                    twnode = QTreeWidgetItem()
                    if self.debug:
                        twnode.setText(0, str(level) + "-" + caption)
                    else:
                        twnode.setText(0, caption)
                    #font
                    if style is not None:
                        try:
                            if children is None or len(children) ==0: #workflow
                                level_style = style.get("workflow", None)
                            else: #hierarachy
                                level_style = style.get("level" + str(level), None)
                            if level_style is None:
                                level_style= style.get("level" + str(level),None)
                            if level_style is not None:
                                family = level_style.get('family',treefont.family())
                                if family is None: family = treefont.family()
                                size= level_style.get('size',treefont.pointSize())
                                if size is None: size = treefont.pointSize()
                                weight = level_style.get('weight',treefont.weight())
                                if weight is None: weight = treefont.weight()
                                italic = level_style.get('italic',treefont.italic())
                                if italic is None: italic=treefont.italic()
                                bold =  level_style.get('bold',treefont.bold())
                                if bold is None: bold = False
                                underline =  level_style.get('underline',treefont.underline())
                                if underline is None: underline = False
                                if self.debug: self.info.log(family,"/",size,"/",weight,"/",italic,"/",bold,"/",underline)
                                fo=QFont(family,size,weight,italic)
                                fo.setUnderline(underline)
                                fo.setBold(bold)
                                twnode.setFont(0, fo)
                                foreground = level_style.get('foreground', None)
                                background = level_style.get('background', None)
                                if foreground is not None: twnode.setForeground(0, QBrush(QColor(foreground)))
                                if background is not None: twnode.setBackground(0, QBrush(QColor(background)))
                                #twnode.setSizeHint(0,QSize(48,48))
                        except Exception as e:
                            self.info.err(e)
                    #icon
                    iconfile = None
                    if icon == '':
                        icon = caption.lower() + ".ico"
                        iconfile =os.path.join( self.path_metadata,icon)
                    else:
                        if icon is not None:
                            iconfile= os.path.join(self.path_metadata,icon)
                    if self.debug: self.info.log("icon:",iconfile)
                    if iconfile is not None and os.path.exists(iconfile):
                        twnode.setIcon(0,QIcon(iconfile))

                    twnode.setData(1, 0, on_enter)
                    twnode.setData(3, 0, on_exit)
                    twnode.setData(4, 0, helptext)
                    if parent is None:
                        self.tree.addTopLevelItem(twnode)
                    else:
                        parent.addChild(twnode)
                    twnode.setData(2, 0, tools)
                    for child in children:
                        self.buildtree(twnode, child,level,style)
        except Exception as e:
            self.info.err(e)

    def loadstyle(self):
        if self.gto_stylefile is not None:
            try:
                if self.debug: self.info.log("stylefile:", self.gto_stylefile)
                f = QFile(self.gto_stylefile)
                f.open(QFile.ReadOnly | QFile.Text)
                ts = QTextStream(f)
                style = ts.readAll()
                self.dockwidget.setStyleSheet(style)
            except Exception as e:
                self.info.err(e)

