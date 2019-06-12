#!/usr/bin/python
# -*- coding: utf-8 -*-

def run(id, gtotool, config, debug):
    try:
        node =config['node']
        gtotool.gtomain.runNode(node)
        return True
    except Exception as e:
        gtotool.info.gtoWarning(e.args)