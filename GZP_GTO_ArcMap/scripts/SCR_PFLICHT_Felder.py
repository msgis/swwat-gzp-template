# -*- coding: utf-8 -*-

"""
@author: ms.gis, May 2020
Script for ArcGIS GTO for Modul GZP

"""

##
import arcpy
import re
import pythonaddins


## -------------------------
# Open progress dialog

with pythonaddins.ProgressDialog as dialog:
    dialog.title = "PRUEFUNG PFLICHTFELDER"
    dialog.description = "Pruefe Pflichtfelder ... Bitte warten..."
    dialog.animation = "Spiral"

    ## -------------------------
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
        queryKURZRID = "KURZRID IS NULL OR KURZRID IN ('',' ','<Null>')"
        queryGGN_VERS_1 = "GGN_VERS IS NULL OR GGN_VERS IN ('',' ','<Null>')"
        queryGGN_VERS_2 = "(GGN_VERS IS NULL OR GGN_VERS IN ('',' ','<Null>')) AND (G_NEU_OK IS NULL)"   # G_NEU_OK is type integer, hence other options not applicable
        queryAK_DATUM = "AK_DATUM IS NULL"
        queryA_AGORG = "A_AGORG IS NULL OR A_AGORG IN ('',' ','<Null>')"
        queryA_PLANER = "A_PLANER IS NULL OR A_PLANER IN ('',' ','<Null>')"
        queryA_DIG_DAT = "A_DIG_DAT IS NULL"
        queryGEN_ZAHL = "GEN_ZAHL IS NULL OR GEN_ZAHL IN ('',' ','<Null>')"
        queryGEN_DAT = "GEN_DAT IS NULL"
        querySZENARIO = "SZENARIO IS NULL"
        queryQMAX = "QMAX IS NULL"


        # --- Check mandatory fields in TABLES

        # Query tables
        for tbl in arcpy.mapping.ListTableViews(mxd):
            tblSrcName = tbl.datasetName
            tblName = tbl.name

            if tblSrcName == "TBPRJ":
                #arcpy.SelectLayerByAttribute_management(tblName, "ADD_TO_SELECTION", queryEDVKZ)    # Circular test
                arcpy.SelectLayerByAttribute_management(tblName, "ADD_TO_SELECTION", queryAK_DATUM)
                arcpy.SelectLayerByAttribute_management(tblName, "ADD_TO_SELECTION", queryA_AGORG)
                arcpy.SelectLayerByAttribute_management(tblName, "ADD_TO_SELECTION", queryA_PLANER)
                arcpy.SelectLayerByAttribute_management(tblName, "ADD_TO_SELECTION", queryA_DIG_DAT)

                desc = arcpy.Describe(tblName)
                if len(desc.FIDSet) > 0:
                    ErrorList.append(tblSrcName)

            elif tblSrcName == "TBGEN":
                arcpy.SelectLayerByAttribute_management(tblName, "ADD_TO_SELECTION", queryEDVKZ)
                arcpy.SelectLayerByAttribute_management(tblName, "ADD_TO_SELECTION", queryGEN_ZAHL)
                arcpy.SelectLayerByAttribute_management(tblName, "ADD_TO_SELECTION", queryGEN_DAT)

                desc = arcpy.Describe(tblName)
                if len(desc.FIDSet) > 0:
                    ErrorList.append(tblSrcName)

            elif tblSrcName == "TBGZP":
                arcpy.SelectLayerByAttribute_management(tblName, "ADD_TO_SELECTION", queryEDVKZ)
                arcpy.SelectLayerByAttribute_management(tblName, "ADD_TO_SELECTION", queryAK_DATUM)

                desc = arcpy.Describe(tblName)
                if len(desc.FIDSet) > 0:
                    ErrorList.append(tblSrcName)

            elif tblSrcName == "TBGGN":
                arcpy.SelectLayerByAttribute_management(tblName, "ADD_TO_SELECTION", queryEDVKZ)
                arcpy.SelectLayerByAttribute_management(tblName, "ADD_TO_SELECTION", queryKURZRID)
                arcpy.SelectLayerByAttribute_management(tblName, "ADD_TO_SELECTION", queryGGN_VERS_2)
                arcpy.SelectLayerByAttribute_management(tblName, "ADD_TO_SELECTION", queryAK_DATUM)

                desc = arcpy.Describe(tblName)
                if len(desc.FIDSet) > 0:
                    ErrorList.append(tblSrcName)

        # --- Check mandatory fields in FEATURE LAYERS

        # Clear all previous selections
            for lyr in arcpy.mapping.ListLayers(mxd):
                if lyr.isFeatureLayer:
                    arcpy.SelectLayerByAttribute_management(lyr.name, "CLEAR_SELECTION")

        # Query feature layers
        for lyr in arcpy.mapping.ListLayers(mxd):
            if lyr.isFeatureLayer:
                lyrSrcName = lyr.datasetName
                lyrName = lyr.name

                if lyrSrcName in ("PLGBT","GPLBAU","GSCHUTZ","LPAKT"):
                    arcpy.SelectLayerByAttribute_management(lyrName, "ADD_TO_SELECTION", queryEDVKZ)
                    arcpy.SelectLayerByAttribute_management(lyrName, "ADD_TO_SELECTION", queryKURZRID)
                    arcpy.SelectLayerByAttribute_management(lyrName, "ADD_TO_SELECTION", queryGGN_VERS_1)
                    arcpy.SelectLayerByAttribute_management(lyrName, "ADD_TO_SELECTION", queryAK_DATUM)

                    desc = arcpy.Describe(lyrName)
                    if len(desc.FIDSet) > 0:
                        ErrorList.append(lyrSrcName)

                elif lyrSrcName in ("GFPKT","GFLIN","GFFLA","FLUSS"):
                    arcpy.SelectLayerByAttribute_management(lyrName, "ADD_TO_SELECTION", queryEDVKZ)
                    arcpy.SelectLayerByAttribute_management(lyrName, "ADD_TO_SELECTION", queryAK_DATUM)

                    desc = arcpy.Describe(lyrName)
                    if len(desc.FIDSet) > 0:
                        ErrorList.append(lyrSrcName)

                elif lyrSrcName in ("UFHQN","GZ100","GZ300","FUNKT"):
                    arcpy.SelectLayerByAttribute_management(lyrName, "ADD_TO_SELECTION", queryEDVKZ)
                    arcpy.SelectLayerByAttribute_management(lyrName, "ADD_TO_SELECTION", queryKURZRID)
                    arcpy.SelectLayerByAttribute_management(lyrName, "ADD_TO_SELECTION", queryGGN_VERS_1)
                    arcpy.SelectLayerByAttribute_management(lyrName, "ADD_TO_SELECTION", queryAK_DATUM)
                    arcpy.SelectLayerByAttribute_management(lyrName, "ADD_TO_SELECTION", querySZENARIO)

                    desc = arcpy.Describe(lyrName)
                    if len(desc.FIDSet) > 0:
                        ErrorList.append(lyrSrcName)

                elif lyrSrcName in ("OBPKT","OBLIN","OBFLA","MODEL","QPLIN"):
                    arcpy.SelectLayerByAttribute_management(lyrName, "ADD_TO_SELECTION", queryEDVKZ)
                    arcpy.SelectLayerByAttribute_management(lyrName, "ADD_TO_SELECTION", queryAK_DATUM)
                    arcpy.SelectLayerByAttribute_management(lyrName, "ADD_TO_SELECTION", querySZENARIO)

                    desc = arcpy.Describe(lyrName)
                    if len(desc.FIDSet) > 0:
                        ErrorList.append(lyrSrcName)

                elif lyrSrcName == "BWERT":
                    arcpy.SelectLayerByAttribute_management(lyrName, "ADD_TO_SELECTION", queryEDVKZ)
                    arcpy.SelectLayerByAttribute_management(lyrName, "ADD_TO_SELECTION", querySZENARIO)
                    arcpy.SelectLayerByAttribute_management(lyrName, "ADD_TO_SELECTION", queryQMAX)

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
            pythonaddins.MessageBox("Pruefung erfolgreich.\nAlle Pflichtfelder befuellt.", "INFORMATION", 0)

        else:
            MessageFinal = "ACHTUNG:\n\nEin oder mehrere Pflichtfelder in folgenden Tabellen nicht befuellt bzw. ist die EDVKZ inkorrekt:\n" + MessageContent + "\n\nBitte korrigieren! \n"
            pythonaddins.MessageBox(MessageFinal, "FEHLERMELDUNG", 0)

del ErrorList
del edvkz
