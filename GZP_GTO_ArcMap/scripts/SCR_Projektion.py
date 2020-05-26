# -*- coding: utf-8 -*-
"""
@author: ms.gis, May 2020
Script for ArcGIS GTO for Modul GZP

"""

import arcpy
import pythonaddins

# Set counter and message content
ErrorCount = 0
MessageInhalt = ""


# Get data frame crs
mxd = arcpy.mapping.MapDocument("CURRENT")
for df in arcpy.mapping.ListDataFrames(mxd):
    if df.name == "GZP Datentemplate":
        dfCrs = df.spatialReference.factoryCode

# Error if project crs not set
if dfCrs == 0:
    MessageDfCrs = "ACHTUNG:\n\nProjekt-KBS ist nicht gesetzt! \nBitte in den Datenrahmen-Eigenschaften das im GZP verwendete Koordinatenbezugssystem setzen.\n"
    pythonaddins.MessageBox(MessageDfCrs, "FEHLERMELDUNG", 0)

else:
    # get list of all layers
    for lyr in arcpy.mapping.ListLayers(mxd):

        # get spatial reference
        if lyr.isFeatureLayer:
            crs = arcpy.Describe(lyr).spatialReference.factorycode
            
            # print warning if not data frame crs
            if crs != dfCrs:
                ErrorCount += 1
                MessageInhalt += "{}\n".format(lyr.datasetName)
        
        else:
            pass

    if ErrorCount == 0:
        pythonaddins.MessageBox ("Pruefung erfolgreich abgeschlossen. \nAlle Feature Layer liegen im Projekt-KBS ({}) vor.".format(dfCrs), "INFORMATION", 0)
            
    else:
        MessageFinal = "ACHTUNG:\n\nFolgende Layer liegen nicht im Projekt-KBS ({}) vor: \n\n{}\nBitte korrigieren!!! \n".format(dfCrs, MessageInhalt)
        pythonaddins.MessageBox (MessageFinal, "FEHLERMELDUNG", 0)