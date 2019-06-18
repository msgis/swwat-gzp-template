# -*- coding: utf-8 -*-

from __future__ import print_function
from builtins import str
from .gto_info import gtoInfo
from PyQt5.QtCore import QObject

class gtoHelper(QObject):
    def __init__(self,gtomain):
        super(gtoHelper, self).__init__()
        self.setObjectName(__name__)
        self.gtomain=gtomain
        self.metadata = self.gtomain.metadata
        self.info = gtoInfo(self)
        self.debug = self.gtomain.gtoplugin.debug

    def getName(self,value):
        try:
            result = []
            for c in value:
                if not c.isdigit():
                    result.append(c)
            return ''.join(result)
        except Exception as e:
            return ''

    def dispatch(self,obj, value, run=True):
        method_name = value
        try:
            method = getattr(obj, method_name)
        except AttributeError:
            # fix_print_with_import
            print((method_name, "not found"))
        else:
            if run:
                method()
            else:
                return method

    def findToolbar(self,iface,toolbarobjectname):
        from PyQt5.QtWidgets import QToolBar
        found= None
        try:
            toolbars = iface.mainWindow().findChildren(QToolBar)
            for toolbar in toolbars:
                if toolbar.objectName() == toolbarobjectname:
                    found = toolbar
                    break
        except Exception as e:
            pass
        finally:
            return found

    def gettext(self,text):
        debug=False
        from qgis.core import QgsMessageLog

        res = text
        if debug: QgsMessageLog.logMessage('==========', __name__)
        if debug: QgsMessageLog.logMessage('gettext ' + str(type(res)), __name__)
        try:
            res = u'%s' % text
            return res
        except:
            pass
        try:
            if debug: QgsMessageLog.logMessage('int', __name__)
            if isinstance(text,int):
                res=str(text)
                return res
        except:
            pass
        # try:
        #     if debug: QgsMessageLog.logMessage('unicode', __name__)
        #     res = unicode(text)
        #     if debug: QgsMessageLog.logMessage(res, __name__)
        #     return res
        # except:
        #     pass
        try:
            if debug: QgsMessageLog.logMessage('sys encode', __name__)
            import sys
            res = text.decode(sys.getfilesystemencoding())
            if debug: QgsMessageLog.logMessage(res, __name__)
            return res
        except:
            pass
        try:
            if debug: QgsMessageLog.logMessage('arg 0', __name__)
            res = text[0]
            if debug: QgsMessageLog.logMessage(res, __name__)
            return res
        except:
            pass
        try:
            if debug: QgsMessageLog.logMessage('latin-1', __name__)
            res = text.decode('latin-1')
            if debug: QgsMessageLog.logMessage(res, __name__)
            return res
        except:
            pass
        try:
            if debug: QgsMessageLog.logMessage('str', __name__)
            res = str(text)
            if debug: QgsMessageLog.logMessage(res, __name__)
            return res
        except:
            pass
        if debug: QgsMessageLog.logMessage('none', __name__)
        return res

    def checkFileExists (self,file, ordner = None):
        try:
            import os
            if os.path.isfile(file):
                return file
            if ordner is not None:
                file = os.path.join(ordner, file)
                if os.path.isfile(file):
                    return file
        except Exception as e:
            return None

    def getsetting(self,dic, key, default, *not_allowed):
        try:
            x = None
            try:
                x = dic[key]
            except:
                return default
            if x is not None:
                for n in not_allowed:
                    if x == n: x =  default
            else:
                for n in not_allowed:
                    if n is None: x = default
            return x
        except Exception as e:
            return 'getsetting' + e.args[0]

    def getFilenameExt(self,file):
        try:
            filename = file.split(".")[0]
            ext = file.split(".")[-1]
            return filename, ext
        except:
            pass

    def startApplication(self,app_path,filepath=None):
        try:
            import subprocess
            subprocess.call(app_path, filepath)
        except Exception as e:
            return 'startApplication' + e.args[0]

    def startFile(self,filepath):
        try:
            import os
            os.startfile(filepath)
        except Exception as e:
            return 'startFile' + e.args[0]

    def getFilePath (self,filepath, createPath = False):
        import os
        try:
            filepath =  filepath.replace('%APPDATA%',os.environ.get('APPDATA'))
            filedir = os.path.dirname((filepath))
            if createPath and not os.path.exists(filedir):
                os.makedirs(filedir)
            return filepath
        except Exception as e:
            return 'getFilePath' + e.args[0]


    def getTableName(self,layer):
        try:
            uri = layer.dataProvider().dataSourceUri()
            if self.debug: self.info.log("URI:",uri)
            try:
                uri = uri[uri.find("table="):]
                uri = uri.split("=")
                uri = uri[1]
                uri = uri.split('"')
                uri = uri[1]
                return uri
            except:
                return layer.name()
        except Exception as e:
            self.info.err(e)

    def timestamp(self,):
        try:
            # import datetime
            # import pytz
            # ts = datetime.datetime.now().timestamp()
            # d = datetime.datetime.utcfromtimestamp(ts)
            # return d

            # import datetime
            # return datetime.datetime.now().timestamp()
            import time
            ts = time.gmtime()
            return str(time.strftime("%Y%m%d#%H%M%S", ts))

        except Exception as e:
            self.info.err(e)


    def importModule(self,filepath, modulename):
        module = None
        try:
            import importlib.util
            import sys
            module = sys.modules[modulename]
            if module is None:
                spec = importlib.util.spec_from_file_location(modulename, filepath)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                # Optional; only necessary if you want to be able to import the module
                # by name later.
                sys.modules[modulename] = module
                return module
        except:
            pass
