"""
@author: ms.gis, June 2020
Script for QGIS GTO for Modul GZP

"""

import re
from qgis.core import ( QgsProject, 
                        QgsVectorLayer, 
                        QgsMapLayer)
from PyQt5.QtWidgets import (QMessageBox,
                             QProgressDialog,
                             QApplication)


def pruefungPFLICHT_LAYER(iface):

    # Display Progress Dialog
    dialog = QProgressDialog()
    dialog.setWindowTitle("IN ARBEIT ... Bitte warten ...")
    dialog.setLabelText("Prüfe, ob alle Pflichtdatensätze befüllt ... Bitte warten...")
    dialog.setMinimumWidth(200)
    dialog.setCancelButton(None)
    dialog.show()

    
    # Identify compulsory layers without entries/ features
    lyrList = []
    countBGef = 0
    countObj = 0

    legend = [tree_layer.layer() for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
    for layer in legend:
        if not layer.name().startswith('DOM') and layer.type() != QgsMapLayer.RasterLayer:
            SrcName = layer.source().split('|layername=')[1].split('|')[0]
            
            if SrcName in ["TBPRJ", "TBGEN", "PLGBT", "TBGZP", "TBGGN", "GSCHUTZ", "LPAKT", "FLUSS", "MODEL"]:
                count = layer.featureCount()
                if count == 0:
                    lyrList.append(SrcName)
                
            elif SrcName == "UFHQN":
                listKat = [] 
                feats = layer.getFeatures()
                for feat in feats:
                    listKat.append(feat["L_KATEGO"])                
                # Check that all categories (1,2,3) present
                if not {1,2,3}.issubset(listKat):
                    lyrList.append(SrcName)

            elif SrcName == "GZ100":
                # Access unfiltered source layer
                SrcLayer = layer.source().split("|subset")[0]
                vLyrGZ100 = QgsVectorLayer(SrcLayer, "vLyrGZ100", "ogr")
                
                listKat = []
                feats = vLyrGZ100.getFeatures()
                for feat in feats:
                    listKat.append(feat["L_KATEGO"])
                #Check that categories (1, 2) present
                if not {1, 2}.issubset(listKat):
                    lyrList.append(SrcName)

            elif SrcName == "GZ300":
                listKat = []
                feats = layer.getFeatures()
                for feat in feats:
                    listKat.append(feat["L_KATEGO"])                
                # Check that category "Gelb-schraffierte Zone" (2) present
                if 2 not in set(listKat):
                    lyrList.append(SrcName)

            elif SrcName == "FUNKT":
                listKat = []
                feats = layer.getFeatures()
                for feat in feats:
                    listKat.append(feat["L_KATEGO"])                
                # Check that category "Rot-Gelb-schraffierter Funktionsbereich" present
                if 1 not in set(listKat):
                    lyrList.append(SrcName)

            elif SrcName == "KNTPKT":
                listKat = []
                feats = layer.getFeatures()
                for feat in feats:
                    listKat.append(feat["SZENARIO"])
                # Check that all szenarios (30, 100, 300) present
                if not {30, 100, 300}.issubset(listKat):
                    lyrList.append(SrcName)

            elif SrcName == "GPLBAU":
                listKat = []
                feats = layer.getFeatures()
                for feat in feats:
                    listKat.append(feat["L_KATEGO"])                
                # Check that category "beplant od. verbaut" (1) present
                if 1 not in set(listKat):
                    lyrList.append(SrcName)
                
            elif SrcName == "BWERT":
                listKat = [] 
                feats = layer.getFeatures()
                for feat in feats:
                    listKat.append(feat["SZENARIO"])                
                # Check that all szenarios (30, 100, 300) present
                if not {30, 100, 300}.issubset(listKat):
                    lyrList.append(SrcName)
                    
            elif SrcName in ["GFPKT", "GFLIN", "GFFLA"]:
                countBGef += layer.featureCount()
                
            elif SrcName in ["OBPKT", "OBLIN", "OBFLA"]:
                countObj += layer.featureCount()
                
            elif SrcName == "QPLIN":
                listKat = []
                feats = layer.getFeatures()
                for feat in feats:
                    listKat.append(feat["L_KATEGO"])
                # Check that at least categories 1 & 2 present
                if not {1,2}.issubset(listKat):
                    lyrList.append(SrcName)

            QApplication.processEvents()
                    
    # Test if at least one feature of Besondere Gefährdungen or Objekte present
    if countBGef == 0:
        lyrList.append("GFPKT, GFLIN oder GFFLA")
    if countObj == 0:
        lyrList.append("OBPKT, OBLIN oder OBFLA")    

    # Message content
    MessageContent = ''
    for l in sorted(set(lyrList)):
        MessageContent += "\n{}".format(l)

    dialog.hide()

    # Define Message
    if len(lyrList) == 0:
        QMessageBox.information(None, "INFORMATION", "Prüfung erfolgreich!\nAlle Pflichtlayer sind befüllt.")
    else:
        MessageFinal = "ACHTUNG:\n\nFolgende Pflichtdatensätze sind nicht (ausreichend) befüllt:\n" + MessageContent + "\n\nBitte korrigieren!!!\n"
        QMessageBox.critical(None, "FEHLERMELDUNG", MessageFinal)

def pruefungPFLICHT_FELDER(iface):
    
    # Get TBPROJ via source name

    edvkz = None    # Set edvkz Null in case no TBPRJ entry

    legend = [tree_layer.layer() for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
    for layer in legend:
        if not layer.name().startswith('DOM') and layer.type() != QgsMapLayer.RasterLayer:
            SrcName = layer.source().split('|layername=')[1].split('|')[0]
            
            if SrcName == "TBPRJ":
                
                # Get edvkz
                feats = layer.getFeatures()
                for feat in feats:
                    edvkz = feat["EDVKZ"]

    # Error Messages if edvkz not correct format
    if edvkz in (None, '',' ','<Null>') or not re.match("^\d[A-Z]\d{6}$",edvkz):
        MessageNULL = 'ACHTUNG:\n\nIn der Projekttabelle (TBPRJ) ist das Feld "EDVKZ" nicht korrekt befüllt (leer bzw. keine EDVKZ).\nBitte korrigieren bevor die Prüfung aller Layer möglich ist!\n'
        QMessageBox.critical(None, "FEHLERMELDUNG", MessageNULL)

    # If correct format proceed with checking of other layers
    else:
        
        queryEDVKZ = "EDVKZ IS NULL OR EDVKZ IN ('',' ','<Null>') OR EDVKZ != '{}'".format(edvkz)
        queryKURZRID = "KURZRID IS NULL OR KURZRID IN ('',' ','<Null>')"
        queryGGN_VERS_1 = "GGN_VERS IS NULL OR GGN_VERS IN ('',' ','<Null>')"
        queryGGN_VERS_2 = "(GGN_VERS IS NULL OR GGN_VERS IN ('',' ','<Null>')) AND (G_NEU_OK IS NULL OR GGN_VERS IN ('',' ','<Null>'))"
        queryAK_DATUM = "AK_DATUM IS NULL OR AK_DATUM IN ('',' ','<Null>')"
        queryA_AGORG = "A_AGORG IS NULL OR A_AGORG IN ('',' ','<Null>')"
        queryA_PLANER = "A_PLANER IS NULL OR A_PLANER IN ('',' ','<Null>')"
        queryA_DIG_DAT = "A_DIG_DAT IS NULL OR A_DIG_DAT IN ('',' ','<Null>')"
        queryGEN_ZAHL = "GEN_ZAHL IS NULL OR GEN_ZAHL IN ('',' ','<Null>')"
        queryGEN_DAT = "GEN_DAT IS NULL OR GEN_DAT IN ('',' ','<Null>')"
        querySZENARIO = "SZENARIO IS NULL OR SZENARIO IN ('',' ','<Null>')"
        queryQMAX = "QMAX IS NULL OR QMAX IN ('',' ','<Null>')"


        # Check mandatory fields in other layers and select not compliant entries
        legend = [tree_layer.layer() for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
        for layer in legend:
            if not layer.name().startswith('DOM') and layer.type() != QgsMapLayer.RasterLayer:
                SrcName = layer.source().split('|layername=')[1].split('|')[0]
                
                if SrcName == "TBPRJ":
                    # layer.selectByExpression(queryEDVKZ,0)    # Circular Test
                    layer.selectByExpression(queryAK_DATUM,0)
                    layer.selectByExpression(queryA_AGORG,1)
                    layer.selectByExpression(queryA_PLANER,1)
                    layer.selectByExpression(queryA_DIG_DAT,1)
                
                elif SrcName == "TBGEN":
                    layer.selectByExpression(queryEDVKZ,0)
                    layer.selectByExpression(queryGEN_ZAHL,1)
                    layer.selectByExpression(queryGEN_DAT,1)
                
                elif SrcName in ("PLGBT","GPLBAU","GSCHUTZ","LPAKT"):
                    layer.selectByExpression(queryEDVKZ,0)
                    layer.selectByExpression(queryKURZRID,1)
                    layer.selectByExpression(queryGGN_VERS_1,1)
                    layer.selectByExpression(queryAK_DATUM,1)
                
                elif SrcName in ("TBGZP","GFPKT","GFLIN","GFFLA","FLUSS"):
                    layer.selectByExpression(queryEDVKZ,0)
                    layer.selectByExpression(queryAK_DATUM,1)
                
                elif SrcName == "TBGGN":
                    layer.selectByExpression(queryEDVKZ,0)
                    layer.selectByExpression(queryKURZRID,1)
                    layer.selectByExpression(queryGGN_VERS_2,1)
                    layer.selectByExpression(queryAK_DATUM,1)
                
                elif SrcName in ("UFHQN","GZ100","GZ300","FUNKT"):
                    layer.selectByExpression(queryEDVKZ,0)
                    layer.selectByExpression(queryKURZRID,1)
                    layer.selectByExpression(queryGGN_VERS_1,1)
                    layer.selectByExpression(queryAK_DATUM,1)
                    layer.selectByExpression(querySZENARIO,1)
                
                elif SrcName in ("OBPKT","OBLIN","OBFLA","MODEL","QPLIN"):
                    layer.selectByExpression(queryEDVKZ,0)
                    layer.selectByExpression(queryAK_DATUM,1)
                    layer.selectByExpression(querySZENARIO,1)
                
                elif SrcName in ("BWERT"):
                    layer.selectByExpression(queryEDVKZ,0)
                    layer.selectByExpression(querySZENARIO, 1)
                    layer.selectByExpression(queryQMAX, 1)
        
        # Identify layer with selection
        lyrList = []

        legend = [tree_layer.layer() for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
        for layer in legend:
            if not layer.name().startswith('DOM') and layer.type() != QgsMapLayer.RasterLayer:
                SrcName = layer.source().split('|layername=')[1].split('|')[0]
                count = layer.selectedFeatureCount()
                if count > 0:
                    lyrList.append(SrcName)

        # Message content
        MessageContent = ''
        for l in lyrList:
            MessageContent += "\n{}".format(l)

        # Define Message
        if len(lyrList) == 0:
            QMessageBox.information(None, "INFORMATION", "Prüfung erfolgreich!\nAlle Pflichtfelder befüllt.")
        else:
            MessageFinal = "ACHTUNG:\n\nEin oder mehrere Pflichtfelder in folgenden Datensätzen nicht befüllt bzw. ist die EDVKZ inkorrekt:\n" + MessageContent + "\n\nBitte korrigieren!!!\n"
            QMessageBox.critical(None, "FEHLERMELDUNG", MessageFinal)

def pruefungPFLICHT_FELDER_KNTPKT(iface):
    # Get TBPROJ via source name
    
    edvkz = None  # Set edvkz Null in case no TBPRJ entry
    
    legend = [tree_layer.layer() for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
    for layer in legend:
        if not layer.name().startswith('DOM') and layer.type() != QgsMapLayer.RasterLayer:
            SrcName = layer.source().split('|layername=')[1].split('|')[0]
            
            if SrcName == "TBPRJ":
                
                # Get edvkz
                feats = layer.getFeatures()
                for feat in feats:
                    edvkz = feat["EDVKZ"]
    
    # Error Messages if edvkz not correct format
    if edvkz in (None, '', ' ', '<Null>') or not re.match("^\d[A-Z]\d{6}$", edvkz):
        MessageNULL = 'ACHTUNG:\n\nIn der Projekttabelle (TBPRJ) ist das Feld "EDVKZ" nicht korrekt befüllt (leer bzw. keine EDVKZ).\nBitte korrigieren bevor die Prüfung aller Layer möglich ist!\n'
        QMessageBox.critical(None, "FEHLERMELDUNG", MessageNULL)
    
    # If correct format proceed with checking of other layers
    else:
        
        queryEDVKZ = "EDVKZ IS NULL OR EDVKZ IN ('',' ','<Null>') OR EDVKZ != '{}'".format(edvkz)
        querySZENARIO = "SZENARIO IS NULL OR SZENARIO IN ('',' ','<Null>')"
        queryKN_Z = "KN_Z IS NULL OR KN_Z IN ('',' ','<Null>')"
        queryKN_FLAECH = "KN_FLAECH IS NULL OR KN_FLAECH IN ('',' ','<Null>')"
        queryWT_MAX = "WT_MAX IS NULL OR WT_MAX IN ('',' ','<Null>')"
        queryFG_MAX = "FG_MAX IS NULL OR FG_MAX IN ('',' ','<Null>')"
        queryQF_SUM = "QF_SUM IS NULL OR QF_SUM IN ('',' ','<Null>')"
        
        
        # Check mandatory fields in other layers and select not compliant entries
        legend = [tree_layer.layer() for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
        for layer in legend:
            if not layer.name().startswith('DOM') and layer.type() != QgsMapLayer.RasterLayer:
                SrcName = layer.source().split('|layername=')[1].split('|')[0]
                
                if SrcName in ("KNTPKT"):
                    layer.selectByExpression(queryEDVKZ,0)
                    layer.selectByExpression(querySZENARIO, 1)
                    layer.selectByExpression(queryKN_Z, 1)
                    layer.selectByExpression(queryKN_FLAECH, 1)
                    layer.selectByExpression(queryWT_MAX, 1)
                    layer.selectByExpression(queryFG_MAX, 1)
                    layer.selectByExpression(queryQF_SUM, 1)
        
        # Identify layer with selection
        lyrList = []
        
        legend = [tree_layer.layer() for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
        for layer in legend:
            if not layer.name().startswith('DOM') and layer.type() != QgsMapLayer.RasterLayer:
                SrcName = layer.source().split('|layername=')[1].split('|')[0]
                
                if SrcName in ("KNTPKT"):
                    count = layer.selectedFeatureCount()
                    if count > 0:
                        lyrList.append(SrcName)
        
        # Message content
        MessageContent = ''
        for l in lyrList:
            MessageContent += "\n{}".format(l)
        
        # Define Message
        if len(lyrList) == 0:
            QMessageBox.information(None, "INFORMATION", "Prüfung erfolgreich!\nAlle Pflichtfelder im Layer Knotenpunkte (KNTPKT) befüllt.")
        else:
            MessageFinal = "ACHTUNG:\n\nEin oder mehrere Pflichtfelder im Layer Knotenpunkte (KNTPKT) nicht befüllt bzw. ist die EDVKZ inkorrekt:\n" + MessageContent + "\n\nBitte korrigieren!\n"
            QMessageBox.critical(None, "FEHLERMELDUNG", MessageFinal)

def pruefungDOM(iface):

    # Check mandatory fields in other layers and select not compliant entries
    legend = [tree_layer.layer() for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
    for layer in legend:
        if not layer.name().startswith('DOM') and layer.type() != QgsMapLayer.RasterLayer:
            SrcName = layer.source().split('|layername=')[1].split('|')[0]

            if SrcName == "TBPRJ":
                layer.selectByExpression("PRJ_TYP IS NULL OR PRJ_TYP NOT IN (5,6,16)",0)
                layer.selectByExpression("FIN_ART IS NULL OR FIN_ART NOT IN (1,2,3)",1)
            elif SrcName == "TBGEN":
                layer.selectByExpression("GEN_ORG IS NULL OR GEN_ORG NOT IN (1,2,3,4)",0)
                layer.selectByExpression("GEN_ART IS NULL OR GEN_ART NOT IN (1,2,3,4)",1)
            elif SrcName == "GPLBAU":
                layer.selectByExpression("L_KATEGO IS NULL OR L_KATEGO NOT IN (1,2,3)",0)
            elif SrcName == "GSCHUTZ":
                layer.selectByExpression("L_KATEGO IS NULL OR L_KATEGO NOT IN (1,2,3,4,5)",0)
                layer.selectByExpression("G_LAGE IS NULL OR G_LAGE NOT IN (1,2,3)",1)
            elif SrcName == "TBGZP":
                layer.selectByExpression("BERECH_M IS NULL OR BERECH_M NOT IN (1,2,3,4)",0)
                layer.selectByExpression("DIMENS_M NOT IN (1,2,3)",1)
                layer.selectByExpression("M_HWENT NOT IN (1,2,3)",1)
            elif SrcName == "UFHQN":
                layer.selectByExpression("L_KATEGO IS NULL OR L_KATEGO NOT IN (1,2,3,4)",0)
            elif SrcName == "GZ100":
                layer.selectByExpression("L_KATEGO IS NULL OR L_KATEGO NOT IN (1,2)",0)
            elif SrcName == "GZ300":
                layer.selectByExpression("L_KATEGO IS NULL OR L_KATEGO NOT IN (1,2)",0)
            elif SrcName == "FUNKT":
                layer.selectByExpression("L_KATEGO IS NULL OR L_KATEGO NOT IN (1,2)",0)
            elif SrcName == "LPAKT":
                layer.selectByExpression("L_KATEGO IS NULL OR L_KATEGO NOT IN (1,2,3,4,5)",0)
            elif SrcName in ["GFPKT", "GFLIN", "GFFLA"]:
                layer.selectByExpression("L_KATEGO NOT IN (1,2,3,4,5,6,7,8,9,10,11,12,13,14,15)",0)
                layer.selectByExpression("GF_GRAD NOT IN (1,2,3,4)",1)
            elif SrcName in ["OBPKT", "OBLIN", "OBFLA"]:
                layer.selectByExpression("L_KATEGO NOT IN (1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17)",0)
                layer.selectByExpression("O_PRIOR NOT IN (1,2,3,4)",1)
            elif SrcName == "FLUSS":
                layer.selectByExpression("L_KATEGO NOT IN (1,2,3,4)",0)
            elif SrcName == "MODEL":
                layer.selectByExpression("L_KATEGO NOT IN (1,2,3,4,5,6)",0)
            elif SrcName == "QPLIN":
                layer.selectByExpression("L_KATEGO IS NULL OR L_KATEGO NOT IN (1,2,3,4,5)",0)


    # Identify layer with selection
    lyrList = []

    legend = [tree_layer.layer() for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
    for layer in legend:
        if not layer.name().startswith('DOM') and layer.type() != QgsMapLayer.RasterLayer:
            SrcName = layer.source().split('|layername=')[1].split('|')[0]

            count = layer.selectedFeatureCount()
            if count > 0:
                lyrList.append(SrcName)

    # Message content
    MessageContent = ''
    for l in lyrList:
        MessageContent += "\n{}".format(l)

    # Define Message
    if len(lyrList) == 0:
        QMessageBox.information(None, "INFORMATION", "Prüfung erfolgreich!\nEinträge in den Domainfeldern entsprechen den vorgegebenen Auswahlwerten.")
    else:
        MessageFinal = "ACHTUNG:\n\nEinträge in den Domainfeldern in folgenden Tabellen entsprechen nicht dem vorgegebenen Auswahlwerten:\n" + MessageContent + "\n\nBitte korrigieren!\n"
        QMessageBox.critical(None, "FEHLERMELDUNG", MessageFinal)
