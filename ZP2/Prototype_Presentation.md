---
marp: true
title: Zwischenpräsentation 1
theme: uncover
header: "TA.BA_DT_PROGR.H25 | Zwischenpräsentation 1"
footer: "Gruppe 8 | 27. Oktober 2025"
paginate: true
---
<style>
section { font-size: 30px; }
</style>

<!-- _header: "" -->

<!-- _footer: "27. Oktober 2025" -->

<!-- _paginate: skip -->

<!-- _class: invert -->

# eBKP-H Klassifizierung

_Ein pyRevit-Plugin von Nicole und Orlando_

---

## Konzept

- Datenauswertung mit **pyRevit** direkt aus dem Revit Modell
- Schnelles, modellbasiertes **Ausmass nach eBKP-H** mit [Haiku](https://www.anthropic.com/claude/haiku)
- Visualisierung und Export mit **Streamlit**
- **Kostenberechnung** nach verschiedenen Methoden

---

## Entwicklungsumgebung

- [Visual Studio Code](https://code.visualstudio.com/) als IDE
- Virtual Environment mit Python **3.13.7**
- [pyRevit](https://pyrevitlabs.notion.site/) als Schnittstelle zwischen Python und Revit
- [GitHub](https://github.com/NH-HSLU/TA.BA_DT_PROGR) Repository

#### zusätzliche Tools:

- [Mermaid](https://www.mermaidchart.com/) Flowchart-Diagramme erstellen
- [Marp](https://marp.app/) Slides aus Markdown-Syntax

---

## Python-Bibliotheken

**Datenanalyse**

```
numpy           # Numerische Berechnungen und Arrays   
pandas          # Tabellen-Verarbeitung und Analyse
```

**Visualisierung**

```
matplotlib      # Datenplotting und Visualisierung
plotly          # Diagramme und Dashboards.          
streamlit       # Apps und Dashboards.               
```

**Sonstige nützliche Tools**

```
openpyxl        # Verarbeitung von Excel-Dateien (.xlsx).  
```

---

## Herausforderungen

- Datenexport mit Schichtaufbau aus Revit

---

## Erfolge

- eBKP-H Kategorisierung über Claude API
- 

---

<!-- _header: "" -->

<!-- _footer: "" -->

<!-- _paginate: skip -->

<!-- _class: invert -->

# STREAMLIT
Klassifizierung mit Haiku
Visualisierung der Ergebnisse
Kostenberechnung

---

![width:1100px](KI_Klassifizierung_Dashboard.png)

---

![width:1100px](KI_Monitoring.png)

---

![width:1100px](KI_Response.png)

---

## Nächste Schritte

1. ~~Alle Elemente in einer **Excel**-Liste exportieren~~
2. ~~Elemente mit **BKP** klassifizieren~~
3. ~~**Streamlit**-Dashboard erstellen~~
4. Auswertung als **PDF** exportieren
5. Flächen-/ Volumenauswertung nach **SIA416**
6. Kostenberechnung nach verschiedenen Methoden

---

<!-- _header: "" -->
<!-- _footer: "" -->
<!-- _paginate: skip -->
<!-- _class: invert -->
 
>  
>  
> If a picture is worth a thousand words,
>  
> a prototype is worth a thousand meetings,
>  
>  

— *Tom & David Kelley, IDEO*
