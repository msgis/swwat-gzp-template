# -*- coding: utf-8 -*-

"""
@author: ms.gis, June 2020
Script for ArcGIS GTO for Modul GZP

"""

##
import arcpy
import re
import pythonaddins


## -------------------------
# Open progress dialog

with pythonaddins.ProgressDialog as dialog:
    dialog.title = "PRUEFUNG PFLICHTFELDER KNTPKT"
    dialog.description = "Pruefe Pflichtfelder ... Bitte warten..."
    dialog.animation = "Spiral"


    # Start processing
    mxd = arcpy.mapping.MapDocument("CURRENT")
    
    # Create list for message content
    ErrorList = []

    # Clear all previous selections
    for tbl in arcpy.mapping.ListTableViews(mxd):
        arcpy.SelectLayerByAttribute_management(tbl.name, "CLEAR_SELECTION")

    # Get edvkz from TBPRJ
    edvkz = None    # Set edvkz Null in case no TBPRJ entry
    for tbl in arcpy.mapping.ListTableViews(mxd):
        if tbl.datasetName == "TBPRJ":
            # Get edvkz
            with arcpy.da.SearchCursor(tbl, ['EDVKZ']) as cursor:
                for row in cursor:
                    edvkz = row[0]

    del cursor

    # Error Messages if edvkz not correct format
    if edvkz in (None, '',' ','<Null>') or not re.match("^\d[A-Z]\d{6}$",edvkz):
        MessageNULL = 'ACHTUNG:\n\nIn der Projekttabelle (TBPRJ) ist das Feld "EDVKZ" nicht korrekt befuellt (leer bzw. keine EDVKZ).\nBitte korrigieren bevor die Pruefung aller Layer moeglich ist!\n'
        pythonaddins.MessageBox(MessageNULL, "FEHLERMELDUNG", 0)

    # If correct format proceed with checking of other layers
    else:

        # Define queries
        queryEDVKZ = "EDVKZ IS NULL OR EDVKZ IN ('',' ','<Null>') OR EDVKZ <> '{}'".format(edvkz)
        querySZENARIO = "SZENARIO IS NULL"
        queryKN_Z = "KN_Z IS NULL"
        queryKN_FLAECH = "KN_FLAECH IS NULL"
        queryWT_MAX = "WT_MAX IS NULL"
        queryFG_MAX = "FG_MAX IS NULL"
        queryQF_SUM = "QF_SUM IS NULL"


        # Clear all previous selections
        for lyr in arcpy.mapping.ListLayers(mxd):
            if lyr.isFeatureLayer:
                arcpy.SelectLayerByAttribute_management(lyr.name, "CLEAR_SELECTION")

        # Query feature layers
        for lyr in arcpy.mapping.ListLayers(mxd):
            if lyr.isFeatureLayer:
                lyrSrcName = lyr.datasetName
                lyrName = lyr.name

                if lyrSrcName == "KNTPKT":
                    arcpy.SelectLayerByAttribute_management(lyrName, "ADD_TO_SELECTION", queryEDVKZ)
                    arcpy.SelectLayerByAttribute_management(lyrName, "ADD_TO_SELECTION", querySZENARIO)
                    arcpy.SelectLayerByAttribute_management(lyrName, "ADD_TO_SELECTION", queryKN_Z)
                    arcpy.SelectLayerByAttribute_management(lyrName, "ADD_TO_SELECTION", queryKN_FLAECH)
                    arcpy.SelectLayerByAttribute_management(lyrName, "ADD_TO_SELECTION", queryWT_MAX)
                    arcpy.SelectLayerByAttribute_management(lyrName, "ADD_TO_SELECTION", queryFG_MAX)
                    arcpy.SelectLayerByAttribute_management(lyrName, "ADD_TO_SELECTION", queryQF_SUM)

                    desc = arcpy.Describe(lyrName)
                    if len(desc.FIDSet) > 0:
                        ErrorList.append(lyrSrcName)

        ##
        MessageContent = ""
        for l in ErrorList:
            MessageContent += "\n{}".format(l)

        ##
        # Define Message
        if len(ErrorList) == 0:
            pythonaddins.MessageBox("Pruefung erfolgreich.\nAlle Pflichtfelder im Layer Knotenpunkte (KNTPKT) befuellt.", "INFORMATION", 0)

        else:
            MessageFinal = "ACHTUNG:\n\nEin oder mehrere Pflichtfelder sind im Layer Knotenpunkte (KNTPKT) nicht befuellt bzw. ist die EDVKZ inkorrekt: Bitte korrigieren! \n"
            pythonaddins.MessageBox(MessageFinal, "FEHLERMELDUNG", 0)

del ErrorList
del edvkz
