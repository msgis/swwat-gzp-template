# -*- coding: utf-8 -*-
"""
@author: ms.gis, June 2020
Script for QGIS GTO for Modul GZP

"""

##
import qgis
from qgis.core import QgsProject
from qgis.core import QgsMapLayer
from qgis.core import QgsWkbTypes
from PyQt5.QtWidgets import QMessageBox
import json
import inspect, os.path
from pprint import pprint as prettyprint



def testDatenmodell(iface):
    ## -------------------------
    # Open dictionary containing schema of GZP Datenmodell

    # locate dictionary and define relative path
    try:
        filename = inspect.getframeinfo(inspect.currentframe()).filename
        JPath = os.path.dirname(os.path.abspath(filename))
        SchemaPath = os.path.join(JPath,r'schemaVorgabe.json')
#
        # open dictionary
        with open(SchemaPath, 'r') as f:
            schema = json.load(f)
    except FileNotFoundError:
        raise QMessageBox.information(None, "FEHLERMELDUNG", "Datei schemaVorlage.json nicht gefunden")

    ## -------------------------
    # Create schema file from layers in qgz

    # Create dictionary of layer schemas
    schemaIN = {}
    legend = [tree_layer.layer() for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]

    for layer in legend:
        if layer.type() != QgsMapLayer.RasterLayer and not layer.name().startswith('DOM_'):
            dsName = layer.source().split('|layername=')[1].split('|')[0]
            dsFields = layer.fields()
            dsshapeType = QgsWkbTypes().displayString(int(layer.wkbType()))

            lFields = []

            # Add information of fields
            for field in dsFields:
                # translate type
                if field.typeName() == u'Integer64':
                    ftype = unicode('INTEGER')
                elif field.typeName() == u'String':
                    ftype = unicode('TEXT')
                elif field.typeName() == u'Date':
                    ftype = unicode('DATE')
                elif field.typeName() == u'Real':
                    ftype = unicode('REAL')
                else:
                    ftype = field.typeName()

                # translate defaultValue
                if field.defaultValueDefinition().expression() == '':
                    fdefault = None
                else:
                    fdefault = field.defaultValueDefinition().expression()

                tfield = (field.name(), ftype, field.constraints().ConstraintNotNull, fdefault)
                lFields.append(tfield)

            schemaIN[dsName] = {a:(b,c,d) for a,b,c,d in lFields}


            # Add information on shape type
            if dsshapeType == 'Polygon':
                shType = 'MultiPolygon'
            elif dsshapeType == 'LineString':
                shType = 'MultiLineString'
            else:
                shType = dsshapeType

            schemaIN[dsName]['SHAPE'] = (shType,0,None)

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


    # Define Message
    if ErrorCount == 0:
        QMessageBox.information(None, "INFORMATION", "Prüfung erfolgreich abgeschlossen. \nAlle Layer und Tabellen entsprechen dem vorgegebenen Datenschema.")
    else:
        MessageFinal = "ACHTUNG:\n\nFolgende Layer und Tabellen entsprechen nicht dem vorgegebenen Datenschema:\n" + MessageContent + "\n\nBitte korrigieren! \n"
        QMessageBox.information(None, "FEHLERMELDUNG", MessageFinal)
    