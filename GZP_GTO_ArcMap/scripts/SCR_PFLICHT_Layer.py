# -*- coding: utf-8 -*-
"""
@author: ms.gis, May 2020
Script for ArcGIS GTO for Modul GZP

"""

##
import arcpy
import pythonaddins

## -------------------------
# Open progress dialog

with pythonaddins.ProgressDialog as dialog:
    dialog.title = "PRUEFUNG PFLICHTDATENSAETZE"
    dialog.description = "Pruefe Pflichtdatensaetze ... Bitte warten..."
    dialog.animation = "Spiral"


    # --- Identify compulsory layers without entries/ features ---

    # Create List for Message Content
    lyrList = []
    countBGef = 0
    countObj = 0

    # Access current map document
    mxd = arcpy.mapping.MapDocument("CURRENT")

    # --- Check TABLES

    # Clear all previous selections
    for tbl in arcpy.mapping.ListTableViews(mxd):
        arcpy.SelectLayerByAttribute_management(tbl.name, "CLEAR_SELECTION")

    # Query tables
    for tbl in arcpy.mapping.ListTableViews(mxd):
        tblSrcName = tbl.datasetName

        if tblSrcName in ["TBPRJ", "TBGEN", "TBGZP", "TBGGN"]:
            result = arcpy.GetCount_management(tbl)
            count = int(result.getOutput(0))
            if count == 0:
                lyrList.append(tblSrcName)


    # --- Check FEATURE LAYERS

    # Clear all previous selections
    for lyr in arcpy.mapping.ListLayers(mxd):
        if lyr.isFeatureLayer:
            arcpy.SelectLayerByAttribute_management(lyr.name, "CLEAR_SELECTION")

    # Query tables
    for lyr in arcpy.mapping.ListLayers(mxd):
        if lyr.isFeatureLayer:
            lyrSrcName = lyr.datasetName

            if lyrSrcName in ["PLGBT", "GSCHUTZ", "LPAKT", "FLUSS", "MODEL"]:
                result = arcpy.GetCount_management(lyr)
                count = int(result.getOutput(0))
                if count == 0:
                    lyrList.append(lyrSrcName)

            elif lyrSrcName == "UFHQN":
                listKat = []
                with arcpy.da.SearchCursor(lyr, ["L_KATEGO"]) as cursor:
                    for row in cursor:
                        listKat.append(row[0])
                    # Check that all scenario categories (1,2,3) present
                    if sorted(set(listKat)) != [1,2,3]:
                        lyrList.append(lyrSrcName)

            elif lyrSrcName == "GZ100":
                # Access unfiltered source layer
                SrcLayer = lyr.dataSource

                listKat = []
                with arcpy.da.SearchCursor(SrcLayer, ["L_KATEGO"]) as cursor:
                    for row in cursor:
                        listKat.append(row[0])
                    # Check that categories (1, 2) present
                    if sorted(set(listKat)) != [1,2]:
                        lyrList.append(lyrSrcName)

            elif lyrSrcName == "GZ300":
                listKat = []
                with arcpy.da.SearchCursor(lyr, ["L_KATEGO"]) as cursor:
                    for row in cursor:
                        listKat.append(row[0])
                    # Check that category "Gelb-schraffierte Zone" (2) present
                    if 2 not in sorted(set(listKat)):
                        lyrList.append(lyrSrcName)

            elif lyrSrcName == "FUNKT":
                listKat = []
                with arcpy.da.SearchCursor(lyr, ["L_KATEGO"]) as cursor:
                    for row in cursor:
                        listKat.append(row[0])
                    # Check that category "Rot-Gelb-schraffierter Funktionsbereich" (1) present
                    if 1 not in sorted(set(listKat)):
                        lyrList.append(lyrSrcName)

            elif lyrSrcName == "KNTPKT":
                listKat = []
                with arcpy.da.SearchCursor(lyr, ["SZENARIO"]) as cursor:
                    for row in cursor:
                        listKat.append(row[0])
                    # Check that all szenarios (30, 100, 300) present
                    if sorted(set(listKat)) != [30,100,300]:
                        lyrList.append(lyrSrcName)

            elif lyrSrcName == "GPLBAU":
                listKat = []
                with arcpy.da.SearchCursor(lyr, ["L_KATEGO"]) as cursor:
                    for row in cursor:
                        listKat.append(row[0])
                    # Check that category "beplant od. verbaut" (1) present
                    if 1 not in sorted(set(listKat)):
                        lyrList.append(lyrSrcName)

            elif lyrSrcName == "BWERT":
                listKat = []
                with arcpy.da.SearchCursor(lyr, ["SZENARIO"]) as cursor:
                    for row in cursor:
                        listKat.append(row[0])
                    # Check that all szenarios (30, 100, 300) present
                    if sorted(set(listKat)) != [30,100,300]:
                        lyrList.append(lyrSrcName)

            elif lyrSrcName in ["GFPKT", "GFLIN", "GFFLA"]:
                result = arcpy.GetCount_management(lyr)
                countBGef += int(result.getOutput(0))

            elif lyrSrcName in ["OBPKT", "OBLIN", "OBFLA"]:
                result = arcpy.GetCount_management(lyr)
                countBGef += int(result.getOutput(0))

            elif lyrSrcName == "QPLIN":
                listKat = []
                with arcpy.da.SearchCursor(lyr, ["L_KATEGO"]) as cursor:
                    for row in cursor:
                        listKat.append(row[0])
                    # Check that at least categories 1 & 2 present
                    if not set([1,2]).issubset(sorted(set(listKat))):
                        lyrList.append(lyrSrcName)

    # Test if at least one feature of Besondere Gefährdungen or Objekte present
    if countBGef == 0:
        lyrList.append("GFPKT, GFLIN oder GFFLA")
    if countObj == 0:
        lyrList.append("OBPKT, OBLIN oder OBFLA")

    ##
    MessageContent = ""
    for l in lyrList:
        MessageContent += "\n{}".format(l)

##
# Define Message
if len(lyrList) == 0:
    pythonaddins.MessageBox("Pruefung erfolgreich.\nAlle Pflichtdatensaetze befuellt.", "INFORMATION", 0)

else:
    MessageFinal = "Folgende Pflichtdatensaetze sind nicht (ausreichend) befuellt:\n" + MessageContent + "\n\nBitte korrigieren! \n"
    pythonaddins.MessageBox(MessageFinal, "FEHLERMELDUNG", 0)

del lyrList
