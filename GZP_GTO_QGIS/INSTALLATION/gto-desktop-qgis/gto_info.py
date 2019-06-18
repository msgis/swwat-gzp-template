# -*- coding: utf-8 -*-

from builtins import str
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QObject
from qgis.core import *

class gtoInfo(QObject):
    def __init__(self, logobject, path = None, parent=None):
        super(gtoInfo,self).__init__(parent)
        self.path = path
        self.title = __name__
        self.iface = None
        self.metadata = None
        self.parent = None
        if isinstance(parent,QWidget):
            self.parent = parent
        try:
            self.metadata = logobject.metadata
        except:
            pass
        try:
            self.metadata = logobject.gtomain.metadata
        except:
            pass
        try:
            self.title= logobject.objectName()
            if self.title == "":
                self.title= __name__
        except:
            self.title = __name__
        try:
            if self.parent is None:
                self.iface = logobject.iface
                self.parent = self.iface.mainWindow()
        except:
            pass
        try:
            self.title = self.title.split(".")[1]
        except:
            pass

    def getLogPanelName(self):
        return __name__

    def log(self, *args):
        self.err(None,*args)

    def err(self,e, *args):
        if args is None and e is None: return
        from qgis.core import QgsMessageLog
        try:
            text = self.title + "::"
            if e is not None:
                level = Qgis.Critical
                import sys
                import os
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                text = text + " " + self.ArgsToText("ERROR:", exc_type, fname, "| line:", exc_tb.tb_lineno, "|", e.args)+ " " + self.ArgsToText(*args)
            else:
                level = Qgis.Info
                text = text + " " + self.ArgsToText(*args)
            QgsMessageLog.logMessage(text, __name__, level)
        except ValueError as e:
            QgsMessageLog.logMessage(str(e.args), __name__)
        try:
            if level == Qgis.Critical or 1 == 1:
                if self.metadata:
                    logfile= self.metadata.logfile
                    with open(logfile,'a') as f:
                        f.write(text  + '\n')
        except Exception as e:
            QgsMessageLog.logMessage(str(e.args), __name__)

    def msg(self,*args):
        from PyQt5.QtWidgets import QMessageBox
        try:
            self.getdialog(self.parent, self.title, self.ArgsToText(*args), QMessageBox.Information).exec_()
        except Exception as e:
            self.getdialog(self.parent, __name__, str(e.args),QMessageBox.Critical).exec_()

    def gtoWarning(self, *args):
        from PyQt5.QtWidgets import QMessageBox
        try:
            self.getdialog(self.parent, self.title, self.ArgsToText(*args), QMessageBox.Warning).exec_()
        except Exception as e:
            self.getdialog(self.parent, __name__, str(e.args),QMessageBox.Critical).exec_()

    def gtoCritical(self, *args):
        from PyQt5.QtWidgets import QMessageBox
        try:
            self.getdialog(self.parent, self.title, self.ArgsToText(*args), QMessageBox.Critical).exec_()
        except Exception as e:
            self.getdialog(self.parent, __name__, str(e.args),QMessageBox.Critical).exec_()

    def ArgsToText(self, *args):
        if args is None: return
        from PyQt5.QtWidgets import QMessageBox
        try:
            text =""
            for arg in args:
                text = text + " " + str(arg)
            text = text.strip()
            return text
        except Exception as e:
            self.getdialog(self.parent, __name__, str(e.args),QMessageBox.Critical).exec_()

    def getdialog(self, parent, title, text, icon):
        from PyQt5.QtWidgets import QMessageBox

        msg = QMessageBox(parent)
        msg.setIcon(icon)
        msg.setText(text)
        msg.setWindowTitle(title)
        msg.setStandardButtons(QMessageBox.Ok)
        return msg

class Info(gtoInfo):
        pass

