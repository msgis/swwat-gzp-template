from PyQt5.QtCore import QSettings
from qgis.core import QgsMessageLog, Qgis

def run_script(iface):#for scriptrunner, iface is for accessing QGIS API
    print ("===========run_script=============")
    s = QSettings()
    key = "qgis/digitizing/default_snap_enabled"
    val = "true"
    s.setValue(key,val)

    for k in s.allKeys(): 
        val = s.value(k)
        if k == key:
            print (k + ":" + str(val))#console
            QgsMessageLog.logMessage(k + ":" + str(val),"Qgis Settings",Qgis.Info )#qgis message log
    
    print("with parameters:")
    parameters = [5,6]
    run_script2(iface,parameters)
    
    print("with dicontary (key/value pairs)")
    settings ={"Land": "Österreich","PI": 3.14}
    run_script3(iface,settings)
    
    print ("With both")
    run_script4(iface,parameters,settings)
    
def run_script2(iface,*args):
    print (str(args))
    QgsMessageLog.logMessage("params:"+ str(args),"Qgis Settings",Qgis.Info )#qgis message log
    
def run_script3(iface,*kwargs):
    print(str(kwargs))
    QgsMessageLog.logMessage("settings" + str(kwargs), "Qgis Settings",Qgis.Info )#qgis message log
    
def run_script4(iface, *args,**kwargs):
    QgsMessageLog.logMessage("params:" + str(args) + "settings" + str(kwargs), "Qgis Settings",Qgis.Info )#qgis message log
    for p in args:
        print(p)
    for k in kwargs.keys():
        print (k,"=",kwargs[k])
    print ("finished")   

try:  
    run_script(iface)
except Exception as e:
    print (e.args)
