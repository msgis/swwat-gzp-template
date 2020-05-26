from PyQt5.QtCore import Qt, QFile, QTextStream, QStandardPaths
from PyQt5.QtGui import QIcon, QPixmap, QFont, QBrush, QColor
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QAction, QWidgetAction, QDockWidget, QTreeWidgetItem, \
    QSplashScreen, \
    QHBoxLayout, QLabel, QToolButton, QComboBox, QSizePolicy, QToolBar, QHeaderView, QVBoxLayout, QSpacerItem

from qgis.core import Qgis, QgsMapLayerProxyModel, QgsVectorLayerCache, QgsFeatureRequest, QgsVectorLayer
from qgis.gui import QgsMapLayerComboBox, QgsAttributeTableView, QgsAttributeTableModel, QgsAttributeTableFilterModel, \
    QgsScaleRangeWidget, QgsScaleComboBox, QgsScaleWidget

from .gto_widgets import *
from .gto_point import GTOPointWidget


class GtoActionActiveLayer(QWidgetAction):
    def __init__(self, gtoObj, parent=None):
        super(GtoActionActiveLayer, self).__init__(parent)
        self.setObjectName('mActionGTOactivelayer')
        self.gtomain = gtoObj.gtomain

        self.single_use = False
        if self.single_use:
            self.setDefaultWidget(GtoWidgetActiveLayer(self.gtomain, parent))

    def createWidget(self, parent):
        if not self.single_use:
            return GtoWidgetActiveLayer(self.gtomain, parent)


class GtoActionLayerCombo(QWidgetAction):
    def __init__(self, gtoObj, parent=None):
        super(GtoActionLayerCombo, self).__init__(parent)
        self.setObjectName('mActionGTOlayers')
        self.gtomain = gtoObj.gtomain

    def createWidget(self, parent):
        return GtoWidgetQgisLayers(self.gtomain, parent)


class GtoActionVersion(QWidgetAction):
    def __init__(self, gtoObj, parent=None):
        super(GtoActionVersion, self).__init__(parent)
        self.setObjectName('mActionGTOversion')
        self.gtomain = gtoObj.gtomain
        self.helper = self.gtomain.helper

    def createWidget(self, parent):
        lbl = QLabel("GTO " + self.helper.getGTOversion())
        wid = QWidget(parent)
        layout = QHBoxLayout(wid)
        layout.addWidget(lbl)
        wid.setLayout(layout)
        wid.setStyleSheet("QWidget{background: transparent;}")
        return wid


class GtoActionQgisVersion(QWidgetAction):
    def __init__(self, gtoObj, parent=None):
        super(GtoActionQgisVersion, self).__init__(parent)
        self.setObjectName('mActionQGISversion')
        self.gtomain = gtoObj.gtomain
        self.helper = self.gtomain.helper

    def createWidget(self, parent):
        lbl = QLabel('Qgis ' + Qgis.QGIS_VERSION)
        wid = QWidget(parent)
        layout = QHBoxLayout(wid)
        layout.addWidget(lbl)
        wid.setLayout(layout)
        wid.setStyleSheet("QWidget{background: transparent;}")
        return wid


class GtoActionQgisFile(QWidgetAction):
    def __init__(self, gtoObj, parent=None):
        super(GtoActionQgisFile, self).__init__(parent)
        self.setObjectName('mActionQGISfile')
        self.gtomain = gtoObj.gtomain
        self.helper = self.gtomain.helper

    def createWidget(self, parent):
        class MyLabel(QLabel):
            def __init__(self, gtomain):
                super(MyLabel, self).__init__(parent)
                self.gtomain = gtomain
                self.prj = QgsProject.instance()
                self.prj.fileNameChanged.connect(self.qgs_changed)
                self.prj.homePathChanged.connect(self.qgs_changed)
                self.qgs_changed()

            def qgs_changed(self, *a0):
                try:
                    self.setText(os.path.abspath(self.prj.absoluteFilePath()))
                except:
                    pass

        lbl = MyLabel(self.gtomain)
        wid = QWidget(parent)
        layout = QHBoxLayout(wid)
        layout.addWidget(lbl)
        wid.setLayout(layout)
        wid.setStyleSheet("QWidget{background: transparent;}")
        return wid


class GtoActionHomepage(QWidgetAction):
    def __init__(self, gtoObj, parent=None):
        super(GtoActionHomepage, self).__init__(parent)
        self.setObjectName('mActionGTOhomepage')

        self.gtomain = gtoObj.gtomain
        self.iface = self.gtomain.iface
        self.helper = self.gtomain.helper

    def openHomePage(self):
        import webbrowser
        webbrowser.open('http://msgis.com/')

    def createWidget(self, parent):
        tb = QToolButton()
        tb.setText("msgis Homepage")
        tb.setIcon(self.helper.getIcon('msgis.png'))
        tb.setToolTip('Homepage msgis.com')
        tb.setIconSize(self.iface.iconSize(False))
        tb.clicked.connect(self.openHomePage)

        wid = QWidget(parent)
        layout = QVBoxLayout(wid)
        layout.addWidget(tb)
        wid.setLayout(layout)
        return wid


class GtoActionPoint(QWidgetAction):
    def __init__(self, gtoObj, parent=None):
        super(GtoActionPoint, self).__init__(parent)
        self.setObjectName('mActionGTOpoint')

        self.single_use = True
        if self.single_use:
            self.setDefaultWidget(GTOPointWidget(gtoObj, parent=parent))


class GtoActionScale(QWidgetAction):
    def __init__(self, gtoObj, parent=None):
        super(GtoActionScale, self).__init__(parent)

        self.setObjectName('mActionGTOscale')

        self.gtomain = gtoObj.gtomain

    def createWidget(self, parent):
        wid = GtoWidgetScale(self.gtomain, parent)
        return wid


class GtoActionProjectionSelection(QWidgetAction):
    def __init__(self, gtoObj, parent=None):
        super(GtoActionProjectionSelection, self).__init__(parent)

        self.setObjectName('mActionGTOprojectionSelection')

        self.gtomain = gtoObj.gtomain

    def createWidget(self, parent):
        wid = GtoWidgetProjectionSelection(self.gtomain, parent)
        return wid


class GtoActionSpacer(QWidgetAction):
    def __init__(self, gtoObj, parent=None):
        super(GtoActionSpacer, self).__init__(parent)

        self.setObjectName('mActionGTOspacer')

        self.gtomain = gtoObj.gtomain

    def createWidget(self, parent):
        spacer = QWidget(parent)
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        spacer.setStyleSheet("QWidget{background: transparent;}")
        # spacer= QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        return spacer
