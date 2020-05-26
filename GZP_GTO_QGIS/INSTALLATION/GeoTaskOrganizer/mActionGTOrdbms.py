#!/usr/bin/python
# -*- coding: utf-8 -*-

from builtins import str
from PyQt5.QtCore import *
# from PyQt5.QtSql import *
from PyQt5.QtWidgets import *
from qgis.core import QgsDataSourceUri, QgsFeatureRequest, QgsProject
from qgis.PyQt.QtSql import QSqlDatabase, QSqlQuery


class run(QObject):
    def __init__(self, id, gtotool, config, debug):
        super(run, self).__init__()
        self.debug = gtotool.debug
        self.info = gtotool.info
        self.iface = gtotool.iface
        self.prj = QgsProject.instance()
        self.infotext = ""
        self.result = None
        try:
            # read metadata
            # connection:
            self.dbdriver = config.get('dbdriver', None)
            self.provider = config.get('provider', config.get('driver', None))  # compatibility
            self.host = config.get('host', config.get('server', None))  # compatibility
            self.database = config.get('database', None)
            self.port = config.get('port', None)
            self.user = config.get('user', None)
            self.password = config.get('password', None)
            self.service = config.get('service', None)
            # others:
            self.use_selection = config.get('use_selection', False)
            self.pocedure = config.get('procedure', None)
            self.sql = config.get('sql', None)
            self.parameters = config.get('parameters', [])
            self.layer = self.iface.activeLayer()
            self.message = config.get('message', None)
            self.refreshmap = config.get('refreshmap', False)
            self.limit = config.get('limit', 10000)

            # declare vars
            layer = self.iface.activeLayer()
            # get the database connection:
            if self.provider is None and self.dbdriver is None and self.service is None:  # use active layer
                db, sql = self.getConnectionFromLayer()
            else:
                db, sql = self.getConnectionFromMetaData()
            # prepare sql
            if db is not None and db.isValid():
                self.result = False
                try:
                    if db.open():
                        if self.use_selection:  # wlk specific
                            if self.debug: self.info.log('using selection')
                            # features = layer.selectedFeatures()#slow one
                            request = QgsFeatureRequest()
                            request.setFilterFids(layer.selectedFeatureIds())
                            fields = [self.parameters[0]]
                            request.setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes(fields, layer.fields())
                            request.setLimit(self.limit)
                            for feat in layer.getFeatures(request):
                                self.executeQuery(db, sql, feat)
                                if not self.result: break  # to avoiding get same error for each feature
                        else:
                            self.executeQuery(db, sql)
                        if self.result:
                            if self.message is not None:  # everything is fine!
                                QMessageBox.information(self.iface.mainWindow(), self.infotext, self.message)
                        db.close()
                    else:
                        err = db.lastError()
                        self.info.gtoWarning(err.text())
                except:
                    self.info.log("database not opened!")
                    err = db.lastError()
                    self.info.gtoWarning(err.text())
            else:
                self.info.gtoWarning("No valid database!")
        except Exception as e:
            self.info.err(e)

    def executeQuery(self, db, sql, feat=None):
        try:
            fparams = self.preparesql(feat)
            if self.debug:
                self.info.log("sql:", sql)
                self.info.log("fparams:", fparams)
            sqlexe = sql % fparams
            if self.debug: self.info.log("SQL execute:", sqlexe)
            # if db is not specified, or is invalid, the application's default database is used.
            # If query is not an empty string, it will be executed
            query = QSqlQuery(db)
            # query = db.exec_(sql)#obsolete
            query.prepare(sqlexe)
            self.result = query.exec_()
            if not self.result:
                self.info.log(query.lastError().databaseText())
                self.info.gtoWarning("Database Error:" + query.lastError().databaseText())
        except Exception as e:
            self.info.err(e)

    def getConnectionFromLayer(self):
        try:
            provider = self.layer.dataProvider()
            uri = QgsDataSourceUri(provider.dataSourceUri())
            db, sql = self.getDatabase(provider.name (), self.pocedure)
            if uri.service() != '':  # use service
                service = 'service=' + uri.service()
                db.setConnectOptions(service)
            else:
                # set the parameters needed for the connection
                db.setHostName(uri.host())
                db.setDatabaseName(uri.database())
                db.setPort(int(uri.port()))
                db.setUserName(uri.username())
                db.setPassword(uri.password())
            if self.debug:
                layerinfo = 'Layer connection:\n'
                layerinfo = layerinfo + "\nActive layer: " + self.layer.name() + "\nlayer provider: " + provider.name() + "\n"
                layerinfo = layerinfo + "URI: host:" + uri.host() + "\ndatabse:" + uri.database() + "\nport" + uri.port()
                layerinfo = layerinfo + "\nuser:" + uri.username() + "\npassword:" + uri.password()
                layerinfo = layerinfo + "\nservice:" + uri.service()
                self.info.log(layerinfo)
        except Exception as e:
            self.info.err(e)
        finally:
            return db, sql

    def getConnectionFromMetaData(self):
        try:
            db = None
            sql = self.pocedure
            if self.provider is not None:
                db, sql = self.getDatabase(self.provider, self.pocedure)
            if self.dbdriver is not None:
                db = QSqlDatabase.addDatabase(self.dbdriver)
                sql = self.sql
            if self.service is not None: db.setConnectOptions("service=" + self.service)
            if self.host is not None: db.setHostName(self.host)
            if self.database is not None: db.setDatabaseName(self.database)
            if self.port is not None: db.setPort(int(self.port))
            if self.user is not None: db.setUserName(self.user)
            if self.password is not None: db.setPassword(self.password)
            if self.debug:
                dbinfo = 'Database connection:\n'
                dbinfo = dbinfo + "driver: " + db.driverName() + "\nhost: " + db.hostName() + "\ndatabase: " + db.databaseName() + "\nport: " \
                         + str(db.port()) + "\nuser: " + db.userName() + "\npassword: " + db.password() + "\noptions: " + db.connectOptions()
                self.info.log(dbinfo)
        except Exception as e:
            self.info.err(e)
        finally:
            return db, sql

    def getDatabase(self, provider_name, procedure):
        db = None
        sql = ''
        try:
            if provider_name == "oracle" or provider_name == 'QOCISPATIAL':
                db = QSqlDatabase.addDatabase('QOCISPATIAL')  # QSqlDatabase.addDatabase('QOCI')
                sql = "BEGIN " + procedure + "%s" + ";" + " END;"
            elif provider_name == "postgres" or provider_name == 'QPSQL':
                db = QSqlDatabase.addDatabase('QPSQL')
                sql = "SELECT " + procedure + "%s" + ";"
            elif provider_name == 'QOCISPATIAL8':
                db = QSqlDatabase.addDatabase('QOCISPATIAL8')
                sql = "BEGIN " + procedure + "%s" + ";" + " END;"
            elif provider_name == 'QSQLITE':
                db = QSqlDatabase.addDatabase('QSQLITE')
                sql = procedure
            elif provider_name == 'QMYSQL':
                db = QSqlDatabase.addDatabase('QMYSQL')
                sql = procedure
            elif provider_name == 'QMYSQL3':
                db = QSqlDatabase.addDatabase('QMYSQL3')
                sql = procedure
            elif provider_name == 'QPSQL7':
                db = QSqlDatabase.addDatabase('QPSQL7')
                sql = procedure
            elif provider_name == 'QODBC':
                db = QSqlDatabase.addDatabase('QODBC')  # ODBC Driver (includes Microsoft SQL Server)
                sql = "EXEC " + procedure + "%s"
            elif provider_name == 'QODBC3':
                db = QSqlDatabase.addDatabase('QODBC3')  # ODBC Driver (includes Microsoft SQL Server)
                sql = "EXEC " + procedure + "%s"
            else:
                self.info.msg("Unknown provider: \n" + provider_name + "\nTry using ODBC...")
                db = QSqlDatabase.addDatabase('QODBC')  # ODBC Driver (includes Microsoft SQL Server)
                sql = "EXEC " + procedure + "%s"
            if db is None:
                self.info.log("No Database created!")
                self.info.log( "Available database drivers:",QSqlDatabase.drivers())
        except Exception as e:
            self.info.err(e)
        finally:
            return db, sql

    def preparesql(self, feat=None):
        try:
            expr = ""
            for p in self.parameters:
                if self.layer is not None and feat is not None:  # wlk spesific
                    if isinstance(p, str):
                        id = self.layer.fields().lookupField(p)
                        if id != -1:
                            p = feat.attributes()[id]
                if p is not None:
                    if isinstance(p, str):  # assume its an expression
                        expr = expr + "'%s'," % p
                    elif isinstance(p, dict):
                        expr = expr + self.specialFunctions(p) + ","
                    else:
                        expr = expr + "%s," % str(p)
                else:
                    expr = expr + "NULL,"
            if expr.endswith(","): expr = expr[:-1]  # remove last colon
            return "(" + expr + ")"
        except Exception as e:
            self.info.err(e)

    def specialFunctions(self, p):
        try:
            if "extent" in p.keys():
                ext = self.iface.mapCanvas().extent()
                return str(ext.xMinimum()) + "," + str(ext.yMinimum()) + "," + str(ext.xMaximum()) + "," + str(
                    ext.yMaximum())
            elif "project_srsid" in p.keys():
                srsid = QgsProject.instance().crs().srsid()
                if not srsid: srsid = 0
                return str(srsid)
            elif "layer_srsid" in p.keys():
                srsid = self.iface.activeLayer().sourceCrs().srsid()
                if not srsid: srsid = 0
                return str(srsid)
            elif "layer_postgis_srid" in p.keys():
                srsid = self.iface.activeLayer().sourceCrs().postgisSrid()
                if not srsid: srsid = 0
                return str(srsid)
            elif "project_postgis_srid" in p.keys():
                srsid = QgsProject.instance().crs().postgisSrid()
                if not srsid: srsid = 0
                return str(srsid)
            elif "expression" in p.keys():
                return "'" + p['expression'] + "'"
            elif "selection" in p.keys():
                return ','.join([str(elem) for elem in self.layer.selectedFeatureIds()])
        except Exception as e:
            self.info.err(e)
            return 'NULL'

# QGIS
# ['QOCISPATIAL', 'QOCISPATIAL8', 'QSPATIALITE', 'QSQLITE', 'QMYSQL', 'QMYSQL3', 'QODBC', 'QODBC3', 'QPSQL', 'QPSQL7']

# QSqlDatabase 5.13:
#
# QDB2 - IBM DB2
# QIBASE - Borland InterBase Driver
# QMYSQL - MySQL Driver
# QOCI - Oracle Call Interface Driver
# QODBC - ODBC Driver (includes Microsoft SQL Server)
# QPSQL - PostgreSQL Driver
# QSQLITE - SQLite version 3 or above
# QSQLITE2 - SQLite version 2
# QTDS - Sybase Adaptive Server
