# -*- coding: utf-8 -*-
"""
@author: ms.gis, May 2020
Script for ArcGIS GTO for Modul GZP

"""

##
import arcpy
import pythonaddins
import arcpy.da
import json
import inspect
import os
import sys


## -------------------------
# Open progress dialog

with pythonaddins.ProgressDialog as dialog:
    dialog.title = "PRUEFUNG DATENSCHEMA"
    dialog.description = "Pruefe Datenschema aller Layer ... Bitte warten..."
    dialog.animation = "Spiral"


    ## -------------------------
    # Open dictionary containing schema of GZP Datenmodell
    try:
        # locate dictionary and define relative path
        filename = inspect.getframeinfo(inspect.currentframe()).filename
        JPath = os.path.dirname(os.path.abspath(filename))
        SchemaPath = os.path.join(JPath, r'schemaVorgabe.json')

        # open dictionary
        with open(SchemaPath, 'r') as f:
          schema = json.load(f)
    except IOError:
        raise pythonaddins.MessageBox('''Datei "schemaVorgabe.json" nicht gefunden''', "FEHLERMELDUNG", 0)



    ## -------------------------
    # Create schema file of mxd
    mxd = arcpy.mapping.MapDocument("CURRENT")

    # create dictionary of schema .gdb
    schemaIN = {}
    for lyr in arcpy.mapping.ListLayers(mxd):

        if lyr.isFeatureLayer:
            dsName = lyr.datasetName
            dsFields = arcpy.ListFields(lyr.dataSource)
            dsshapeType = arcpy.Describe(lyr.dataSource).shapeType

            lFields =[]
            for field in dsFields :

                # translate name
                if field.name in [u'oid', u'fid', u'id']:
                    fname = unicode('ID')
                elif field.name in [u'geom', u'Shape']:
                    fname = unicode('SHAPE')
                else:
                    fname = field.name

                # translate dsshapeType
                if dsshapeType == u'Polygon':
                    shType = unicode('MultiPolygon')
                elif dsshapeType == u'Polyline':
                    shType = unicode('MultiLineString')
                else:
                    shType = dsshapeType

                # translate type
                if field.type == u'OID':
                    ftype = unicode('INTEGER')
                elif field.type == u'String':
                    ftype = unicode('TEXT')
                elif field.type == u'Integer':
                    ftype = unicode('INTEGER')
                elif field.type == u'Date':
                    ftype = unicode('DATE')
                elif field.type == u'Geometry':
                    ftype = unicode(shType)
                elif field.type == u'Double':
                    ftype = unicode('REAL')
                else:
                    ftype = field.type

                tfield = (fname, ftype)
                lFields.append(tfield)

            schemaIN[dsName] = {a:[b] for a, b in lFields}


    for tbl in arcpy.mapping.ListTableViews(mxd):
        tblName = tbl.datasetName
        tblFields = arcpy.ListFields(tbl.dataSource)

        lFields = []
        for field in tblFields:

            # translate name
            if field.name in [u'oid', u'fid', u'id']:
                fname = unicode('ID')
            else:
                fname = field.name

            # translate type
            if field.type == u'OID':
                ftype = unicode('INTEGER')
            elif field.type == u'String':
                ftype = unicode('TEXT')
            elif field.type == u'Integer':
                ftype = unicode('INTEGER')
            elif field.type == u'Date':
                ftype = unicode('DATE')
            elif field.type == u'Geometry':
                ftype = unicode(shType)
            elif field.type == u'Double':
                ftype = unicode('REAL')
            else:
                ftype = field.type

            tfield = (fname, ftype)
            lFields.append(tfield)

        schemaIN[tblName] = {a:[b] for a, b in lFields}


    ## compare schemas and write messages
    # Set up counter and message content
    ErrorCount = 0
    MessageDict = {}

    for keyDM in schema.keys():

        if not keyDM.startswith('DOM_'):
            MessageDict[keyDM] = {}

            # TEST 1 - table exists
            if keyDM in schemaIN.keys():

                # TEST 2 - Field exists
                MessageDict[keyDM]["Feld nicht gefunden"] = []
                MessageDict[keyDM]["Data Typ inkorrekt in Feld"] = []
                for fname in schema[keyDM].keys():
                    if fname in schemaIN[keyDM].keys():
                        pass

                        # TEST 3 - Field has correct attributes
                        # data type
                        if schema[keyDM][fname][0] == schemaIN[keyDM][fname][0]:
                            pass
                        else:
                            ErrorCount += 1
                            MessageDict[keyDM]["Data Typ inkorrekt in Feld"].append(str(fname))

                    else:
                        ErrorCount += 1
                        MessageDict[keyDM]["Feld nicht gefunden"].append(str(fname))

            else:
                ErrorCount += 1
                MessageDict[keyDM]["Layer/Tabelle nicht gefunden"] = 'NA'


    # Creat interim message dictionary, shortening content
    interimMessContent = {}
    for key1 in MessageDict.keys():
        print(key1)
        interimMessContent[key1] = []
        for key2, val2 in MessageDict[key1].items():
            if val2 == 'NA':
                interimMessContent[key1].append("\n\t{}.".format(key2))       
            if len(val2) != 0 and val2 != 'NA':
                valStr = ""
                for val in val2:
                    valStr += ", "+val
                interimMessContent[key1].append("\n\t{}:   {}".format(key2,valStr[2:]))


    # Define Message Content
    MessageContent = ""
    for key, val in interimMessContent.items():
        if len(val) != 0:
            MessageContent += "\n{}:".format(key)
            for i in val:
                MessageContent += i



##
# Define Message
if ErrorCount == 0:
    pythonaddins.MessageBox(
        "Pruefung erfolgreich abgeschlossen. \nAlle Layer und Tabellen entsprechen dem vorgegebenen Datenschema.",
        "INFORMATION", 0)

else:
    MessageFinal = "ACHTUNG:\n\nFolgende Layer und Tabellen entsprechen nicht dem vorgegebenen Datenschema:\n" + MessageContent + "\n\nBitte korrigieren! \n"
    pythonaddins.MessageBox(MessageFinal, "FEHLERMELDUNG", 0)
