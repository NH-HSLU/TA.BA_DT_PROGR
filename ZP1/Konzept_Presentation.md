---
marp: true
title: Zwischenpräsentation 1
theme: uncover
header: "TA.BA_DT_PROGR.H25"
footer: "Zwischenprüfung 1 | Gruppe 8"
paginate: true
---

<style>
section { font-size: 25px; }
</style>

<!-- _header: "" -->
<!-- _footer: "" -->
<!-- _paginate: skip -->
<!-- _class: invert -->

# Ausmass und Kostenvoranschlag

_Ein pyRevit-Plugin von Nicole und Orlando_

---

# Konzept

- Datenauswertung mit **pyRevit**
- Schnelles, modellbasiertes **Ausmass nach BKP**
- Visualisierung und Export mit **Streamlit**

---

# Workflow

![width:1000px height:200px](DT_PROGR_Flow_simplified.svg)

---

# Entwicklungsumgebung

- **Visual Studio Code** als Entwicklungsumgebung
- Virtual Environment mit Python **3.13.7**
- [GitHub Repository](https://github.com/NH-HSLU/TA.BA_DT_PROGR)

### zusätzliche Tools:

- [Mermaid](https://www.mermaidchart.com/) Flowchart-Diagramme erstellen
- [Marp](https://marp.app/) Slides aus Markdown Dateien

---

## Wichtige Python-Bibliotheken

**Datenanalyse**

```
numpy           # Numerische Berechnungen und Arrays       
pandas          # Tabellen-Verarbeitung und Analyse
matplotlib      # Datenplotting und Visualisierung
```

**Interaktive Visualisierung**

```
plotly          # Interaktive Diagramme und Dashboards.    
```

**BIM/IFC-Projekte**

```
streamlit       # Interaktive Apps und Dashboards
ifcopenshell    # Verarbeitung von IFC/BIM-Dateien.        
```

**Sonstige nützliche Tools**

```
openpyxl        # Verarbeitung von Excel-Dateien (.xlsx).  
```

---

# Herausforderungen

- pyRevit-Intellisense und Autocomplete
- Geeignete pyRevit-Syntax finden

---

# Nächste Schritte

1. Alle wichtigen Elemente einzeln exportieren
2. Elemente zusammenführen in eine Liste
3. Streamlit-Dashboard erstellen

---

<!-- _header: "" -->
<!-- _footer: "" -->
<!-- _paginate: skip -->
<!-- _class: invert -->

> ​
> ​
> Tell me and I forget,
> 
> teach me and I may remember,
> 
> involve me and I learn.
> ​
> ​

— *Benjamin Franklin*