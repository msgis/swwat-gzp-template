from builtins import str
from builtins import object
import win32gui
import re

class WindowMgr(object):
    """Encapsulates some calls to the winapi for window management"""
    def __init__ (self,gtoObj,debug):
        """Constructor"""
        self._handle = None
        self.debug = debug
        self.gtoObj =gtoObj

    def find_window(self, class_name, window_name = None):
        """find a window by its class_name"""
        self._handle = win32gui.FindWindow(class_name, window_name)
        if self.debug: self.gtoObj.info.log("Found window handle:",window_name, self.handle)

    def _window_enum_callback(self, hwnd, wildcard):
        '''Pass to win32gui.EnumWindows() to check all the opened windows'''
        if re.match(wildcard, str(win32gui.GetWindowText(hwnd))) != None:
            self._handle = hwnd

    def find_window_wildcard(self, wildcard):
        self._handle = None
        win32gui.EnumWindows(self._window_enum_callback, wildcard)

    def set_foreground(self):
        """put the window in the foreground"""
        win32gui.SetForegroundWindow(self._handle)

def ActivateApp (gtoObj,debug,title,file):
    if debug:gtoObj.info.log('ActivateApp:', title,file )
    import win32com.client
    import win32process
    import os
    try:
        wmgr = WindowMgr(gtoObj,debug)
        wmgr.find_window_wildcard(title)
        hwnd  = wmgr._handle
        if debug: gtoObj.info.log ("Found window handle for <%s>:" % title,hwnd)

        _, pid = win32process.GetWindowThreadProcessId(wmgr._handle)
        shell = win32com.client.Dispatch("WScript.Shell")
        if hwnd is None:
            if debug: gtoObj.info.log("Start file:",file)
            os.startfile(file)
            #shell.Run(file)
        else:
            if debug: gtoObj.info.log("Activate app:",hwnd)
            shell.AppActivate(pid)
            shell.SendKeys ("% r{ENTER}")

    except Exception as e:
        gtoObj.info.err(e)

def ReactivatePreviousApp ():
    import win32com.client
    import win32gui
    import win32process

    hwnd = win32gui.GetForegroundWindow()

    _, pid = win32process.GetWindowThreadProcessId(hwnd)

    shell = win32com.client.Dispatch("WScript.Shell")

    shell.AppActivate('Console2')
    shell.SendKeys('{UP}{ENTER}')

    shell.AppActivate(pid)

def getLogin():
    import win32api
    import win32net
    import win32netcon
    def UserGetInfo():
        dc = win32net.NetServerEnum(None, 100, win32netcon.SV_TYPE_DOMAIN_CTRL)
        user = win32api.GetUserName()
        if dc[0]:
            dcname = dc[0][0]['name']
            return win32net.NetUserGetInfo("\\\\" + dcname, user, 1)
        else:
            return win32net.NetUserGetInfo(None, user, 1)

def openfile(file):
    import win32com.client
    def raw(text):
        escape_dict = {'\a': r'\a',
                       '\b': r'\b',
                       '\c': r'\c',
                       '\f': r'\f',
                       '\n': r'\n',
                       '\r': r'\r',
                       '\t': r'\t',
                       '\v': r'\v',
                       '\'': r'\'',
                       '\"': r'\"',
                       '\0': r'\0',
                       '\1': r'\1',
                       '\2': r'\2',
                       '\3': r'\3',
                       '\4': r'\4',
                       '\5': r'\5',
                       '\6': r'\6',
                       '\7': r'\7',
                       '\8': r'\8',
                       '\9': r'\9',
                       '\256': r'\256'}  # notice this line is the first 3 digits of the resolution

        for k in escape_dict:
            if text.find(k) > -1:
                text = text.replace(k, escape_dict[k])

        return text

    shell = win32com.client.Dispatch("WScript.Shell")
    try:
        shell.Run(str(file))
        return True
    except:
        pass
    try:
        shell.Run(raw("\\" + file))
        return True
    except:
        pass#unc failed
    try:
        shell.Run(raw(file))
        return True
    except:
        pass #raw only failed