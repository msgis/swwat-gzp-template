# -*- coding: utf-8 -*-
"""
@author: ms.gis, March 2019
Script for ArcGIS GTO for Modul GZP

"""

import arcpy
import pythonaddins

# Set counter and message content
ErrorCount = 0
MessageInhalt = ""


# Test projection
mxd = arcpy.mapping.MapDocument("CURRENT")

for lyr in arcpy.mapping.ListLayers(mxd):

	# get spatial reference  
	if lyr.isFeatureLayer:
		crs = arcpy.Describe(lyr).spatialReference.factorycode
		
		# print warning if not epsg 31287
		if crs != 31287:
			ErrorCount += 1
			MessageInhalt += "{}\n".format(lyr.datasetName)
	
	else:
		pass

if ErrorCount == 0:
	pythonaddins.MessageBox ("Pruefung erfolgreich abgeschlossen. \nAlle Feature Layer liegen in MGI Austria Lambert (EPSG: 31287) vor.", "INFORMATION", 0)
		
else:
	MessageFinal = "ACHTUNG:\n\nFolgende Layer liegen nicht in MGI Austria Lambert (EPSG: 31287) vor: \n\n" + MessageInhalt + "\nBitte korrigieren!!! \n"
	pythonaddins.MessageBox (MessageFinal, "FEHLERMELDUNG", 0)