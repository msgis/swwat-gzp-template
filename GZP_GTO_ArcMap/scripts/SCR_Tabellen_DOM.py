# -*- coding: utf-8 -*-
"""
@author: ms.gis, March 2019
Script for ArcGIS GTO for Modul GZP

"""

##
import arcpy
import pythonaddins

# Access current map document
mxd = arcpy.mapping.MapDocument("CURRENT")

# Clear all previous selections
for tbl in arcpy.mapping.ListTableViews(mxd):
	tblName = tbl.name
	arcpy.SelectLayerByAttribute_management(tblName, "CLEAR_SELECTION")

# Create List for Message Content
ErrorList = []

# Loop through tables in map document
for tbl in arcpy.mapping.ListTableViews(mxd):
	tblSrcName = tbl.datasetName
	tblName = tbl.name

	if tblSrcName == "TBGGN":
		arcpy.SelectLayerByAttribute_management(tblName, "ADD_TO_SELECTION", "G_BEPLAN NOT BETWEEN 1 AND 3")
		desc = arcpy.Describe(tblName)
		if len(desc.FIDSet) > 0:
			ErrorList.append(tblSrcName)
	
	if tblSrcName == "TBGZP":
		arcpy.SelectLayerByAttribute_management(tblName, "ADD_TO_SELECTION", "BERECH_M NOT BETWEEN 1 AND 4")
		arcpy.SelectLayerByAttribute_management(tblName, "ADD_TO_SELECTION", "DIMENS_M NOT BETWEEN 1 AND 3")
		arcpy.SelectLayerByAttribute_management(tblName, "ADD_TO_SELECTION", "M_HWENT NOT BETWEEN 1 AND 3")
		desc = arcpy.Describe(tblName)
		if len(desc.FIDSet) > 0:
			ErrorList.append(tblSrcName)
		
	if tblSrcName == "TBPRJ":
		arcpy.SelectLayerByAttribute_management(tblName, "ADD_TO_SELECTION", "PRJ_TYP NOT IN (NULL,5,6,15)")
		arcpy.SelectLayerByAttribute_management(tblName, "ADD_TO_SELECTION", "FIN_ART NOT BETWEEN 1 AND 3")
		desc = arcpy.Describe(tblName)
		if len(desc.FIDSet) > 0:
			ErrorList.append(tblSrcName)
		
	if tblSrcName == "TBGEN":
		arcpy.SelectLayerByAttribute_management(tblName, "ADD_TO_SELECTION", "GEN_ORG NOT BETWEEN 1 AND 4")
		arcpy.SelectLayerByAttribute_management(tblName, "ADD_TO_SELECTION", "GEN_ART NOT BETWEEN 1 AND 4")
		desc = arcpy.Describe(tblName)
		if len(desc.FIDSet) > 0:
			ErrorList.append(tblSrcName)


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
	MessageFinal = "ACHTUNG:\n\nEintraege in den Domainfeldern in folgenden Tabellen entsprechen nicht dem vorgegebenen Auswahlwerten:\n" + MessageContent + "\n\nBitte korrigieren!!! \n"
	pythonaddins.MessageBox(MessageFinal, "FEHLERMELDUNG", 0)
