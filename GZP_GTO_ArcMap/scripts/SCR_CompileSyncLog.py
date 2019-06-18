# -*- coding: utf-8 -*-
"""
@author: ms.gis, May 2019
Script for ArcGIS GTO for Modul GZP

"""

import arcpy
import datetime
import os
import pythonaddins

## -------------------------
# Open progress dialog

with pythonaddins.ProgressDialog as dialog:
	dialog.title = "Progress Dialog"
	dialog.description = "Befuelle Sync Log Tabelle fuer den Datenupload ... Bitte warten..."
	dialog.animation = "Spiral"

# -------------------------
	# Get .gdb path

	# List of relevant layer
	dsList = [u'BWERT', u'LPAKT', u'GSCHUTZ', u'QPLIN', u'PLGBT', u'MODEL', u'KNTPKT', u'GFPKT', u'GFLIN', u'GFFLA', u'GZ100', u'FUNKT', u'GZ300', u'UFHQN', u'TBGGN', u'TBGZP', u'TBPRJ', u'TBGEN']

	# Access current mxd
	mxd = arcpy.mapping.MapDocument("CURRENT")

	# Get .gdb path from first layer that is in dsList
	for l in arcpy.mapping.ListLayers(mxd):
		if l.isFeatureLayer:
			if l.datasetName in dsList:
				gdbPath = os.path.split(l.dataSource)[0]
				break

	## -------------------------
	# Write from layers to GTO sync log

	# Define path to GTO Sync Log
	syncLog = os.path.join(gdbPath,'GTO_SYNC_LOG')

	# Delete content GTO Sync Log
	arcpy.DeleteRows_management(syncLog)

	# Set timestamp value
	entry = 0
	syncTimeStamp = datetime.datetime.now().strftime('%Y.%m.%d %H:%M:%S')

	# Set insert cursor on GTO Sync Log
	with arcpy.da.InsertCursor(syncLog, ["GTO_FC_NAME", "GTO_SQLITE_ID", "GTO_OP", "GTO_OP_DATE", "GTO_ENT_ID", "GTO_ID"]) as curs1:

		# Get list of tables in .gdb
		walk = arcpy.da.Walk(gdbPath, datatype=["Table","FeatureClass"])
		for dirpath, dirnames, filenames in walk:
			for filename in filenames:

				# Reduce to relevant datasets
				if not filename.startswith("DOM") and not filename.startswith("GTO"):
					dSource = os.path.join(dirpath,filename)

					# Set read cursor on dataset
					with arcpy.da.SearchCursor(dSource, ["OID@"]) as curs2:
						for row2 in curs2:
							entry += 1
							curs1.insertRow((filename, row2[0], "C", syncTimeStamp, row2[0], entry))

MessageFinal = "Befuellen der Sync Log Tabelle erfolgreich abgeschlossen"
pythonaddins.MessageBox(MessageFinal, "INFORMATION", 0)
