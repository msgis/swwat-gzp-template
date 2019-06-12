"""
@author: ms.gis, March 2019
Script for QGIS GTO for Modul GZP

"""
import qgis
from qgis.core import QgsProject
from qgis.core import QgsMapLayer
from PyQt5.QtWidgets import QMessageBox

def messagePFLICHT(iface):
    # Identify layer with selection
    lyrList = []

    legend = [tree_layer.layer() for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
    for layer in legend:
        if not layer.name().startswith('DOM') and layer.type() != QgsMapLayer.RasterLayer:
            SrcName = layer.source().split('|layername=')[1].split('|')[0]
            if SrcName == "TBPRJ":
                count1 = layer.featureCount()
                count2 = layer.selectedFeatureCount()
                if count1 == 0 or count2 > 0:
                    lyrList.append(SrcName)
            else:
                count = layer.selectedFeatureCount()
                if count > 0:
                    lyrList.append(SrcName)

    # Message content
    MessageContent = ''
    for l in lyrList:
        MessageContent += "\n{}".format(l)

    # Define Message
    if len(lyrList) == 0:
        QMessageBox.information(None, "INFORMATION", "Prüfung erfolgreich!\nAlle Pflichtfelder befüllt.")
    else:
        MessageFinal = "ACHTUNG:\n\nEin oder mehrere Pflichtfelder in folgenden Datensätzen nicht befüllt:\n" + MessageContent + "\n\nBitte korrigieren!!!\n"
        QMessageBox.critical(None, "FEHLERMELDUNG", MessageFinal)



def messageDOM(iface):
    # Identify layer with selection
    lyrList = []

    legend = [tree_layer.layer() for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
    for layer in legend:
        if not layer.name().startswith('DOM') and layer.type() != QgsMapLayer.RasterLayer:
            SrcName = layer.source().split('|layername=')[1].split('|')[0]

            count = layer.selectedFeatureCount()
            if count > 0:
                lyrList.append(SrcName)

    # Message content
    MessageContent = ''
    for l in lyrList:
        MessageContent += "\n{}".format(l)

    # Define Message
    if len(lyrList) == 0:
        QMessageBox.information(None, "INFORMATION", "Prüfung erfolgreich!\nEinträge in den Domainfeldern entsprechen den vorgegebenen Auswahlwerten.")
    else:
        MessageFinal = "ACHTUNG:\n\nEinträge in den Domainfeldern in folgenden Tabellen entsprechen nicht dem vorgegebenen Auswahlwerten:\n" + MessageContent + "\n\nBitte korrigieren!!!\n"
        QMessageBox.critical(None, "FEHLERMELDUNG", MessageFinal)
