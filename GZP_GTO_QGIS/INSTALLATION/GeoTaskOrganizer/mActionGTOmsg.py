#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

class run(QObject):
    def __init__(self, id, gtotool, config, debug):
        super(run, self).__init__()
        try:
            iface = gtotool.iface
            resval =""
            #tool data
            title =  config.get("title", "GeoTaskOrganizer")
            text = config.get("text", "???")
            informativetext = config.get('informativetext', None)
            detailedtext = config.get("detailedtext", None)
            icon = config.get("icon", 1)

            button_ok_caption = config.get('button_ok_caption', "Ok")  # None: button not set. important!
            button_ok_tools = config.get("button_ok_tools", [])

            button_yes_caption = config.get('button_yes_caption', "Yes")# None: button not set. important!
            button_yes_tools = config.get("button_yes_tools", [])

            button_no_caption = config.get('button_no_caption', "No")  # None: button not set. important!
            button_no_tools = config.get("button_no_tools", [])

            button_cancel_tools = config.get("button_cancel_tools", [])
            button_cancel_caption =config.get('button_cancel_caption', "Cancel")#None: button not set. important!

            msg = QMessageBox(iface.mainWindow())
            msg.setWindowTitle(title)
            msg.setText(text)
            if informativetext is not None:
                msg.setInformativeText(informativetext)
            if detailedtext is not None:
                msg.setDetailedText(detailedtext)
            if icon == 0:#no icon/ok
                msg.setIcon(QMessageBox.NoIcon)
            elif icon == 1:
                msg.setIcon(QMessageBox.Information)
            elif icon == 2:
                msg.setIcon(QMessageBox.Warning)
            elif icon == 3:
                msg.setIcon(QMessageBox.Critical)
            elif icon == 4:
                msg.setIcon(QMessageBox.Question)
            else:
                msg.setIcon(QMessageBox.Information)

            if button_ok_caption is not None: msg.addButton(button_ok_caption, QMessageBox.AcceptRole)
            if button_yes_caption is not None: msg.addButton(button_yes_caption, QMessageBox.YesRole)
            if button_no_caption is not None: msg.addButton(button_no_caption, QMessageBox.NoRole)
            if button_cancel_caption is not None: msg.addButton(button_cancel_caption, QMessageBox.RejectRole)

            #msg.buttonClicked.connect(msgbtn_clicked)
            retval = msg.exec_()
            resval = msg.clickedButton().text()
            if debug: gtotool.info.log (resval)

            if resval == button_ok_caption:
                gtotool.gtomain.runcmd(button_ok_tools)
            elif resval == button_yes_caption:
                gtotool.gtomain.runcmd(button_yes_tools)
            elif resval == button_no_caption:
                gtotool.gtomain.runcmd(button_no_tools)
            elif resval == button_cancel_caption:
                gtotool.gtomain.runcmd(button_cancel_tools)
        except Exception as e:
            gtotool.info.err(e)

    # def msgbtn_clicked(self, msgbtn):
    #     resval = msgbtn.text()




