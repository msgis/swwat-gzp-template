from qgis.core import *
from qgis.gui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


def run_script(iface, *args, **kwargs):
    try:
        # QgsMessageLog.logMessage('script: ' + __file__, __name__, 0)
        parameters = args
        settings = kwargs
        # script:
        # set select features als aktuelle tool
        act = iface.mainWindow().findChild(QAction, "mActionSelectFeatures")
        if act is not None:
            act.trigger()
            return "mActionSelectFeatures"
        else:
            return "Not found: mActionSelectFeatures"
        # script end
    except Exception as e:
        QgsMessageLog.logMessage(e.args[0], __name__)

# test with QGIS console:
# run_script (iface,[],{})
