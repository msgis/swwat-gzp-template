#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5.QtCore import pyqtSignal, Qt, QEvent, QTimer, QObject, QPoint, QDateTime
from PyQt5.QtWidgets import QApplication, QWidgetAction, QAction, QWidget, QComboBox, QLabel, QHBoxLayout, QMessageBox
from PyQt5.QtGui import QColor

from qgis.core import QgsProject, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsDistanceArea, QgsWkbTypes, \
    QgsPoint, QgsGpsDetector, QgsGpsConnection, QgsApplication, QgsGeometry, QgsPointXY, QgsVectorLayerUtils, \
    QgsSnappingUtils, QgsSnappingConfig, QgsNmeaConnection
from qgis.gui import QgsVertexMarker, QgsMapTool, QgsRubberBand

from .gto_info import Info
import random


class GPS(QObject):
    def __init__(self, gtomain):
        super(GPS, self).__init__()
        self.gtomain = gtomain
        self.debug = self.gtomain.debug
        self.helper = self.gtomain.helper
        self.iface = self.gtomain.iface
        self.info = self.gtomain.info
        self.prj = None
        self.canvas = self.iface.mapCanvas()
        self.gpsLog = Info(self)
        self.gpsLog.panel_name = "GTO-GPS"
        self.mouse = None
        self.LastMapTool = None
        try:
            # settings
            self.settings = None
            self.timer_intervall = 1000
            self.port = None
            self.pdop = 0
            self.wgs_crs = 'EPSG:4326'
            self.gps_streaming_distance = 10

            # refs
            self.gpsCon = None
            self.gpsDetector = None
            self.gps_active = False
            self.dic_gpsinfo = {}

            self.prj_crs = None
            self.src_crs = None
            self.transformation = None
            self.marker = None
            self.prevPointXY = None
            self.prevTime = None
            self.lastGpsInfo = None
            self.center = False
            self.scale = 0
            # actions
            mw = self.iface.mainWindow()
            self.actionGPStoggle = QAction("GTO-GPS", mw)
            self.actionGPStoggle.setObjectName('mActionGTOgpsToggle')
            self.actionGPStoggle.setToolTip('GTO GPS starten')
            self.actionGPStoggle.setIcon(self.gtomain.helper.getIcon('mActionGTOgpsToggle.png'))
            self.actionGPStoggle.setCheckable(True)
            self.actionGPStoggle.setChecked(False)
            self.actionGPStoggle.toggled.connect(self.activate)

            self.actionGPSaddPoint = QAction("GPS Punkt hinzufügen", mw)
            self.actionGPSaddPoint.setObjectName('mActionGTOgpsAddPoint')
            self.actionGPSaddPoint.setToolTip('GPS Punkt hinzufügen')
            self.actionGPSaddPoint.setIcon(self.gtomain.helper.getIcon('mActionGTOgpsAddPoint.png'))
            self.actionGPSaddPoint.triggered.connect(self.addPoint)
            self.actionGPSaddPoint.setEnabled(False)

            self.actionGPSclick = QAction("GPS Punkt hinzufügen", mw)
            self.actionGPSclick.setObjectName('mActionGTOgpsAddcPoint')
            self.actionGPSclick.setToolTip('GPS Punkt hinzufügen')
            self.actionGPSclick.setIcon(self.gtomain.helper.getIcon('mActionGTOgpsAddcPoint.png'))
            self.actionGPSclick.triggered.connect(self.gps_click)
            self.actionGPSclick.setEnabled(False)

            self.actionGPSstreaming = QAction("GPS streaming", mw)
            self.actionGPSstreaming.setObjectName('mActionGTOgpsStream')
            self.actionGPSstreaming.setToolTip('GPS Punkte aufzeichnen')
            self.actionGPSstreaming.setIcon(self.gtomain.helper.getIcon('mActionGTOgpsStream.png'))
            self.actionGPSstreaming.setCheckable(True)
            self.actionGPSstreaming.setEnabled(False)
            self.actionGPSstreaming.toggled.connect(self.streaming)

            self.actionGPSsave = QAction("GPS Geometrie speichern", mw)
            self.actionGPSsave.setObjectName('mActionGTOgpsSave')
            self.actionGPSsave.setToolTip('GPS Geometrie speichern')
            self.actionGPSsave.setIcon(self.gtomain.helper.getIcon('mActionGTOgpsSave.png'))
            self.actionGPSsave.triggered.connect(self.saveGeometry)
            self.actionGPSsave.setEnabled(False)

            self.actionGPSaddVertexTool = QAction("GPS AddVertexTool", mw)
            self.actionGPSaddVertexTool.setObjectName('mActionGTOgpsAddVertexTool')
            self.actionGPSaddVertexTool.setToolTip('GPS add vertex to stream')
            self.actionGPSaddVertexTool.setIcon(self.gtomain.helper.getIcon('mActionGTOgpsAddVertexTool.png'))
            self.actionGPSaddVertexTool.setCheckable(True)
            self.actionGPSaddVertexTool.toggled.connect(self.activateVertexTool)
            self.actionGPSaddVertexTool.setEnabled(False)
            # add vertex tool
            self.streamTool = VertexTool(self.iface, self.canvas, True)
            self.streamTool.canvasReleased.connect(self.addVertex)
            self.streamTool.isActive.connect(self.tool_isactive)

            self.actionGPSlog = QAction("GPS Log", mw)
            self.actionGPSlog.setObjectName('mActionGTOgpsLog')
            self.actionGPSlog.setToolTip('GPS events anzeigen')
            self.actionGPSlog.setIcon(self.gtomain.helper.getIcon('mActionGTOgpsLog.png'))
            self.actionGPSlog.setCheckable(True)

            self.actionGPScenter = QAction("GPS zentriere Karte", mw)
            self.actionGPScenter.setObjectName('mActionGTOgpsCenter')
            self.actionGPScenter.setToolTip('GPS zentriere Karte')
            self.actionGPScenter.setIcon(self.gtomain.helper.getIcon('mActionGTOgpsCenter.png'))
            self.actionGPScenter.setCheckable(True)
            self.actionGPScenter.toggled.connect(self.activateCenter)

            self.actionGPSport = GtoWidgetGpsPort(self, mw)
            self.actionGPSport.portChanged.connect(self.setPort)

            self.canvas.currentLayerChanged.connect(self.layer_changed)
            # streaming
            self.debugXoffset = 0  # debugging
            self.debugYoffset = 0
            # rubberband
            # get selection color
            selcolor = self.canvas.selectionColor()
            mycolor = QColor(selcolor.red(), selcolor.green(), selcolor.blue(), 40)
            self.rb = QgsRubberBand(self.canvas)
            self.rb.setStrokeColor(QColor(255, 0, 0, 90))
            self.rb.setFillColor(mycolor)
            self.rb.setLineStyle(Qt.PenStyle(Qt.SolidLine))
            self.rb.setWidth(4)

            # watchdog
            self.watchdog = QTimer()
            self.watchdog.setInterval(2000)
            self.watchdog.timeout.connect(self.watch_dog)
            # layer
            self.streamLayer = None
            self.pointLayer = None
            self.gps_stream_mode = 0  # "0=rubber, 1=click, 2=both
            self.gps_debug = False
        except Exception as e:
            self.info.err(e)

    def watch_dog(self):
        try:
            self.watchdog.stop()
            self.gpsLog.log('Status:', self.gpsCon.status())  # doesnt work properly
            self.marker.setColor(QColor(255, 0, 0))
            if self.actionGPSlog.isChecked(): self.gpsLog.log('No signal!')
            res = self.info.gtoQuestion("GPS deaktivieren? (Empfohlen)", title='Kein GPS Signal!',
                                        btns=QMessageBox.Yes | QMessageBox.No, parent=self.iface.mainWindow())
            if res == QMessageBox.Yes:
                self.deactivate()
                self.actionGPStoggle.setChecked(False)
        except Exception as e:
            self.info.err(e)

    def init(self):
        try:
            if self.debug: self.gpsLog.log('gps init')
            self.actionGPStoggle.setChecked(False)
            # qgis
            self.prj = QgsProject().instance()
            self.canvas = self.iface.mapCanvas()
            # settings
            if "GPS" in self.gtomain.settings:  # compatible
                self.settings = self.gtomain.settings["GPS"]
            else:
                self.settings = self.gtomain.settings
            # timer
            self.timer_intervall = self.settings.get("gps_timer_intervall", 5000)
            # gps
            self.port = self.settings.get("gps_port", None)
            if self.port is None:
                self.setPort(self.helper.getGlobalSetting('GpsPort'))
            self.pdop = self.settings.get("gps_pdop", 0)
            self.actionGPSlog.setChecked(self.settings.get("gps_log", False))
            watchdog_interval = self.settings.get("gps_watchdog_interval", 3000)
            self.watchdog.setInterval(watchdog_interval)
            # streaming
            self.pointLayer = self.settings.get("gps_point_layer", None)
            try:
                if self.pointLayer is not None:
                    self.pointLayer = self.prj.mapLayersByName(self.pointLayer)[0]
                    geoType = self.pointLayer.geometryType()
                    if geoType != QgsWkbTypes.GeometryType.PointGeometry:
                        self.pointLayer = None
            except Exception as e:
                self.pointLayer = None
                self.info.err(e)
            self.gps_debug = self.settings.get("gps_debug", False)
            self.gps_stream_mode = self.settings.get("gps_stream_mode", 0)
            self.gps_streaming_distance = self.settings.get("gps_streaming_distance", 1)
            # map
            self.center = self.settings.get("gps_center", True)
            self.actionGPScenter.setChecked(self.center)
            self.scale = self.settings.get("gps_scale", 0)
            # transformation
            self.prj_crs = self.prj.crs()
            self.wgs_crs = self.settings.get("gps_wgs_crs", 'EPSG:4326')
            self.init_transformation(self.wgs_crs)
        except Exception as e:
            self.info.err(e)

    def activateCenter(self):
        self.center = self.actionGPScenter.isChecked()

    def activate(self):
        try:
            self.deactivate()
            if self.actionGPStoggle.isChecked():
                if self.port is None:
                    self.info.msg("Kein GPS Port gesetzt!")
                    return
                self.actionGPSport.setEnabled(False)
                if self.actionGPSlog.isChecked(): self.gpsLog.log('gps activate')
                self.gpsDetector = QgsGpsDetector(self.port)
                self.gpsDetector.detected[QgsGpsConnection].connect(self.connection_succeed)
                # self.gpsDetector.detected[QgsNmeaConnection].connect(self.connection_succeed)
                self.gpsDetector.detectionFailed.connect(self.connection_failed)
                self.gpsDetector.advance()
                self.init_marker()
        except Exception as e:
            self.info.err(e)

    def setPort(self, port):
        try:
            self.port = port
            self.actionGPStoggle.setToolTip('GPS on/off (Port:{0})'.format(self.port))
        except Exception as e:
            self.info.err(e)

    def enableGPSfunctions(self, enabled):
        try:
            if self.iface.mainWindow() is None: return  # dummy
        except:
            # prevent: ERROR:  <class 'RuntimeError'> gto_gps.py | line: 240 | ('wrapped C/C++ object of type QgisInterface has been deleted',)
            # because QGIS is already closing
            return
        try:
            if self.iface.activeLayer() is not None:
                geoType = self.iface.activeLayer().geometryType()
                if geoType == QgsWkbTypes.GeometryType.PointGeometry:
                    self.actionGPSaddPoint.setEnabled(enabled)
                else:
                    self.actionGPSaddPoint.setEnabled(False)
            self.actionGPSclick.setEnabled(enabled)
            self.actionGPSstreaming.setEnabled(enabled)
            self.actionGPSport.setEnabled(not enabled)
        except Exception as e:
            self.info.err(e)

    def connection_succeed(self, connection):
        try:
            self.gps_active = True
            self.gpsCon = connection
            self.gpsCon.stateChanged.connect(self.status_changed)
            self.watchdog.start()
        except Exception as e:
            self.info.err(e)

    def connection_failed(self):
        if not self.gps_active:
            self.actionGPStoggle.setChecked(False)
            self.info.msg("GPS konnte nicht initialisiert werden!")
            self.info.log('GPS connection failed')
            self.enableGPSfunctions(False)

    def deactivate(self):
        try:
            if self.iface.mainWindow() is None: return  # dummy
        except:
            # prevent: ERROR:  <class 'RuntimeError'> gto_gps.py | line: 240 | ('wrapped C/C++ object of type QgisInterface has been deleted',)
            # because QGIS is already closing
            return
        try:
            if self.debug: self.info.log('gps deactivate')
            self.watchdog.stop()
            self.debugXoffset = 0
            self.debugYoffset = 0
            self.prevTime = None
            self.actionGPSstreaming.setChecked(False)
            self.enableGPSfunctions(False)
            self.prevPointXY = None
            if self.gpsCon is not None:
                if self.actionGPSlog.isChecked(): self.gpsLog.log('gps deactivate')
                self.gpsCon.close()
            if self.canvas is not None:
                self.canvas.scene().removeItem(self.marker)
            self.gps_active = False
        except Exception as e:
            self.info.err(e)

    def init_marker(self):
        try:
            if self.actionGPSlog.isChecked(): self.info.log('gps init_marker')
            self.marker = QgsVertexMarker(self.canvas)
            self.marker.setColor(QColor(255, 0, 0))  # (R,G,B)
            self.marker.setIconSize(10)
            self.circle = QgsVertexMarker.ICON_CIRCLE
            self.marker.setIconType(self.circle)
            #        ICON_BOX
            #        ICON_CIRCLE
            #        ICON_CROSS
            #        ICON_DOUBLE_TRIANGLE
            #        ICON_NONE
            #        ICON_X
            self.marker.setPenWidth(3)
        except Exception as e:
            self.info.err(e)

    def init_transformation(self, wgs_crs):
        try:
            self.src_crs = QgsCoordinateReferenceSystem(wgs_crs)
            self.transformation = QgsCoordinateTransform(self.src_crs, self.prj_crs, self.prj)
        except Exception as e:
            self.info.err(e)

    def status_changed(self, gpsInfo):
        try:
            if self.gpsCon.status() != 3: return  # 3=data received
            self.watchdog.stop()
            self.watchdog.start()
            if gpsInfo.longitude == 0: return
            valid = False
            self.dic_gpsinfo = {"direction": gpsInfo.direction, "elevation": gpsInfo.elevation,
                                "fixMode": gpsInfo.fixMode, "fixType": gpsInfo.fixType, "hacc": gpsInfo.hacc,
                                "satInfoComplete": gpsInfo.satInfoComplete, "speed": gpsInfo.speed,
                                "utcDateTime": gpsInfo.utcDateTime, "vacc": gpsInfo.vacc, "status": gpsInfo.status,
                                "hdop": gpsInfo.hdop, "vdop": gpsInfo.vdop, "pdop": gpsInfo.pdop,
                                "latitude": gpsInfo.latitude, "longitude": gpsInfo.longitude,
                                "satellitesInView": gpsInfo.satellitesInView, "satellitesUsed": gpsInfo.satellitesUsed,
                                "quality": gpsInfo.quality}
            if self.actionGPSlog.isChecked():
                self.gpsLog.log('direction:', gpsInfo.direction)
                self.gpsLog.log('elevation:', gpsInfo.elevation)
                self.gpsLog.log('fixMode:', gpsInfo.fixMode)
                self.gpsLog.log('fixType:', gpsInfo.fixType)
                self.gpsLog.log('hacc:', gpsInfo.hacc)
                self.gpsLog.log('satInfoComplete:', gpsInfo.satInfoComplete)
                self.gpsLog.log('speed:', gpsInfo.speed)
                self.gpsLog.log('utcDateTime:', gpsInfo.utcDateTime.toString())
                self.gpsLog.log('vacc:', gpsInfo.vacc)
                self.gpsLog.log('status:', gpsInfo.status)
                self.gpsLog.log('hdop:', gpsInfo.hdop)
                self.gpsLog.log('vdop:', gpsInfo.vdop)
                self.gpsLog.log('pdop:', gpsInfo.pdop)
                self.gpsLog.log('latitude:', gpsInfo.latitude)
                self.gpsLog.log('longitude:', gpsInfo.longitude)
                self.gpsLog.log('satellitesInView:', len(gpsInfo.satellitesInView))
                self.gpsLog.log('satellitesUsed:', gpsInfo.satellitesUsed)
                self.gpsLog.log('quality:', gpsInfo.quality)
                self.gpsLog.log("---------------------")
            if gpsInfo.pdop >= self.pdop:  # gps ok
                valid = True
                self.enableGPSfunctions(True)
                self.marker.setColor(QColor(0, 200, 0))
            else:

                self.enableGPSfunctions(False)
                self.marker.setColor(QColor(255, 0, 0))
            wgs84_pointXY = QgsPointXY(gpsInfo.longitude, gpsInfo.latitude)
            wgs84_point = QgsPoint(wgs84_pointXY)

            wgs84_point.transform(self.transformation)
            if self.gps_debug:
                self.debugXoffset = self.debugXoffset + random.randint(0,
                                                                       int(self.gps_streaming_distance))
                self.debugYoffset = self.debugYoffset + random.randint(0,
                                                                       int(self.gps_streaming_distance))
                x = wgs84_point.x() + self.debugXoffset
                y = wgs84_point.y() + self.debugYoffset
            else:
                x = wgs84_point.x()
                y = wgs84_point.y()
            if self.actionGPSlog.isChecked():
                self.gpsLog.log("x:", x)
                self.gpsLog.log("y:", y)
                self.gpsLog.log("--------------------")
            mapPointXY = QgsPointXY(x, y)
            self.lastGpsInfo = gtoGPSinfo(gpsInfo, mapPointXY, valid)
            # map
            if self.center and valid:
                self.canvas.setCenter(mapPointXY)
                if self.scale > 0: self.canvas.zoomScale(self.scale)
            self.marker.setCenter(mapPointXY)
            self.marker.show()
            # streaming
            gpsDateTime = None
            diff = 0
            if self.pointLayer is not None:
                self.actionGPSaddPoint.setEnabled(valid)
            if self.actionGPSstreaming.isChecked() and valid and not self.actionGPSaddVertexTool.isChecked():
                if self.prevTime is None:
                    self.prevTime = gpsInfo.utcDateTime.currentDateTime()
                else:
                    gpsDateTime = gpsInfo.utcDateTime.currentDateTime()
                    diff = self.prevTime.msecsTo(gpsDateTime)
                    if diff < self.timer_intervall:
                        return

                if self.prevPointXY is None:
                    self.prevPointXY = mapPointXY
                    self.prevTime = gpsDateTime
                    if self.pointLayer is not None:
                        self.addPoint()
                    else:
                        if self.gps_stream_mode == 1:
                            self.gps_click()
                        elif self.gps_stream_mode == 2:
                            self.gps_click()
                            self.addVertex(mapPointXY)
                        else:
                            self.addVertex(mapPointXY)
                else:
                    qgsDistance = QgsDistanceArea()
                    distance = qgsDistance.measureLine([self.prevPointXY, mapPointXY])
                    if distance > self.gps_streaming_distance and diff > self.timer_intervall:
                        self.prevTime = gpsDateTime
                        self.prevPointXY = mapPointXY
                        if self.pointLayer is not None:
                            self.addPoint()
                        else:
                            if self.gps_stream_mode == 1:
                                self.gps_click()
                            elif self.gps_stream_mode == 2:
                                self.gps_click()
                                self.addVertex(mapPointXY)
                            else:
                                self.addVertex(mapPointXY)
        except Exception as e:
            self.info.err(e)

    def gps_click(self):
        from pynput.mouse import Button, Controller
        try:
            if self.gps_active:
                if self.debug: self.gpsLog.log('gps_click')
                actionAddFeature = self.iface.mainWindow().findChild(QAction, 'mActionAddFeature')
                gtoGpsInfo = self.lastGpsInfo
                if gtoGpsInfo.isValid and actionAddFeature.isChecked():
                    self.mouse = Controller()
                    mapX = gtoGpsInfo.mapPointXY.x()
                    mapY = gtoGpsInfo.mapPointXY.y()
                    pointXY = self.canvas.getCoordinateTransform().transform(mapX, mapY)  # map coords to device coords
                    x = pointXY.x()
                    y = pointXY.y()
                    p = self.canvas.mapToGlobal(QPoint(x, y))  # device coords to screen coords
                    x = p.x()
                    y = p.y()
                    prevX, prevY = self.mouse.position
                    self.mouse.position = (x, y)
                    if self.debug: self.gpsLog.log('addPoint', x, "/", y)
                    self.mouse.click(Button.left, 1)
                    self.mouse.position = (prevX, prevY)
        except Exception as e:
            self.info.err(e)

    def layer_changed(self):
        try:
            self.actionGPSstreaming.setChecked(False)
            if self.gps_active:
                geoType = self.iface.activeLayer().geometryType()
                if geoType == QgsWkbTypes.GeometryType.PointGeometry or self.pointLayer is not None:
                    self.actionGPSaddPoint.setEnabled(True)
                else:
                    self.actionGPSaddPoint.setEnabled(False)
        except Exception as e:
            self.info.err(e)

    def streaming(self):
        try:
            self.actionGPSsave.setEnabled(False)
            self.actionGPSaddVertexTool.setChecked(False)
            self.activateVertexTool()
            if self.pointLayer is not None:
                return
            if self.actionGPSstreaming.isChecked():
                if self.streamLayer is not None:
                    self.actionGPSstreaming.setChecked(False)
                    res = self.saveGeometry()
                    if res == QMessageBox.Cancel: return
                    self.actionGPSstreaming.setChecked(True)
                geoType = self.iface.activeLayer().geometryType()
                if geoType == QgsWkbTypes.GeometryType.PolygonGeometry or geoType == QgsWkbTypes.GeometryType.LineGeometry:
                    self.streamLayer = self.iface.activeLayer()
                    self.actionGPSaddVertexTool.setEnabled(True)
                    self.rb.reset(geoType)
                else:
                    self.actionGPSstreaming.setChecked(False)
                    self.actionGPSaddVertexTool.setEnabled(False)
                    self.info.msg("Aktiver Layer muss vom Typ Polgone oder Line sein!")
            else:
                self.actionGPSaddVertexTool.setEnabled(False)
                if self.streamLayer is not None:
                    geoType = self.streamLayer.geometryType()
                    tools = self.settings.get('gps_afterstream_tools', [])
                    if geoType == QgsWkbTypes.GeometryType.PolygonGeometry:
                        if self.rb.numberOfVertices() > 2:
                            self.actionGPSsave.setEnabled(True)
                            self.gtomain.runcmd(tools)
                    if geoType == QgsWkbTypes.GeometryType.LineGeometry:
                        if self.rb.numberOfVertices() > 1:
                            self.actionGPSsave.setEnabled(True)
                            self.gtomain.runcmd(tools)
        except Exception as e:
            self.info.err(e)

    def addPoint(self):
        try:
            if self.gps_active:
                if self.actionGPSlog.isChecked(): self.gpsLog.log('addPoint')
                gtoGpsInfo = self.lastGpsInfo
                if gtoGpsInfo.isValid:
                    if self.pointLayer is not None:
                        layer = self.pointLayer
                    else:
                        layer = self.iface.activeLayer()
                    geoType = layer.geometryType()
                    if geoType != QgsWkbTypes.GeometryType.PointGeometry:
                        self.info.msg("Kein Punktlayer ausgewählt!")
                        return
                    # create feature
                    feat = QgsVectorLayerUtils.createFeature(layer)
                    tr = QgsCoordinateTransform(self.prj_crs, layer.crs(), self.prj)
                    tr_point = tr.transform(gtoGpsInfo.mapPointXY)
                    geo = QgsGeometry.fromPointXY(tr_point)
                    feat.setGeometry(geo)
                    # set attributes
                    gps_addpoint_attributes = self.settings.get("gps_addpoint_attributes", {})
                    for k, v in gps_addpoint_attributes.items():
                        feat[k] = layer.fields().field(k).convertCompatible(self.dic_gpsinfo[v])
                    # add to layer
                    if self.pointLayer is not None:
                        # add to provider
                        (res, outFeats) = layer.dataProvider().addFeatures([feat])
                        layer.select(outFeats[0].id())
                    else:
                        if not layer.isEditable(): layer.startEditing()
                        layer.beginEditCommand('Add stream geometry')
                        layer.addFeatures([feat])
                        layer.endEditCommand()
                        self.helper.refreshLayer(layer)
        except Exception as e:
            self.info.err(e)

    def saveGeometry(self, force=False):
        try:
            if self.streamLayer is not None:
                if not force:
                    res = self.info.gtoQuestion(
                        "GPS Stream-Geometry in Layer \n{0}\nspeichern?".format(self.streamLayer.name()),
                        title='GPS Streaming',
                        btns=QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                        parent=self.iface.mainWindow())
                    if res == QMessageBox.Cancel: return res
                    if res == QMessageBox.No:
                        self.actionGPSsave.setEnabled(False)
                        self.streamLayer = None
                        self.rb.reset()
                        return
                # create feature
                feat = QgsVectorLayerUtils.createFeature(self.streamLayer)
                geo = self.rb.asGeometry()
                feat.setGeometry(geo)
                # add to layer
                if not self.streamLayer.isEditable(): self.streamLayer.startEditing()
                self.streamLayer.beginEditCommand('Add stream geometry')
                self.streamLayer.addFeatures([feat])
                self.streamLayer.endEditCommand()
                # add to provider
                # (res, outFeats) = self.streamLayer.dataProvider().addFeatures([feat])
                # self.streamLayer.select(outFeats[0].id())

                # reset streaming
                self.actionGPSsave.setEnabled(False)
                self.streamLayer = None
                self.rb.reset()
        except Exception as e:
            self.streamLayer.destroyEditCommand()
            self.info.err(e)

    def addVertex(self, point):
        try:
            self.rb.addPoint(point)
        except Exception as e:
            self.info.err(e)

    def activateVertexTool(self):
        try:
            if self.actionGPSaddVertexTool.isChecked():
                if self.actionGPSlog.isChecked(): self.gpsLog.log('activated VertexTool: stream paused')
                self.LastMapTool = self.canvas.mapTool()
                self.canvas.setMapTool(self.streamTool)
            else:
                if self.actionGPSlog.isChecked(): self.gpsLog.log('deactivated VertexTool: stream resumed')
                self.canvas.setMapTool(self.LastMapTool)
        except Exception as e:
            self.info.err(e)

    def tool_isactive(self, active):
        try:
            pass
        except Exception as e:
            self.info.err(e)


