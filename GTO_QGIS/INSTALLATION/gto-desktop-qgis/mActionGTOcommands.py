#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from builtins import range
import sys
import os
import ntpath# equivalent to os.path when running on windows

def run(id, gtotool, config, debug):
    try:
        gtomain = gtotool.gtomain

        #read config
        module_name = config['module']
        command = config['command']
        parameters = config.get('parameters',[])
        settings = config.get('settings',{})
        #values
        module_path = None
        method = None
        res = False #return value for gto info
        cmd = ''

        if module_name is None:
            module_name = 'gto_commands.py'
        if os.path.isfile(module_name):#absolute path
            module_path = os.path.dirname(module_name)
            module_name = os.path.basename(module_name)
        else:
            module_path =  gtomain.metadata.dirPlugin
            file = os.path.join(module_path,module_name)
            if not os.path.isfile(file):#look in gto config/scripts
                module_path = gtomain.metadata.dirScripts

        if os.path.exists(module_path):
            if not module_path in sys.path:
                if debug: gtotool.info.log("add syspath", module_path)
                sys.path.append(module_path)
        module_name = module_name.split('.py')[0]

        if debug:
            gtotool.info.log("path: ",module_path)
            gtotool.info.log("module: ", module_name)

        module = None
        if module_name in sys.modules:
            module =  sys.modules[module_name]
            if debug: gtotool.info.log("module already loaded:", module_name)
        else:
            if debug: gtotool.info.log("_import_ : ", module_name, " from ", module_path)
            try:
                module = __import__(module_name)
            except Exception as e:
                gtotool.info.err(e)
        if not module_name:
            try:
                if debug: gtotool.info.log("try importlib:", module_name)
                import importlib.util
                file = os.path.join(module_path, module_name + '.py')
                spec = importlib.util.spec_from_file_location(module_name, file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module_name)
            except Exception as e:
                gtotool.info.err(e)

        if debug: gtotool.info.log("module init:",module.__name__ )
        #get method (command) from module
        method = getattr(module, command)

        if module_name == 'gto_commands':#fixed internal gto structure
            res = method(gtotool, debug, *parameters, **settings)
            cmd = command + '(' + str(parameters) + "," + str(settings) + ')'
        else:#simplyfied, but always passing iface (e.g. for scriptrunner)
            if settings and parameters:
                res = method(gtomain.iface,*parameters,**settings)
                cmd = command + '(' + str(parameters) + "," + str(settings) + ')'
            elif not settings and not parameters:
                res = method(gtomain.iface)
                cmd = command + '()'
            elif parameters:
                res = method(gtomain.iface,*parameters)
                cmd = command + '(' + str(parameters) + ")"
            elif settings:
                res = method(gtomain.iface,**settings)
                cmd = command + '(' + str(settings) + ")"

        if debug: gtotool.info.log("sucessfull:",module.__name__ + "." + cmd)
    except Exception as e:
        gtotool.info.err(e)

