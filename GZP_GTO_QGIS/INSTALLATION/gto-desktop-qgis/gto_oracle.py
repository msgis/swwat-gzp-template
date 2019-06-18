#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5.QtGui import *
from PyQt5.QtSql import *
import qgis.core

def getUser(gtotool, layer):
    try:
        # use the workspace of the layer:
        # get data provider
        provider = layer.dataProvider()
        provider_name = provider.name()
        uri = qgis.core.QgsDataSourceURI(provider.dataSourceUri())
        return uri.username()
    except Exception as e:
        gtotool.info.err(e.args)