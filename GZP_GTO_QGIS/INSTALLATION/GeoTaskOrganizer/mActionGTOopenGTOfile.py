#!/usr/bin/python
# -*- coding: utf-8 -*-

import os


def run(id, gtotool, config, debug):
    try:
        # init
        info = gtotool.info
        metadata = gtotool.metadata
        # metadata
        file = config.get('file')
        if file is not None:
            if not os.path.isfile(file):  # not absolute
                file = os.path.join(metadata.dirGTO, file)
                file = os.path.abspath(file)
            if debug: info.log(file)
        try:
            os.startfile(str(file))
        except Exception as e:
            info.gtoWarning(e.args, file)
    except Exception as e:
        info.err(e)
