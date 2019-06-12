#!/usr/bin/python
# -*- coding: utf-8 -*-

from builtins import str
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import os
import json
import json
import io
from qgis.core import *
from .gto_helper import getFilePath
from .gto_info import gtoInfo


class gtoRemote(QObject):
    def __init__(self, gtomain, parent = None):
        try:
            super(gtoRemote, self).__init__(parent)
            self.gtomain = gtomain
            self.iface = gtomain.iface
            self.debug = gtomain.debug
            self.info = gtoInfo(self)

            if 'remote_watch_file' in gtomain.settings:
                remote_watch_path = getFilePath(gtomain.settings['remote_watch_file'])
                if remote_watch_path is not None:
                    self.remote_watch_file = os.path.basename(remote_watch_path)
                    self.remote_watch_dir = os.path.dirname(remote_watch_path)

                    if self.debug: self.info.log("Watching:",self.remote_watch_dir)
                    if not os.path.exists(self.remote_watch_dir):
                        os.makedirs(self.remote_watch_dir)
                        if self.debug: self.info.log("Created:",self.remote_watch_dir)

                    self.paths = [self.remote_watch_dir]
                    self.fs_watcher = QFileSystemWatcher(self.paths)
                    #if file already exists
                    self.directory_changed(self.paths[0])
                    self.fs_watcher.directoryChanged.connect(self.directory_changed)
                    self.fs_watcher.fileChanged.connect(self.file_changed)
        except Exception as e:
            self.info.err(e)

    def unload(self):
        try:
            self.fs_watcher.disconnect(self.file_changed)
            self.fs_watcher.disconnect(self.directory_changed)
            self.fs_watcher = None
        except Exception as e:
            self.info.err(e)

    def directory_changed(self,path):
        try:
            self.info.log('Directory Changed: %s' % path)
            for f in os.listdir(path):
                #self.info.log(os.listdir(path))
                #if (self.debug and f.lower().endswith(".json")) or f.lower() == self.remote_watch_file.lower():
                if f.lower() == self.remote_watch_file.lower():
                    self.fs_watcher.blockSignals(True)
                    self.excuteCommand(path,f)
                    self.fs_watcher.blockSignals(False)
        except Exception as e:
            self.info.err(e)

    def file_changed(self,path):
        try:
            if self.debug: self.info.log('File Changed: %s' % path)
        except Exception as e:
            self.info.err(e)

    def excuteCommand(self,path,f):
        try:
            if self.debug: self.info.log('excute command')
            filename = path + '/' + f
            #time.sleep(0.5)
            f = io.open(filename, encoding='utf-8')
            jdata = json.load(f)
            f.close()

            res = True
            for cmd in jdata['commands']:
                if self.debug: self.info.log(cmd)
                method = getattr(self, cmd['ecommand'])
                res = res and (method(self.gtomain, self.debug, **cmd['config']))
            if self.debug: self.info.log('result:', res)
            if res:
                os.remove(filename)
        except Exception as e:
            self.info.err(e)

    def writeRemoteFile(self,jdata,prefix = ''):
        try:
            if self.debug: self.info.log('writeRemoteFile:', 'data:', jdata)
            remotefile = self.gtomain.settings['remote_file']
            remotefile = getFilePath(remotefile, True)
            remotefile = '%s%s' % (remotefile,prefix)
            if self.debug: self.info.log("remotefile",remotefile)
            # write the file
            # from io import StringIO
            # io = StringIO()
            # json.dump(jdata,io,ensure_ascii=False, sort_keys=True,indent=4)
            # io.close()
            with open(remotefile, 'w',encoding='utf8') as outfile:
                sort =True
                #simplejson.dump(jdata, outfile,ensure_ascii=False, sort_keys=sort,indent=4)#,encoding='utf8')#.encode('utf8')
                json.dump(jdata, outfile, ensure_ascii=False, sort_keys=sort, indent=4)  # ,encoding='utf8')#.encode('utf8')
            # import pickle
            # with open(remotefile, 'wb') as f:
            #     pickle.dump(jdata,f)

            #activate/start remote app
            if self.debug: self.info.log('writeRemoteFile:', 'settings:',  self.gtomain.settings)
            remote_app_file = self.gtomain.settings['remote_app_file']
            remote_app_title = self.gtomain.settings['remote_app_title']
            if os.name == 'nt':
                try:
                    from .gto_windows import ActivateApp
                    ActivateApp(self.gtomain, self.debug, remote_app_title, remote_app_file)
                except Exception as e:
                    self.info.err(e)
            else:
                os.startfile(remote_app_file)

        except Exception as e:
            self.info.err(e)

    def getLayerByName(self,layername):
        try:
            layers = QgsProject.instance().mapLayersByName(layername)
            if layers:
                return layers[0]# duplicte names => take the first
            else:
                return None
        except Exception as e:
            self.info.err(e)

    def getFeatures(self, gtoobj, debug, **kwargs):
        try:
            if self.debug: self.info.log('getFeatures:', 'parameters:', kwargs)
            layername = kwargs['objectclass']
            layer = self.getLayerByName(layername)
            request = QgsFeatureRequest()
            if 'whereclause' in kwargs:
                whereclause = kwargs['whereclause']
                request.setFilterExpression(whereclause)
            elif 'attribute' in kwargs:
                attribute = kwargs['attribute']
                values = kwargs['data']
                expr_in = ''
                for v in values:
                    expr_in = expr_in + '%s ,' % str(v)
                expr_in = expr_in[:-1]
                expr = '"' + attribute + '" IN (%s)' % expr_in
                if self.debug: self.info.log("expr: %s" % expr)
                request.setFilterExpression(expr)
            features = layer.getFeatures(request)
            ids = [f.id() for f in features]
            if self.debug: self.info.log("res from request ids:",layer, ids)
            return layer, ids
        except Exception as e:
            gtoobj.info.err(e)

    def ZOOMTOFEATURESET(self,gtoobj,debug,**kwargs):
        try:
            scale = kwargs.get('scale',0)

            iface = gtoobj.iface
            layer, ids = self.getFeatures(gtoobj,debug,**kwargs)

            iface.setActiveLayer(layer)
            prj = QgsProject.instance()
            prj.layerTreeRoot().findLayer(layer.id()).setItemVisibilityCheckedParentRecursive(True)
            #legend.setCurrentLayer(layer)
            #legend.setLayerVisible(layer, True)

            layer.selectByIds(ids)
            iface.mapCanvas().zoomToSelected()
            if scale > 0:
                iface.mapCanvas().zoomScale(scale)
            return True
        except Exception as e:
            gtoobj.info.err(e)

    def SETSELECTSET(self,gtoobj,debug,**kwargs):
        try:
            iface = gtoobj.iface
            layer, ids = self.getFeatures(gtoobj,debug,**kwargs)
            layer.removeSelection()
            layer.selectByIds(ids)
            self.iface.mapCanvas().refresh()
            return True
        except Exception as e:
            gtoobj.info.err(e)

    def GETCOORDINATE(self,gtoobj,debug,**kwargs):
        try:
            objclass = kwargs['objectclass']
            id = kwargs['id']
            esubcommand = kwargs['esubcommand']
            iface = gtoobj.iface
            from qgis.gui import QgsMapToolEmitPoint

            # create tool
            prevTool = iface.mapCanvas().mapTool()
            curTool = QgsMapToolEmitPoint(iface.mapCanvas())

            def on_click(coordinate, clickedMouseButton):
                if debug: gtoobj.info.log("Coordinate:", coordinate)
                if clickedMouseButton == Qt.LeftButton:
                    if esubcommand == 'GETCOORDINATE_ID':
                        #jdata = {"commands": [{"ecommand": "SETCOORDINATE", "config": {"esubcommand": "SETCOORDINATE_ID","objectclass": objclass.encode('utf8'),"id":id, "x": round( coordinate.x(),3),"y":round(coordinate.y(),3)}}]}
                        jdata = {"commands": [{"ecommand": "SETCOORDINATE",
                                               "config": {"esubcommand": "SETCOORDINATE_ID",
                                                          "objectclass": objclass, "id": id,
                                                          "x": round(coordinate.x(), 3),
                                                          "y": round(coordinate.y(), 3)}}]}
                        self.writeRemoteFile(jdata)
                        if debug: self.info.log("Set prev tool:", prevTool.toolName())
                        if prevTool is curTool:
                            iface.mapCanvas().setMapTool(None)
                        else:
                            iface.mapCanvas().setMapTool(prevTool)
                    else:
                        if debug: self.info.log('Unknown esubcommand:',esubcommand)

            def tool_changed(tool):  # another tool was activated
                iface.mapCanvas().mapToolSet.disconnect(tool_changed)
                #curTool.deleteLater()

            curTool.canvasClicked.connect(on_click)
            iface.mapCanvas().setMapTool(curTool)
            iface.mapCanvas().mapToolSet.connect(tool_changed)
            return True
        except Exception as e:
            gtoobj.info.err(e)

    def getSelectedFeatures(self,gtoobj, debug, layer,attribute):
        try:
            data = []
            for f in layer.selectedFeatures():
                val = f[attribute]
                try:
                    if int(val) == val: val = int(val)
                except:
                    pass
                data.append("%s" % str(val))
            return data
        except Exception as e:
            gtoobj.info.err(e)