class VertexTool(QgsMapTool):
    canvasReleased = pyqtSignal(QgsPointXY, bool)
    isActive = pyqtSignal(bool)

    def __init__(self, iface, canvas, useSnapped=True):
        super(VertexTool, self).__init__(canvas)

        self.snapper = None
        self.markerSnapped = None
        self.useSnapped = useSnapped
        self.iface = iface
        self.canvas = self.iface.mapCanvas()
        self.setCursor(Qt.CrossCursor)
        self.prj = QgsProject.instance()
        self.snapConfig = self.prj.snappingConfig()
        self.prj.snappingConfigChanged.connect(self.setSnapping)

        self.setSnapping(self.prj.snappingConfig())

    def setSnapping(self, config):
        self.snapConfig = config
        self.snapper = QgsSnappingUtils(self.canvas)
        self.snapper.setConfig(self.snapConfig)
        self.snapper.setMapSettings(self.canvas.mapSettings())

    def canvasMoveEvent(self, event):
        point = self.toMapCoordinates(event.pos())
        if self.snapConfig.enabled() and self.useSnapped:
            self.isSnapped(point)
        else:
            self.resetMarker()

    def canvasReleaseEvent(self, event):
        point = self.toMapCoordinates(event.pos())
        if self.useSnapped:
            point, isnaped = self.isSnapped(point)
            self.canvasReleased.emit(point, isnaped)
        else:
            self.canvasReleased.emit(point, False)

    def activate(self):
        self.isActive.emit(True)
        QgsMapTool.activate(self)

    def deactivate(self):
        self.resetMarker()
        self.isActive.emit(False)
        QgsMapTool.deactivate(self)

    def isSnapped(self, pointxy):
        self.resetMarker()
        matchres = self.snapper.snapToMap(pointxy)  # QgsPointLocator.Match
        if matchres.isValid():
            self.markerSnapped = QgsVertexMarker(self.canvas)
            self.markerSnapped.setColor(Qt.red)
            self.markerSnapped.setIconSize(7)
            self.markerSnapped.setIconType(QgsVertexMarker.ICON_BOX)
            self.markerSnapped.setPenWidth(3)
            self.markerSnapped.setCenter(matchres.point())
            self.markerSnapped.show()
            return matchres.point(), True
        else:
            return pointxy, False

    def resetMarker(self):
        self.canvas.scene().removeItem(self.markerSnapped)


