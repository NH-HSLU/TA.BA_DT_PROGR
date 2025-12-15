# Konzept

Unsere Applikation beschäftigt sich mit der Datenauswertung direkt aus Revit.
Sie soll insbesondere Sachbearbeiter und Bauleiter eine schnelle Lösung für das erstellen von Modellbasierten Ausmassen ermöglichen.
Als Fokus haben wir uns die Aufteilung nach BKP gesetzt. Dadurch soll ein schnelles finden und Vergleichen möglich sein.

Die Auswergung soll anschliessend auf einem Streamlit Dashboard visualisiert und ausgewertet werden können.

Eine mögliche Erweiterung ist das Vergleichen von verschiedenen Versionen.

---

# Entwicklungsumgebung

Als Entwicklungsumgebung wurde VSCode gewählt.
In VSCode wurde ein Virtual Environment von Pyhon 3.13.7 erstellt, in welchem die Pakete vom requirements.txt installiert wurden.

> Requirements.txt:

```
# Datenanalyse
numpy              # Numerische Berechnungen und Arrays
pandas             # Tabellen-Verarbeitung und Analyse
matplotlib         # Datenplotting und Visualisierung

# Interaktive Visualisierung
plotly             # Interaktive Diagramme und Dashboards

# BIM/IFC-Projekte
streamlit          # Interaktive Apps und Dashboards
ifcopenshell       # Verarbeitung von IFC/BIM-Dateien

# Sonstige Nützliche Tools
openpyxl           # Verarbeitung von Excel-Dateien (.xlsx)
```

Auf GitHub haben wir ein Repository erstellt und alle Beteiligten als Contributer hinzugefügt: [GitHub Repository](https://github.com/NH-HSLU/TA.BA_DT_PROGR)

---

# Herausforderungen und nächste Schritte

Das instsllieren von pyRevit und die Integration von intelisense und Autocomplete in VSCode waren trotz guter Dokumentation eine Herausforderung.

Wir haben bereits mit pyRevit herumgespielt und einige Auswertungen erstellt und diese als CSV abgespeichert.

Als nächstes wollen wir die Verschiedenen Elemente nach BKP grupieren und in einer gemeinsamen CSV abspeichern.
