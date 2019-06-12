# -*- coding: utf-8 -*-

import qgis
from qgis.core import QgsProject
from qgis.core import QgsMapLayer
from PyQt5.QtWidgets import QMessageBox

def testProjektion(iface):

    # Set counter and message content
    ErrorCount = 0
    MessageInhalt = ""

    # get list of all layers
    legend = [tree_layer.layer() for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
    for layer in legend:
        #test if feature layer (opposed to table or raster)
        if layer.isSpatial() and layer.type() != QgsMapLayer.RasterLayer:
            # get crs info
            lyr_crs = layer.sourceCrs().authid()

            #add warning if not epsg 31287
            if lyr_crs != "EPSG:31287":
                ErrorCount =+ 1
                MessageInhalt += "{}\n".format(layer.name())

    if ErrorCount == 0:
        QMessageBox.information(None, "INFORMATION", "Prüfung erfolgreich abgeschlossen. \nAlle Feature Layer liegen in MGI Austria Lambert (EPSG: 31287) vor.")
    else:
        MessageFinal = "ACHTUNG:\n\nFolgende Layer liegen nicht in MGI Austria Lambert (EPSG: 31287) vor: \n\n" + MessageInhalt + "\nBitte korrigieren!!! \n"
        QMessageBox.critical(None, "FEHLERMELDUNG", MessageFinal)
