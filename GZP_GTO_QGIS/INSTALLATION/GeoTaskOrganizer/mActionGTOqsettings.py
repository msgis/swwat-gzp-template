#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5.QtCore import QSettings

def run(id, gtotool, config, debug):
    try:
        iface = gtotool.iface
        info = gtotool.info
        settings = config['settings']
        s = QSettings()
        for key in settings:
            val =settings[key]
            s.setValue(key,val)
            if debug: info.log("key:",key,"[set to]:",val,"value:",s.value(key))
    except IndexError as  e:
        info.log(e.args)