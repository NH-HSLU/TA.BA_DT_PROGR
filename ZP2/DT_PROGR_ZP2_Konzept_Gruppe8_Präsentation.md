---
marp: true
title: Zwischenpräsentation 2
theme: uncover
header: "TA.BA_DT_PROGR.H25 | Zwischenpräsentation 2"
footer: "Gruppe 8 | 15. Dezember 2025"
paginate: true
---
<style>
section { font-size: 30px; }
</style>

<!-- _header: "" -->
<!-- _footer: "15. Dezember 2025" -->
<!-- _paginate: skip -->
<!-- _class: invert -->

![width:150](LOGO.gif)

# eBKP⁺
eBKP-H Klassifizierung
⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
Ein pyRevit-Plugin von Nicole und Orlando

---

## Konzept

- Datenauswertung mit **pyRevit** direkt aus dem Revit Modell
- Schnelles, modellbasiertes **Ausmass nach eBKP-H**
  mit Anthropic's [Haiku](https://www.anthropic.com/claude/haiku) KI-Modell
- Visualisierung und Export mit **Streamlit**

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
- Prompt für eBKP-H Kategorisierung > Antwort in **JSON** Format.

---

## Erfolge

- eBKP-H Kategorisierung mit KI
- Export aus pyRevit
- übersichtliche Visualisierung in Streamlit

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

![width:1000px](KI_Klassifizierung_Dashboard.png)

---

![width:1000px](KI_Monitoring.png)

---

![width:1000px](KI_Response.png)

---

## Erkenntnisse

- ~~Einzelne Bauteil-Kategorien pro Liste Auswerten~~
  ➤ Alle Bauteil-Kategorien in einer Liste Auswerten
- Claude funktioniert viel besser mit `#TODO Änderung` als reinem umschreiben vom Problem das gelöst werden soll


---

### Nächste Schritte

1. ~~Alle Elemente in einer **Excel**-Liste exportieren~~
2. ~~Elemente mit **BKP** klassifizieren~~
3. ~~**Streamlit**-Dashboard erstellen~~
4. Auswertung als **PDF** exportieren
5. **Kostenberechnung** nach verschiedenen Methoden

#### Optional

1. Flächen-/ Volumenauswertung nach **SIA416**

---

<!-- _header: "" -->

<!-- _footer: "" -->

<!-- _paginate: skip -->

<!-- _class: invert -->

> If a picture is worth a thousand words,
>
> a prototype is worth a thousand meetings,

— *Tom & David Kelley, IDEO*
