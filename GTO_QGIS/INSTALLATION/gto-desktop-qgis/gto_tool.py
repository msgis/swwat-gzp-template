#!/usr/bin/python
# -*- coding: utf-8 -*-

from builtins import filter
from builtins import str
from PyQt5.QtCore import *
from PyQt5.QtGui import QIcon
import os.path
from .gto_info import gtoInfo
from .gto_helper import getsetting, importModule
import json
import io
import sys
from . import gto_commands

class gtoTool(QObject):
    def __init__(self, gtomain, modulename):
        super(gtoTool, self).__init__()
        self.setObjectName(__name__)#for the info class
        # references
        self.gtomain = gtomain
        self.metadata = gtomain.metadata
        self.info = gtoInfo(self)
        self.debug = gtomain.debug
        self.modulename=modulename
        self.iface = gtomain.iface

    def triggered(self, caller):
        try:
            self.info.log("gto_tool:triggered")
            toolname = str(caller.objectName())#e.g. mActionGTOmisc1'
            self.action = caller
            id_str = ''
            for x in list(filter(str.isdigit, toolname)):
                id_str = id_str + x
            id = int(id_str)
            if self.debug: self.info.log(toolname , " ID=" , id_str)
            #load metadata
            # read data
            data = self.readData(self.modulename, id)
            # get config for id
            if data is not None:
                config = self.getConfig(caller, data, id, self.modulename)
                debug = config['debug']
                if debug:# show info
                    try:
                        text = "metadata of: " + caller.objectName() + " (" + caller.text() + ")\n"
                        for k in list(config.keys()):
                            try:
                                val = str(config[k])
                            except:
                                val = config[k]
                            text = text + k + "=" + val + "\n"
                    except:
                        pass
                    self.info.log(text)
                #run tool
                module = None
                if self.modulename in sys.modules:
                    module = sys.modules[self.modulename]
                try:
                    if module is None:
                        if self.debug: self.info.log("try to __import__:", self.modulename)
                        module = __import__(self.modulename)# python path or assumed sys.path.append(plugin_dir)
                        if self.debug: self.info.log("__import__ SUCCESS!")
                except Exception as e:
                    if self.debug: self.info.err(e)
                try:
                    if module is None:
                        if self.debug: self.info.log("try to importModule:", self.modulename)
                        module = importModule(self.metadata.dirPlugin,self.modulename)
                        if self.debug: self.info.log("importModule:",module, "SUCCESS!")
                except:
                    if self.debug: self.info.err(e)
                if module is not None:
                    self.info.log("run")
                    self.setObjectName(self.modulename)
                    self.info = gtoInfo(self)
                    obj = module.run(id, self, config, debug)
                    try:
                        if self.debug: self.info.log("ID", id_str, ": result:", obj.result)
                    except:
                        if self.debug: self.info.log("ID", id_str, ": result:",obj)
                else:
                    if self.debug: self.info.log(self.modulename , " NOT FOUND!")
        except Exception as e:
            self.info.err(e)

    def readData(self,modulename, id):
        try:
            data = None
            jfile = os.path.join(self.metadata.dirTools , modulename + ".json")
            if os.path.isfile(jfile):
                f = io.open(jfile, encoding='utf-8')
                data = json.load(f)
                f.close()
            else:
                if self.debug: self.info.log('File %s not found!' % jfile)
            return data
        except Exception as e:
            self.info.err(e)

    def getConfig(self,caller, data, id, modulename):
        try:
            for tool in data['tools']:
                if tool['id'] == id:
                    config = tool['config']
                    caption = tool['caption']
                    #icon stuff
                    icon =getsetting( tool,'icon',None)
                    if icon is None or icon == '':
                        icon = modulename.lower() + ".png"
                    iconfile = os.path.join(self.metadata.dirToolIcons, icon)
                    if os.path.isfile(iconfile):
                        caller.setIcon(QIcon(iconfile))
                    #end icon
                    caller.setText(caption)
                    return config
        except Exception as e:
            self.info.err(e)

