# -*- coding: utf-8 -*-

from __future__ import print_function
from builtins import str
def getName(value):
    try:
        result = []
        for c in value:
            if not c.isdigit():
                result.append(c)
        return ''.join(result)
    except Exception as e:
        return ''

def dispatch(obj, value, run=True):
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

def findToolbar(iface,toolbarobjectname):
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

def gettext(text):
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

def checkFileExists (file, ordner = None):
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

def getsetting(dic, key, default, *not_allowed):
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

def getFilenameExt(file):
    try:
        filename = file.split(".")[0]
        ext = file.split(".")[-1]
        return filename, ext
    except:
        pass

def startApplication(app_path,filepath=None):
    try:
        import subprocess
        subprocess.call(app_path, filepath)
    except Exception as e:
        return 'startApplication' + e.args[0]

def startFile(filepath):
    try:
        import os
        os.startfile(filepath)
    except Exception as e:
        return 'startFile' + e.args[0]

def getFilePath (filepath, createPath = False):
    import os
    try:
        filepath =  filepath.replace('%APPDATA%',os.environ.get('APPDATA'))
        filedir = os.path.dirname((filepath))
        if createPath and not os.path.exists(filedir):
            os.makedirs(filedir)
        return filepath
    except Exception as e:
        return 'getFilePath' + e.args[0]


def getTableName(layer):
    uri = layer.dataProvider().dataSourceUri()
    uri = uri[uri.find("table="):]
    uri = uri.split("=")
    uri = uri[1]
    uri = uri.split('"')
    uri = uri[1]
    return uri

def timestamp():
    import datetime
    import pytz
    ts = datetime.datetime.now().timestamp()
    d = datetime.datetime.utcfromtimestamp(ts)
    return d

    # import datetime
    # return datetime.datetime.now().timestamp()
    import time
    ts = time.gmtime()
    return str(time.strftime("%Y%m%d#%H%M%S", ts))


def importModule(filepath, modulename):
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
