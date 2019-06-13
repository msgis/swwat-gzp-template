# swwat-gzp-template

Dieses repository enthält GIS Werkzeuge, welche zur Prüfung der Einhaltung der __[digitalen Datenanforderungen](https://www.bmnt.gv.at/wasser/wasser-oesterreich/foerderungen/foerd_hochwasserschutz/trl_gzp_42a_wrg.html)__ eines Gefahrenzonenplanes oder einer Abflussuntersuchung vor der Übernahme in die Hochwasserfachdatenbank zur Verfügung gestellt werden. Die Prüfung kann funktional gleichwertig mit ESRI ArcGIS for Desktop 10.6.1 oder QGIS (erfordert zumindest Version 3.4 LTR) durchgeführt werden. Geprüft werden:

a)	  Datenschema aller Datensätze (Layer & Tabellen) gemäß der Datenanforderungen, <br>
b)	  gültiger Eintrag in durch Auswahlwerte beschränkte Felder, <br>
c)	  Befüllung aller Pflichtfelder, <br>
d)	  korrekte Projektion aller räumlichen Datenlayer (MGI Austria Lambert, EPSG: 31287), <br>
e)	  Überlappung der roten Gefahrenzone durch die gelbe Gefahrenzone.  <br>

Die Teilprüfungen (a–e) wurden als Tasks im GeoTaskOrganizer der Firma ms.GIS konfiguriert. Der GeoTaskOrganizer wird dem User für ArcGIS Desktop als Extension bzw. für QGIS als Plugin ohne zusätzliche Lizenzkosten und speziell zum Zweck der GZP Datenprüfung zur Verfügung gestellt. <br>

Anleitungen beschreiben die Installation und Handhabung des GeoTaskOrganizer für ArcGIS for Desktop und QGIS. Eine vorkonfigurierte Prüfung durch ArcGIS Pro ist derzeit nicht vorgesehen. <br><br>

***
#### Änderungen in v2.2.0 gegenüber den Digitale Datenanforderungen, Fassung Juni 2018 <br>
Die angeführten Schemaänderungen sind bereits in den Datenvorlagen GZP.gpkg bzw. GZP.gdb der Release v2.2.0 umgesetzt. <br> **Datensätze** (= Tabellen und Layer) sind in fett, *Felder* in kursiv gekennzeichnet.

-  Bundeslandkennung (XX_) im Namen von **allen Datensätzen** entfernt.  <br>
-  **Alle Datensätze** mit einem Feld <font color=blue>*KURZRID*</font> haben auch ein zusätzliches Feld <font color=blue>*LANDRID*</font>, beide mit Datentyp TEXT.
-  Zusammenführung von **BPxyz** und **BWval** zu Punktlayer **BWERT** (Bemessungswerte) mit Ersatz des Auswahlfelds <font color=blue>*BW_KAT*</font> durch die Felder <font color=blue>*QMAX*</font>, <font color=blue>*QSPEZ*</font> und <font color=blue>*GFRACHT*</font>, alle Datentyp ZAHL,  sowie ein zusätzliches Feld PKT_ID, Datentyp TEXT.
-  Zusätzliches Feld <font color=blue>*ABSID*</font>, Datentyp GANZZAHL, für AbschnittsID.
-  Ersatz des Feldes <font color=blue>*G_SCHUTZ*</font> in **TBGGN** durch den Linienlayer **GSCHUTZ** (Schutzgrad). Schema wie **LPAKT**, jedoch mit Verwendung der Auswahlwerte der Kategorie "Allgemeiner Schutzgrad Gewässer“ im Feld <font color=blue>*L_KATEGO*</font> .
-  Ersatz der Tabelle **EDVKZ_SZENARIO** durch einen Punktlayer **KNTPKT** mit gleichen Attributen wie EDVKZ_SZENARIO, jedoch ohne die Felder <font color=blue>*KNT_X*</font> und <font color=blue>*KNT_Y*</font>, da nun bereits in der Geometrie verspeichert.
-  Projektion **aller Layer**: MGI/ Austrian Lambert (EPSG: 31287).