class gtoGPSinfo(QObject):
    def __init__(self, gpsInfo, mapPointXY, valid):
        super(gtoGPSinfo, self).__init__()
        self.gpsInfo = gpsInfo
        self.mapPointXY = mapPointXY
        self.isValid = valid


class GtoWidgetGpsPort(QWidgetAction):
    portChanged = pyqtSignal(str)

    def __init__(self, gtoObj, parent=None):
        super(GtoWidgetGpsPort, self).__init__(parent)
        self.setObjectName('mActionGTOgpsPort')

        self.gtomain = gtoObj.gtomain
        self.helper = self.gtomain.helper
        self.info = self.gtomain.info

        self.wid = self.createDefaultWidget(parent)
        self.cbo = self.wid.findChildren(QComboBox)[0]
        self.setDefaultWidget(self.wid)

    def setPort(self, port):
        self.helper.setGlobalSetting('GpsPort', port)
        self.portChanged.emit(port)

    def getPort(self):
        return self.helper.getGlobalSetting('GpsPort')

    def setEnabled(self, a0):
        self.cbo.setEnabled(a0)

    def createDefaultWidget(self, parent):
        cboPorts = QComboBox()
        for port, name in QgsGpsDetector.availablePorts():
            if port.startswith('COM'):
                cboPorts.addItem(name, port)
        cboPorts.model().sort(0)
        port = self.getPort()
        cboPorts.currentIndexChanged.connect(lambda: self.setPort(cboPorts.currentData()))
        idx = cboPorts.findData(port)
        if idx == -1: idx = 1
        cboPorts.setCurrentIndex(idx)
        # create the widget
        wid = QWidget(parent)
        layout = QHBoxLayout(wid)
        layout.addWidget(QLabel('GPS:'))
        layout.addWidget(cboPorts)
        wid.setLayout(layout)
        return wid
