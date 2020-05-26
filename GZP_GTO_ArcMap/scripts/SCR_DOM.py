# -*- coding: utf-8 -*-
"""
@author: ms.gis, May 2020
Script for ArcGIS GTO for Modul GZP

"""

##
import arcpy
import pythonaddins

with pythonaddins.ProgressDialog as dialog:
    dialog.title = "PRUEFUNG DOMAINWERTE"
    dialog.description = "Pruefe Domainwerte ... Bitte warten..."
    dialog.animation = "Spiral"

    # --- Check DOM values ---

    # Create List for Message Content
    ErrorList = []

    # Access current map document
    mxd = arcpy.mapping.MapDocument("CURRENT")

    # --- Check TABLES

    # Clear all previous selections
    for tbl in arcpy.mapping.ListTableViews(mxd):
        tblName = tbl.name
        arcpy.SelectLayerByAttribute_management(tblName, "CLEAR_SELECTION")

    # Loop through tables in map document
    for tbl in arcpy.mapping.ListTableViews(mxd):
        tblSrcName = tbl.datasetName
        tblName = tbl.name

        if tblSrcName == "TBPRJ":
            arcpy.SelectLayerByAttribute_management(tblName, "ADD_TO_SELECTION", "PRJ_TYP IS NULL OR PRJ_TYP NOT IN (5,6,16)")
            arcpy.SelectLayerByAttribute_management(tblName, "ADD_TO_SELECTION", "FIN_ART IS NULL OR FIN_ART NOT IN (1,2,3)")
            desc = arcpy.Describe(tblName)
            if len(desc.FIDSet) > 0:
                ErrorList.append(tblSrcName)

        elif tblSrcName == "TBGEN":
            arcpy.SelectLayerByAttribute_management(tblName, "ADD_TO_SELECTION", "GEN_ORG IS NULL OR GEN_ORG NOT IN (1,2,3,4)")
            arcpy.SelectLayerByAttribute_management(tblName, "ADD_TO_SELECTION", "GEN_ART IS NULL OR GEN_ART NOT IN (1,2,3,4)")
            desc = arcpy.Describe(tblName)
            if len(desc.FIDSet) > 0:
                ErrorList.append(tblSrcName)

        elif tblSrcName == "TBGZP":
            arcpy.SelectLayerByAttribute_management(tblName, "ADD_TO_SELECTION", "BERECH_M IS NULL OR BERECH_M NOT IN (1,2,3,4)")
            arcpy.SelectLayerByAttribute_management(tblName, "ADD_TO_SELECTION", "DIMENS_M NOT IN (1,2,3)")
            arcpy.SelectLayerByAttribute_management(tblName, "ADD_TO_SELECTION", "M_HWENT NOT IN (1,2,3)")
            desc = arcpy.Describe(tblName)
            if len(desc.FIDSet) > 0:
                ErrorList.append(tblSrcName)


    # --- Check FEATURE LAYERS

    # Clear all previous selections
    for lyr in arcpy.mapping.ListLayers(mxd):
        if lyr.isFeatureLayer:
            arcpy.SelectLayerByAttribute_management(lyr.name, "CLEAR_SELECTION")

    # # Query feature layers
    for lyr in arcpy.mapping.ListLayers(mxd):
        if lyr.isFeatureLayer:
            lyrSrcName = lyr.datasetName
            lyrName = lyr.name

            if lyrSrcName == "GPLBAU":
                arcpy.SelectLayerByAttribute_management(lyrName, "ADD_TO_SELECTION", "L_KATEGO IS NULL OR L_KATEGO NOT IN (1,2,3)")
                desc = arcpy.Describe(lyrName)
                if len(desc.FIDSet) > 0:
                    ErrorList.append(lyrSrcName)

            elif lyrSrcName == "GSCHUTZ":
                arcpy.SelectLayerByAttribute_management(lyrName, "ADD_TO_SELECTION", "L_KATEGO IS NULL OR L_KATEGO NOT IN (1,2,3,4,5)")
                arcpy.SelectLayerByAttribute_management(lyrName, "ADD_TO_SELECTION", "G_LAGE IS NULL OR G_LAGE NOT IN (1,2,3)")
                desc = arcpy.Describe(lyrName)
                if len(desc.FIDSet) > 0:
                    ErrorList.append(lyrSrcName)

            elif lyrSrcName == "UFHQN":
                arcpy.SelectLayerByAttribute_management(lyrName, "ADD_TO_SELECTION", "L_KATEGO IS NULL OR L_KATEGO NOT IN (1,2,3,4)")
                desc = arcpy.Describe(lyrName)
                if len(desc.FIDSet) > 0:
                    ErrorList.append(lyrSrcName)

            elif lyrSrcName == "GZ100":
                arcpy.SelectLayerByAttribute_management(lyrName, "ADD_TO_SELECTION", "L_KATEGO IS NULL OR L_KATEGO NOT IN (1,2)")
                desc = arcpy.Describe(lyrName)
                if len(desc.FIDSet) > 0:
                    ErrorList.append(lyrSrcName)

            elif lyrSrcName == "GZ300":
                arcpy.SelectLayerByAttribute_management(lyrName, "ADD_TO_SELECTION", "L_KATEGO IS NULL OR L_KATEGO NOT IN (1,2)")
                desc = arcpy.Describe(lyrName)
                if len(desc.FIDSet) > 0:
                    ErrorList.append(lyrSrcName)

            elif lyrSrcName == "FUNKT":
                arcpy.SelectLayerByAttribute_management(lyrName, "ADD_TO_SELECTION", "L_KATEGO IS NULL OR L_KATEGO NOT IN (1,2)")
                desc = arcpy.Describe(lyrName)
                if len(desc.FIDSet) > 0:
                    ErrorList.append(lyrSrcName)

            elif lyrSrcName == "LPAKT":
                arcpy.SelectLayerByAttribute_management(lyrName, "ADD_TO_SELECTION", "L_KATEGO IS NULL OR L_KATEGO NOT IN (1,2,3,4,5)")
                desc = arcpy.Describe(lyrName)
                if len(desc.FIDSet) > 0:
                    ErrorList.append(lyrSrcName)

            elif lyrSrcName in ["GFPKT", "GFLIN", "GFFLA"]:
                arcpy.SelectLayerByAttribute_management(lyrName, "ADD_TO_SELECTION", "L_KATEGO NOT IN (1,2,3,4,5,6,7,8,9,10,11,12,13,14,15)")
                arcpy.SelectLayerByAttribute_management(lyrName, "ADD_TO_SELECTION", "GF_GRAD NOT IN (1,2,3,4)")
                desc = arcpy.Describe(lyrName)
                if len(desc.FIDSet) > 0:
                    ErrorList.append(lyrSrcName)

            elif lyrSrcName in ["OBPKT", "OBLIN", "OBFLA"]:
                arcpy.SelectLayerByAttribute_management(lyrName, "ADD_TO_SELECTION", "L_KATEGO NOT IN (1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17)")
                arcpy.SelectLayerByAttribute_management(lyrName, "ADD_TO_SELECTION", "O_PRIOR NOT IN (1,2,3,4)")
                desc = arcpy.Describe(lyrName)
                if len(desc.FIDSet) > 0:
                    ErrorList.append(lyrSrcName)

            elif lyrSrcName == "FLUSS":
                arcpy.SelectLayerByAttribute_management(lyrName, "ADD_TO_SELECTION", "L_KATEGO NOT IN (1,2,3,4)")
                desc = arcpy.Describe(lyrName)
                if len(desc.FIDSet) > 0:
                    ErrorList.append(lyrSrcName)

            elif lyrSrcName == "MODEL":
                arcpy.SelectLayerByAttribute_management(lyrName, "ADD_TO_SELECTION", "L_KATEGO NOT IN (1,2,3,4,5,6)")
                desc = arcpy.Describe(lyrName)
                if len(desc.FIDSet) > 0:
                    ErrorList.append(lyrSrcName)

            elif lyrSrcName == "QPLIN":
                arcpy.SelectLayerByAttribute_management(lyrName, "ADD_TO_SELECTION", "L_KATEGO IS NULL OR L_KATEGO NOT IN (1,2,3,4,5)")
                desc = arcpy.Describe(lyrName)
                if len(desc.FIDSet) > 0:
                    ErrorList.append(lyrSrcName)


    ##
    # Create formatted list of ErrorList
    MessageContent = ""
    for l in ErrorList:
        MessageContent += "\n{}".format(l)


    ##
    # Define Message
    if len(ErrorList) == 0:
        pythonaddins.MessageBox(
            "Pruefung erfolgreich.\nEintraege in den Domainfeldern entsprechen den vorgegebenen Auswahlwerten.", "INFORMATION", 0)

    else:
        MessageFinal = "ACHTUNG:\n\nEintraege in den Domainfeldern in folgenden Tabellen entsprechen nicht dem vorgegebenen Auswahlwerten:\n" + MessageContent + "\n\nBitte korrigieren! \n"
        pythonaddins.MessageBox(MessageFinal, "FEHLERMELDUNG", 0)

del ErrorList
