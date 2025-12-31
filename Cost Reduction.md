exportierte Daten aus pyRevit mit je einem Element pro Zeile

Eindeutige Werte von Kategorie, Familie, Typ, Zusatzinfos finden und in klassifizierungstabelle schreiben.
also werden alle Wände Typ 1 nur als 1 Element gespeichert für die klassifizierung.
Diese klassifizierungsID muss ich irgendwo speichern, dass man noch weiss, welches Element mit welcher klassifizierung später zusammengeführt werden muss.

Diese neue klassifizierungs Tabelle mit einzigartigen Values wird dann wie gewohnt an die KI gesendet

Die klassifizierten ergebnisse werden dann mithilfe der klassifizierungsIDs in die Elemente Liste von pyRevit geschrieben

die neue liste mit allen Elementen und klassifizierungen wird dann visualisiert.
