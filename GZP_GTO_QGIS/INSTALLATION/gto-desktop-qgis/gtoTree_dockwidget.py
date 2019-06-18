# -*- coding: utf-8 -*-
"""
/***************************************************************************
 WFEDockWidget
                                 A QGIS plugin
 Organizes your workflows
                             -------------------
        begin                : 2017-02-20
        git sha              : $Format:%H$
        copyright            : (C) 2017 by msgis
        email                : contact@msgis.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from PyQt5 import QtGui, uic
from PyQt5.QtCore import pyqtSignal
'GP'
from PyQt5.QtCore import  *
from qgis.gui import *
from PyQt5.QtWidgets import QDockWidget

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'gtoTree_dockwidget_base.ui'))


class GTODockWidget(QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(GTODockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()


