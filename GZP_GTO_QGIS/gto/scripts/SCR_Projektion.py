# -*- coding: utf-8 -*-

"""
@author: ms.gis, June 2020
Script for QGIS GTO for Modul GZP

"""

import qgis
from qgis.core import QgsProject
from qgis.core import QgsMapLayer
from PyQt5.QtWidgets import QMessageBox

def testProjektion(iface):

    # Set project, counter, and message content
    project = QgsProject.instance()
    ErrorCount = 0
    MessageInhalt = ""
    
    # Get project crs
    projCrs = project.crs().authid()
    
    # Error if project crs not set
    if projCrs == '':
        MessageProjCrs = "ACHTUNG:\n\nProjekt-KBS ist nicht gesetzt! \nBitte dem Projekt das im GZP verwendete Koordinatenbezugssystem zuweisen.\n"
        QMessageBox.critical(None, "FEHLERMELDUNG", MessageProjCrs)

    else:
        # Get list of all layers
        legend = [tree_layer.layer() for tree_layer in project.layerTreeRoot().findLayers()]
        for layer in legend:
            # Test if feature layer (opposed to table or raster)
            if layer.isSpatial() and layer.type() != QgsMapLayer.RasterLayer:
                SrcName = layer.source().split('|layername=')[1].split('|')[0]
                # Reload layer to get correct crs info
                layer.setDataSource(layer.source(), layer.name(), 'ogr')
                # Get crs info
                lyr_crs = layer.sourceCrs().authid()

                # Add warning if not project CRS
                if lyr_crs != projCrs:
                    ErrorCount =+ 1
                    MessageInhalt += "{}\n".format(SrcName)

        if ErrorCount == 0:
            QMessageBox.information(None, "INFORMATION", "Prüfung erfolgreich abgeschlossen. \nAlle Feature-Layer liegen im Projekt-KBS ({}) vor.".format(projCrs))
        else:
            MessageFinal = "ACHTUNG:\n\nFolgende Layer liegen nicht im Projekt-KBS ({}) vor: \n\n{}\nBitte korrigieren! \n".format(projCrs, MessageInhalt)
            QMessageBox.critical(None, "FEHLERMELDUNG", MessageFinal)