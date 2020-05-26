#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5.QtCore import *
from PyQt5.QtGui import QIcon
import os.path
from .gto_info import gtoInfo
import json
import io
import sys


class gtoTool(QObject):
    def __init__(self, gtomain, modulename):
        super(gtoTool, self).__init__()
        self.setObjectName(__name__)  # for the info class
        # references
        self.gtomain = gtomain
        self.metadata = gtomain.metadata
        self.info = gtoInfo(self)
        self.debug = gtomain.debug
        self.modulename = modulename
        self.iface = gtomain.iface
        self.action = None
        self.obj = None

    def triggered(self, caller):
        try:
            self.info.log("gto_tool:triggered")
            toolname = str(caller.objectName())  # e.g. mActionGTOmisc1'
            self.action = caller
            id_str = ''
            for x in list(filter(str.isdigit, toolname)):
                id_str = id_str + x
            toolID = int(id_str)
            if self.debug: self.info.log(toolname, " ID=", id_str)
            # load metadata
            # read data
            data = self.readData(self.modulename)
            # get config for id
            if data is not None:
                config = self.getConfig(caller, data, toolID, self.modulename)
                debug = config['debug']
                if debug:  # show info
                    text = ''
                    try:
                        text = 'Metadata of: {0} ({1})\n'.format(str(caller.objectName()), str(caller.text()))
                        # text = '' + str(caller.objectName()) + " (" + str(caller.text()) + ")\n"
                        for k in list(config.keys()):
                            text = text + k + "=" + str(config[k]) + "\n"
                    except Exception as e:
                        self.info.err(e)
                    self.info.log(text)
                # run tool
                module = self.gtomain.helper.importModule(self.modulename)
                if module is not None:
                    self.info.log("run")
                    self.setObjectName(self.modulename)
                    self.info = gtoInfo(self)
                    self.obj = module.run(toolID, self, config, debug)
                    try:
                        if isinstance(self.obj, classmethod):
                            if self.debug: self.info.log("ID", id_str, ": result:", self.obj.result)
                        else:
                            if self.debug: self.info.log("ID", id_str, ": result:", self.obj)
                        # if self.debug: self.info.log("ID", id_str, ": result:", self.obj.result)
                    except Exception as e:
                        if self.debug: self.info.err(e)
                else:
                    if self.debug: self.info.log(self.modulename, " NOT FOUND!")
        except Exception as e:
            self.info.err(e)

    def readData(self, modulename):
        try:
            data = None
            jfile = os.path.join(self.metadata.dirTools, modulename + ".json")
            if os.path.isfile(jfile):
                f = io.open(jfile, encoding='utf-8')
                data = json.load(f)
                f.close()
            else:
                if self.debug: self.info.log('File %s not found!' % jfile)
            return data
        except Exception as e:
            self.info.err(e)

    def getConfig(self, caller, data, toolID, modulename):
        try:
            for tool in data['tools']:
                if tool['id'] == toolID:
                    config = tool['config']
                    caption = tool['caption']
                    # icon stuff
                    icon = tool.get('icon', None)
                    if icon is None or icon == '':
                        icon = modulename.lower() + ".png"
                    iconfile = os.path.join(self.metadata.dirToolIcons, icon)
                    if os.path.isfile(iconfile):
                        caller.setIcon(QIcon(iconfile))
                    # end icon
                    caller.setText(caption)
                    return config
        except Exception as e:
            self.info.err(e)
