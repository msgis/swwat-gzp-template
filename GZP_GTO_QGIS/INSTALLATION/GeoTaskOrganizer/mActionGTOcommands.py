#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from builtins import range
import sys
import os
import ntpath  # equivalent to os.path when running on windows


def run(id, gtotool, config, debug):
    try:
        gtomain = gtotool.gtomain

        # read config
        module_name = config['module']
        command = config['command']
        parameters = config.get('parameters', [])
        settings = config.get('settings', {})
        return run_command(gtomain, gtotool, module_name, command, parameters, settings, debug)
    except Exception as e:
        gtotool.info.err(e)


def run_command(gtomain, gtotool, module_name, command, parameters=[], settings={}, debug=True):
    try:
        # values
        module_path = None
        method = None
        res = False  # return value for gto info
        cmd = ''

        if module_name is None:
            module_name = 'gto_commands.py'
            module_path = gtomain.metadata.dirPlugin
        else:
            module_path = gtomain.metadata.dirScripts

        if os.path.exists(module_path):
            if not module_path in sys.path:
                if debug: gtotool.info.log("add syspath", module_path)
                sys.path.append(module_path)

        module_name = module_name.split('.py')[0]
        if debug: gtotool.info.log("path: ", module_path, "/ module: ", module_name)

        full_path = os.path.join(module_path, module_name + ".py")
        if not os.path.isfile(full_path):
            gtomain.info.log("script does not exist:", full_path)
            return

        module = gtomain.helper.importModule(module_name, module_path)
        try:
            if debug: gtotool.info.log("module init:", module.__name__)
            # get method (command) from module
            method = getattr(module, command)

            if module_name == 'gto_commands':  # fixed internal gto structure
                res = method(gtotool, debug, *parameters, **settings)
                cmd = command + '(' + str(parameters) + "," + str(settings) + ')'
            else:  # simplyfied
                res = method(gtomain.iface, *parameters, **settings)
                cmd = command + '(' + str(parameters) + "," + str(settings) + ')'
            if debug: gtotool.info.log("sucessfull:", module.__name__ + "." + cmd, "result:", res)
        except Exception as e:
            gtotool.info.err(e)
            gtotool.info.log("failed:", module.__name__ + "." + cmd)

        # remove it, so its loaded with changes next time again or project changed!
        if module_path != gtomain.metadata.dirPlugin:
            if module_name in sys.modules:
                del sys.modules[module_name]
                if debug: gtotool.info.log("deleted", module_name, "from sys.modules")
            if module_path in sys.path:
                idx = sys.path.index(module_path)
                del sys.path[idx]
                if debug: gtotool.info.log("deleted", module_path, "from sys.path")

        return res
    except Exception as e:
        gtotool.info.err(e)
