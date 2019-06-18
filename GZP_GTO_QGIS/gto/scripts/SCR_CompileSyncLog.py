"""
@author: ms.gis, May 2019
Script for ArcGIS GTO for Modul GZP

"""

import qgis, os, ogr, time
from qgis.core import QgsProject
from qgis.core import QgsVectorLayer
from qgis.core import QgsRasterLayer
from qgis.core import QgsMapLayer
from qgis.core import QgsFeature
from PyQt5.QtWidgets import QMessageBox
from qgis.PyQt.QtWidgets import QProgressDialog
import datetime


def compileSyncLog(iface):

    # Display Progress Dialog
    bar = QProgressDialog()
    bar.setWindowTitle("IN ARBEIT ... Bitte warten ...")
    bar.setLabelText("Befülle Sync Log Tabelle fuer den Datenupload ... Bitte warten...")
#    bar.setCancelButton(None)
    bar.show()
#    bar.setRange(0,0)
    
    time.sleep(5)

    # -------------------------
    # Get .gpkg path

    # List of relevant layer
    dsList = [u'BWERT', u'LPAKT', u'GSCHUTZ', u'QPLIN', u'PLGBT', u'MODEL', u'KNTPKT', u'GFPKT', u'GFLIN', u'GFFLA', u'GZ100', u'FUNKT', u'GZ300', u'UFHQN', u'TBGGN', u'TBGZP', u'TBPRJ', u'TBGEN']

    # Access current project
    legend = [tree_layer.layer() for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]

    # Get .gpkg path from first layer that is in dsList
    for layer in legend:
        if layer.type() != QgsMapLayer.RasterLayer and not layer.name().startswith('DOM_'):
            dsName = layer.source().split('|layername=')[1].split('|')[0]
            if dsName in dsList:
                gpkgPath = layer.source().split('|layername=')[0]
                break


    ## -------------------------
    # Write from layers to GTO sync log

    # Delete previous entries in Sync Log
    syncLog = QgsVectorLayer(gpkgPath+'|layername=GTO_SYNC_LOG', 'syncLog', 'ogr')
    syncLog.startEditing()
    listIds1 = [feat.id() for feat in syncLog.getFeatures()]
    syncLog.deleteFeatures(listIds1)
    syncLog.commitChanges()
    

    # Set timestamp value
    entry = 0
    syncTimeStamp = datetime.datetime.now().strftime('%Y.%m.%d %H:%M:%S')

    # Get access to Sync Log Table
    feat = QgsFeature(syncLog.fields())
        
    gpkg = ogr.Open(gpkgPath)
    for i in gpkg:
        if i.GetName() in dsList:
            layer = QgsVectorLayer(gpkgPath+'|layername='+ i.GetName(), i.GetName(), 'ogr')
            rows = layer.getFeatures()
            for row in rows:
                entry += 1
                feat.setAttribute('GTO_FC_NAME', i.GetName())
                feat.setAttribute('GTO_SQLITE_ID', row.id())
                feat.setAttribute('GTO_OP', "C")
                feat.setAttribute('GTO_OP_DATE', syncTimeStamp)
                feat.setAttribute('GTO_ENT_ID', row.id())
                feat.setAttribute('GTO_ID', entry)
                syncLog.dataProvider().addFeatures([feat])
    
    bar.hide()
    
    MessageFinal = "Befüllen der Sync Log Tabelle erfolgreich abgeschlossen."
    QMessageBox.information(None, "INFORMATION", MessageFinal)

