# swwat-gzp-template

Dieses repository enthält GIS Werkzeuge, welche zur Prüfung der Einhaltung der __[digitalen Datenanforderungen](https://www.bmnt.gv.at/wasser/wasser-oesterreich/foerderungen/foerd_hochwasserschutz/trl_gzp_42a_wrg.html)__ eines Gefahrenzonenplanes oder einer Abflussuntersuchung vor der Übernahme in die Hochwasserfachdatenbank zur Verfügung gestellt werden. Die Prüfung kann funktional gleichwertig mit ESRI ArcGIS for Desktop 10.6.1 oder QGIS (erfordert zumindest Version 3.4 LTR) durchgeführt werden. Geprüft werden:

>a)	  Datenschema aller Datensätze (Layer & Tabellen) gemäß der Datenanforderungen, <br>
>b)	  gültiger Eintrag in durch Auswahlwerte beschränkte Felder, <br>
>c)	  Befüllung aller Pflichtfelder, <br>
>d)	  korrekte Projektion aller räumlichen Datenlayer (MGI Austria Lambert, EPSG: 31287), <br>
>e)	  Überlappung der roten Gefahrenzone durch die gelbe Gefahrenzone.  <br>

Die Teilprüfungen (a–e) wurden als Tasks im GeoTaskOrganizer der Firma ms.GIS konfiguriert. Der GeoTaskOrganizer wird dem User für ArcGIS Desktop als Extension bzw. für QGIS als Plugin ohne zusätzliche Lizenzkosten und speziell zum Zweck der GZP Datenprüfung zur Verfügung gestellt. <br>

Anleitungen beschreiben die Installation und Handhabung des GeoTaskOrganizer für ArcGIS for Desktop und QGIS. Eine vorkonfigurierte Prüfung durch ArcGIS Pro ist derzeit nicht vorgesehen. 