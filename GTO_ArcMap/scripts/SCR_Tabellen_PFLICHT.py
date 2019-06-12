# -*- coding: utf-8 -*-
"""
@author: ms.gis, March 2019
Script for ArcGIS GTO for Modul GZP

"""

##
import arcpy
import pythonaddins

mxd = arcpy.mapping.MapDocument("CURRENT")

# Clear all previous selections
for tbl in arcpy.mapping.ListTableViews(mxd):
	tblName = tbl.name
	arcpy.SelectLayerByAttribute_management(tblName, "CLEAR_SELECTION")

# Create list for message content
ErrorList = []

# Loop through tables in map document
for tbl in arcpy.mapping.ListTableViews(mxd):
	tblSrcName = tbl.datasetName
	tblName = tbl.name
	
	if tblSrcName == "TBGGN":
		arcpy.SelectLayerByAttribute_management(tblName, "ADD_TO_SELECTION", "EDVKZ IS NULL OR EDVKZ = '' OR EDVKZ = ' '  OR EDVKZ = '<Null>'")
		desc = arcpy.Describe(tblName)
		if len(desc.FIDSet) > 0:
			ErrorList.append(tblSrcName)
	
	if tblSrcName == "TBGZP":
		arcpy.SelectLayerByAttribute_management(tblName, "ADD_TO_SELECTION", "EDVKZ IS NULL OR EDVKZ = '' OR EDVKZ = ' '  OR EDVKZ = '<Null>'")
		desc = arcpy.Describe(tblName)
		if len(desc.FIDSet) > 0:
			ErrorList.append(tblSrcName)
	
	if tblSrcName == "TBPRJ":
		prjres1 = arcpy.GetCount_management(tblName)
		arcpy.SelectLayerByAttribute_management(tblName, "ADD_TO_SELECTION", "EDVKZ IS NULL OR EDVKZ = '' OR EDVKZ = ' '  OR EDVKZ = '<Null>'")
		desc = arcpy.Describe(tblName)
		if int(prjres1.getOutput(0)) == 0 or len(desc.FIDSet) > 0:
			ErrorList.append(tblSrcName)
	
	if tblSrcName == "TBGEN":
		arcpy.SelectLayerByAttribute_management(tblName, "ADD_TO_SELECTION", "EDVKZ IS NULL OR EDVKZ = '' OR EDVKZ = ' '  OR EDVKZ = '<Null>'")
		desc = arcpy.Describe(tblName)
		if len(desc.FIDSet) > 0:
			ErrorList.append(tblSrcName)

##
MessageContent = ""
for l in ErrorList:
	MessageContent += "\n{}".format(l)

##
# Define Message
if len(ErrorList) == 0:
	pythonaddins.MessageBox(
		"Pruefung erfolgreich.\nAlle Pflichtfelder befuellt.", "INFORMATION", 0)

else:
	MessageFinal = "ACHTUNG:\n\nEin oder mehrere Pflichtfelder in folgenden Tabellen nicht befuellt:\n" + MessageContent + "\n\nBitte korrigieren!!! \n"
	pythonaddins.MessageBox(MessageFinal, "FEHLERMELDUNG", 0)

del ErrorList
