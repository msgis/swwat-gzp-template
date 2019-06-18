#!/usr/bin/python
# -*- coding: utf-8 -*-

from builtins import str
from PyQt5.QtCore import *
#from PyQt5.QtSql import *
from PyQt5.QtWidgets import *
from qgis.core import QgsDataSourceUri, QgsFeatureRequest
from qgis.PyQt.QtSql import QSqlDatabase,QSqlQuery

class run(QObject):
    def __init__(self, id, gtotool, config, debug):
        super(run, self).__init__()
        self.debug = gtotool.debug
        self.info = gtotool.info
        self.iface =gtotool.iface
        self.infotext = ""
        try:
            #read metadata
            procedure = config.get('procedure',None)
            driver=config.get('driver',None)
            server = config.get('server',None)
            database = config.get('database',None)
            port=config.get('port',None)
            user=config.get('user',None)
            password=config.get('password',None)
            parameters = config.get('parameters',None)
            if not parameters:parameters=[]
            message = config.get('message','')
            editsession = config.get('editsession',True)
            refreshmap = config.get('refreshmap',True)
            limit = config.get('limit',10000)

            #declare vars
            sql=procedure#Sql string
            layer = None
            provider = None
            db = None
            uri = None
            uselayer = False
            if driver is None: uselayer = True
            if uselayer:#use active layer
                if debug: self.info.log("using layer")
                try:
                    layer = self.iface.activeLayer()
                    if layer:
                        # use the workspace of the active layer:
                        # get data provider
                        provider = layer.dataProvider()
                        provider_name = provider.name()
                        uri = QgsDataSourceUri(provider.dataSourceUri())
                        # get connection
                        if provider_name == "oracle":
                            db =QSqlDatabase.addDatabase('QOCISPATIAL') #QSqlDatabase.addDatabase('QOCI')
                            sql = "BEGIN " + procedure + "%s" + ";" + " END;"
                        elif provider_name == "postgres":
                            db = QSqlDatabase.addDatabase('QPSQL')
                        else:
                            if debug: self.info.msg("Unknown provider: \n" + provider_name + "\nTry using ODBC...")
                            db = QSqlDatabase.addDatabase('QODBC')# ODBC Driver (includes Microsoft SQL Server)
                            sql = "EXEC " + procedure + "%s"
                        if db.isValid():
                            db.setHostName(uri.host())
                            db.setDatabaseName(uri.database())
                            try:#uri.port could be ''
                                db.setPort(int(uri.port()))
                            except Exception as e:
                                self.info.err(e,'Invalid port number')
                            db.setUserName(uri.username())
                            db.setPassword(uri.password())
                        else:
                            self.info.log("INVALID database")
                            self.info.log(self.con_info(db, layer))
                            return
                    else:
                        self.info.gtoWarning("No active layer set!")
                        return
                except Exception as e:
                    self.info.err(e)
            else:#use db connection and call procedure
                #db = QSqlDatabase.addDatabase(driver,"qWLK")
                if debug: self.info.log("using config-parameters")
                db = QSqlDatabase.addDatabase(driver)#without name its default
                if server is not None: db.setHostName(server)
                if database is not None: db.setDatabaseName(database)
                if port is not None: db.setPort(int(port))
                if user is not None: db.setUserName(user)
                if password is not None: db.setPassword(password)
            if debug: self.info.log(self.con_info(db, layer))
            if db.open():
                if uselayer:
                    ok = True  # no features is also ok
                    if layer.selectedFeatureCount() > 0:
                        if layer.selectedFeatureCount() > limit:
                            self.info.gtoWarning("Count of selected features higher than limit!\nOnly %i features will be processed!" % limit)
                        if editsession:
                            if not layer.isEditable(): layer.startEditing()
                            layer.beginEditCommand(self.infotext)
                        try:
                            #features = layer.selectedFeatures()#slow one
                            request = QgsFeatureRequest()
                            request.setFilterFids(layer.selectedFeatureIds())
                            fields =[]
                            for p in parameters:
                                if isinstance(p,str):
                                    fields.append(p)
                            request.setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes(fields, layer.fields())
                            request.setLimit(limit)
                            flag = True
                            for feat in layer.getFeatures(request):
                                #build sql
                                sqlexe = sql % self.preparesql(layer, feat, parameters)
                                if debug and flag:
                                    self.info.log(sqlexe)
                                    flag = False
                                query = QSqlQuery(db)#query = db.exec_(sql)#obsolete...
                                query.prepare(sqlexe)
                                ok = query.exec_()
                            if editsession:
                                layer.endEditCommand()
                                #layer.commitChanges()#stop editing
                        except Exception as e:
                            if editsession:
                                try:
                                    layer.destroyEditCommand()
                                except:
                                    pass
                            self.info.gtoWarning(e.args)
                            ok = False
                    else:
                        message = "No features selected!"
                else:
                    sqlexe = sql %  self.preparesql(None, None, parameters)
                    if debug: self.info.log(sqlexe)
                    # if db is not specified, or is invalid, the application's default database
                    # is used. If query is not an empty string, it will be executed
                    query = QSqlQuery(db)#query = db.exec_(sql)#obsolete...if  arg string not empty, it will be executed on default db!
                    query.prepare(sqlexe)
                    ok = query.exec_()
                    #another possibility
                    # query = QSqlQuery(sqlexe,db)#executes with db
                    # ok = query.isActive()
                if ok:
                    if message != "":#everything is fine!
                        QMessageBox.information(self.iface.mainWindow(), self.infotext, message)
                else:
                    self.info.log(db.drivers())
                    self.info.log(query.lastError().databaseText())
                    self.info.gtoWarning(query.lastError().databaseText())
                    refreshmap = True
                db.close()
                if refreshmap:#todo which one???
                    self.iface.mapCanvas().refresh()
                    self.iface.mapCanvas().refreshAllLayers()
            else:
                err = db.lastError()
                self.info.gtoWarning(err.text())
        except Exception as e:
            self.info.err(e)

    def con_info(self, db, layer = None):
        try:
            info = ""
            dbinfo='Database info:\n'
            layerinfo ='Layer info:\n'
            if db:
                dbinfo = "driver: " + db.driverName() + "\nhost: " + db.hostName() + "\ndatabase: " + db.databaseName() + "\nport: " \
                       + str(db.port()) + "\nuser: " + db.userName() + "\npassword: " + db.password()
            if layer:
                provider = layer.dataProvider()
                if provider:
                    uri = QgsDataSourceUri(provider.dataSourceUri())
                    layerinfo = "\nActive layer: " + layer.name() + "\nlayer provider: " + provider.name() + "\n"
                    layerinfo = layerinfo + "URI: host:" + uri.host() + "\ndatabse:" + uri.database() + "\nport" + uri.port()
                    layerinfo = layerinfo + "\nuser:" + uri.username() + "\npassword:" + uri.password()
            info =dbinfo + layerinfo
        except Exception as e:
            self.info.err(e)
        finally:
            return (info)

    def preparesql(self, layer, feat, parameters):
        try:
            expr = ""
            for p in parameters:
                v = p
                if layer and feat:
                    if isinstance(p, str):
                        id = layer.fields().lookupField(p)
                        if id != -1:
                            v = feat.attributes()[id]
                if v is not None:
                    if isinstance(v, str) :
                        expr = expr + "'%s'," % v
                    else:
                        expr = expr + "%s," % str(v)
                else:
                    expr = expr + "NULL,"
            if expr.endswith(","): expr = expr[:-1]  # remove last colon
            return "(" + expr + ")"
        except Exception as e:
            self.info.err(e)