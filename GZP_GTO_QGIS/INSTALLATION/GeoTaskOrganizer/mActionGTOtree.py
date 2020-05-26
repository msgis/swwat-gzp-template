#!/usr/bin/python
# -*- coding: utf-8 -*-

def run(id, gtotool, config, debug):
    try:
        node =config['node']
        expand = config.get('expand',False)
        selected = config.get('select',True)
        execute = config.get('execute', True)
        gtotool.gtomain.runNode(node,expand,selected,execute)
        return True
    except Exception as e:
        gtotool.info.err(e)