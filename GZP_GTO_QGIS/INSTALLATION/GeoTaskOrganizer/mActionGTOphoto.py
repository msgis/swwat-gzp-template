#!/usr/bin/python
# -*- coding: utf-8 -*-
from builtins import str

from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QObject
from qgis.core import QgsProject
import os

class run(QObject):
    def __init__(self, id, gtotool, config, debug):
        super(run, self).__init__()
        try:
            self.debug = debug
            self.gtotool = gtotool
            self.gtomain = gtotool.gtomain
            self.helper = self.gtomain.helper
            self.iface = gtotool.iface
            self.info = gtotool.info

            self.result = False
            # tool data
            layer = config['layer']
            field = config['field']
            path = config.get('dir',self.gtomain.metadata.dirPictures)
            msg_nofeat = config.get('msg_nofeat',"Kein Objekt selektiert!")
            msg_morethanonefeat = config.get('msg_morethanonefeat', "Mehr als ein Objekt selektiert!")
            msg_save = config.get( 'msg_save', "Foto speichern?")
            msg_overwrite = config.get('msg_overwrite', "Bestehendes Foto überschreiben?")
            cam_index= config.get('camera',0)
            if self.debug: self.info.log("msg_nofeat:", msg_nofeat)
            #check conditions
            feat = None
            layers = QgsProject.instance().mapLayersByName(layer)
            if layers:
                layer = layers[0]  # duplicte names => take the first
            else:
                return
            for f in layer.selectedFeatures():
                if feat is None:
                    feat =f
                else:
                    self.info.msg(msg_morethanonefeat)
                    return
            if feat is None:
                self.info.msg(msg_nofeat)
            else:
                try:
                    #capture camera
                    import cv2
                    import time
                    self.info.log ("Version:", cv2.__version__)
                    camera = cv2.VideoCapture(cam_index)
                    check, frame = camera.read()
                    if check:
                        while True:
                            check, frame = camera.read()
                            #gray = cv2.cvtColor(frame,cv2.COLOR_BAYER_BG2GRAY)
                            cv2.imshow(cv2.__version__ + "  Beliebige Taste für Beenden drücken",frame)
                            key = cv2.waitKey(10)
                            if self.debug: self.info.log ("key:",str(key))
                            if key != -1:#== ord('q'):
                                break
                    camera.release()
                    cv2.destroyAllWindows()
                except Exception as e:
                    self.info.gtoWarning(e.args)
                    return
                if not check:
                    self.info.gtoWarning("Kamera nicht bereit!")
                    return
                value = feat[field]
                if self.debug: self.info.log("Value:",value,type(value))
                if value:
                    reply = QMessageBox.question(self.iface.mainWindow(), 'Photo',msg_overwrite, QMessageBox.Yes, QMessageBox.No)
                else:
                    reply = QMessageBox.question(self.iface.mainWindow(), 'Photo',msg_save , QMessageBox.Yes,QMessageBox.No)

                if reply == QMessageBox.Yes:
                    if not layer.isEditable(): layer.startEditing()
                    file = self.gtomain.helper.getTableName(layer)
                    file= file + "_ID" + str(feat.id())
                    file = file + "_TS" + self.gtomain.helper.timestamp() + '.png'
                    self.info.log("Type: ", type(frame))
                    cv2.imwrite( os.path.join(path,file), frame)
                    feat[field] =  path + "/" + file
                    layer.updateFeature(f)
                    layer.endEditCommand()
                    self.result = True
        except Exception as e:
            self.info.err(e)
            try:
                layer.destroyEditCommand()
            except:
                pass
