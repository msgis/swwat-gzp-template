from PyQt5.QtCore import QSettings, QStandardPaths
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QSplashScreen
import os

try:
    s = QSettings()
    s.setValue("PythonPlugins/GeoTaskOrganizer", True)
    s.setValue("qgis/iconSize", 32)
    s.setValue("qgis/stylesheet/iconSize", 32)
    s.setValue("qgis/stylesheet/fontPointSize", 12)
except:
    pass

try:
    widgets = QApplication.allWidgets()
    for wid in widgets:
        if isinstance(wid, QSplashScreen):
            qgisAppDataPath = QStandardPaths.standardLocations(QStandardPaths.AppDataLocation)[0]
            file = os.path.join(qgisAppDataPath, "splash.png")
            if os.path.isfile(file):
                pixmap = QPixmap(file)
                wid.setPixmap(pixmap)
            break
except:
    pass
