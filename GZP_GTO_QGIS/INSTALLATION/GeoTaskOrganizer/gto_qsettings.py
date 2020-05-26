from PyQt5.QtCore import Qt, pyqtSlot, QSortFilterProxyModel, QSettings, QRegExp
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLineEdit, QDialog, QTableView, QLabel, QHeaderView, \
    QPushButton, QSpacerItem, QSizePolicy, QAbstractItemView, QCheckBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem

import random
import json


class GtoQgisSettingsDialog(QDialog):
    def __init__(self, gtomain, parent=None):
        super(GtoQgisSettingsDialog, self).__init__(parent)
        # gto
        self.gtomain = gtomain
        self.info = self.gtomain.info
        self.helper = self.gtomain.helper
        self.debug = self.gtomain.debug
        self.iface = self.gtomain.iface
        try:
            # references
            self.undoList = []
            self.setWindowTitle('QGIS settings')
            self.setSizeGripEnabled(True)

            self.model = QStandardItemModel(self)
            self.model.setColumnCount(2)
            self.model.setHeaderData(0, Qt.Horizontal, "key")
            self.model.setHeaderData(1, Qt.Horizontal, "value")

            s = QSettings()
            for key in s.allKeys():
                val = s.value(key)
                items = []
                itKey = QStandardItem(key)
                itKey.setEditable(False)
                items.append(itKey)
                try:
                    items.append(QStandardItem(val))
                    self.model.appendRow(items)
                except Exception as e:
                    pass
                    # if self.debug: self.info.err(e)

            self._proxy = MyFilter(self)
            self._proxy.setSourceModel(self.model)

            self.model.itemChanged.connect(self.dataChanged)  # QstandardItem

            # create gui
            self.tableview = QTableView()
            self.tableview.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.tableview.horizontalHeader().setSectionsMovable(False)
            self.tableview.setSelectionBehavior(QAbstractItemView.SelectRows)  # SelectItems
            self.tableview.setSelectionMode(QAbstractItemView.SingleSelection)
            self.tableview.setModel(self._proxy)

            self.search = QLineEdit()
            self.search.textChanged.connect(self.on_text_changed)
            self.btnDelete = QPushButton('Delete')
            self.btnDelete.clicked.connect(self.delete)
            self.btnAddRandowKey = QPushButton('add key')
            self.btnAddRandowKey.clicked.connect(self.addRandomKey)
            self.btnAddRandowKey.setHidden(not self.debug)
            # self.btnDelete.setEnabled(self.debug)
            self.btnUndo = QPushButton("Undo")
            self.btnUndo.setEnabled(False)
            self.btnUndo.clicked.connect(self.undo)
            self.btnCopy = QPushButton('Copy')
            self.btnCopy.clicked.connect(self.copy)
            self.chkPureJson = QCheckBox('Pure json')
            # layout search
            laySearch = QHBoxLayout()
            laySearch.addWidget(QLabel('Suche:'))
            laySearch.addWidget(self.search)
            # layout buttons
            layBtns = QHBoxLayout()
            layBtns.addWidget(self.btnAddRandowKey)
            layBtns.addWidget(self.btnDelete)
            layBtns.addWidget(self.btnUndo)
            hspacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
            layBtns.addItem(hspacer)
            layBtns.addWidget(self.btnCopy)
            layBtns.addWidget(self.chkPureJson)
            # layout dialog
            self.layout = QVBoxLayout(self.iface.mainWindow())
            self.layout.addLayout(laySearch)
            self.layout.addWidget(self.tableview)
            self.layout.addLayout(layBtns)

            self.setLayout(self.layout)
            self.resize(640, 480)

            self.tableview.sortByColumn(0, Qt.AscendingOrder)
            self.tableview.setSortingEnabled(True)
            self.tableview.selectRow(0)
        except Exception as e:
            self.info.err(e)

    def addRandomKey(self):
        try:
            if self.debug:
                val = str(random.random() * 100)
                key = val[0:1] + "/" + val[3:5]
                self.setQvalue(key, float(val))
                items = []
                it = QStandardItem(key)
                it.setEditable(False)
                items.append(it)
                items.append(QStandardItem(val))
                self.model.appendRow(items)
        except Exception as e:
            self.info.err(e)

    def copy(self):
        try:
            index = self.tableview.currentIndex()
            key = self._proxy.index(index.row(), 0).data(0)
            val = self._proxy.index(index.row(), 1).data(0)
            s = QSettings()
            val = s.value(key)
            if self.debug: self.info.log("copy key:", key)
            if self.debug: self.info.log("copy val", val)
            if self.debug: self.info.log("copy Qval", val)
            if self.chkPureJson.isChecked():
                val = json.dumps(val, ensure_ascii=False)
            else:
                val = self.getValue(val)
            text = '"{0}":{1},\n'.format(key, val)
            if self.debug: self.info.log("copy:", text)
            self.helper.copyToClipboard(text)
        except Exception as e:
            self.info.err(e)

    def getValue(self, val):
        try:  # readable json expression: true instead of "true" or 9.99 instead of "9.99"
            if val is not None:
                try:  # bool :S
                    if val == "true": return json.dumps(True, ensure_ascii=False)
                    if val == "false": return json.dumps(False, ensure_ascii=False)
                    if val.lower() == "true": return json.dumps(True, ensure_ascii=False)
                    if val.lower() == "false": return json.dumps(False, ensure_ascii=False)
                except:
                    pass
                try:  # integer
                    return int(val)
                except:
                    pass
                try:  # float
                    return float(val)
                except:
                    pass
                if val is not None:
                    if isinstance(val, str): return json.dumps(val, ensure_ascii=False)
                    if not (isinstance(val, list) or isinstance(val, dict)):
                        val = [val]
                        lst = json.dumps(val, ensure_ascii=False)
                        val = lst[1:-1]
                if val == "": val = None
            return json.dumps(val, ensure_ascii=False)
        except Exception as e:
            if self.debug: self.info.err(e)
            return val

    def delete(self, *args):
        try:
            index = self._proxy.mapSelectionToSource(self.tableview.selectionModel().selection()).indexes()[0]
            row = index.row()
            items = self.model.takeRow(row)  # QList<QStandardItem>
            key = items[0].data(0)
            val = items[1].data(0)
            if self.debug: self.info.log("delete key:", key)
            if self.debug: self.info.log("delte val", val)
            s = QSettings()
            s.remove(key)

            self.undoList.append((index, items))
            self.btnUndo.setEnabled(True)
        except Exception as e:
            self.info.err(e)

    def undo(self):
        try:
            if len(self.undoList) > 0:
                self.undoList.reverse()
                index, items = self.undoList[0]

                key = items[0].data(0)
                val = items[1].data(0)
                if self.debug: self.info.log("undo key:", key)
                if self.debug: self.info.log("undo val", val)
                self.setQvalue(key, val)

                self.model.insertRow(index.row(), items)

                tabindex = self._proxy.mapFromSource(index)
                self.tableview.selectRow(tabindex.row())

                del self.undoList[0]
                self.undoList.reverse()
            if len(self.undoList) == 0: self.btnUndo.setEnabled(False)
        except Exception as e:
            self.info.err(e)

    def dataChanged(self, item):
        try:
            val = item.data(0)
            key = self.model.item(item.row(), 0).data(0)
            if self.debug: self.info.log("datachanged key:", key)
            if self.debug: self.info.log("datachanged val", val)
            self.setQvalue(key, val)
        except Exception as e:
            self.info.err(e)

    def setQvalue(self, key, val):
        try:
            s = QSettings()
            s.setValue(key, val)
        except Exception as e:
            self.info.err(e)

    @pyqtSlot(str)
    def on_text_changed(self, text):
        try:
            regExp = QRegExp(text, Qt.CaseInsensitive, QRegExp.Wildcard)
            self._proxy.setFilterRegExp(regExp)
        except Exception as e:
            self.info.err(e)


class MyFilter(QSortFilterProxyModel):
    def __init__(self, parent):
        QSortFilterProxyModel.__init__(self, parent)

    def filterAcceptsRow(self, sourceRow, sourceParent):
        index0 = self.sourceModel().index(sourceRow, 0, sourceParent)
        index1 = self.sourceModel().index(sourceRow, 1, sourceParent)
        regex = self.filterRegExp()
        return regex.indexIn(self.sourceModel().data(index0)) != -1 or regex.indexIn(
            str(self.sourceModel().data(index1))) != -1

# if __name__ == '__main__':
#     import sys
#
#     app = QApplication(sys.argv)
#     w = GtoQgisSettingsDialog()
#     w.show()
#     sys.exit(app.exec_())
# else:
#     w = GtoQgisSettingsDialog()
#     w.show()
