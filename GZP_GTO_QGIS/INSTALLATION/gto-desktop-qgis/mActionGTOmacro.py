#!/usr/bin/python
# -*- coding: utf-8 -*-

def run(id, gtotool, config, debug):
    try:
        #tool data
        tools = config['tools']
        gtotool.gtomain.runcmd(tools)
    except Exception as e:
        gtotool.info.gtoWarning(e.args)
