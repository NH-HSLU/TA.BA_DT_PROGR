---
marp: true
title: Modulabschlussprüfung
theme: uncover
header: "TA.BA_DT_PROGR.H25 | Modulabschlussprüfung"
footer: "Gruppe 8 | 22. Januar 2026"
paginate: true
---
<style>
section { font-size: 30px; }
</style>

<!-- _header: "" -->
<!-- _footer: "22. Januar 2026" -->
<!-- _paginate: skip -->
<!-- _class: invert -->

![width:150](LOGO.gif)

# eBKP-H⁺
eBKP-H Klassifizierung und Kostenermittlung
⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
Ein pyRevit-Plugin von Nicole und Orlando

---

## Konzept

- Datenauswertung mit **pyRevit** direkt aus dem Revit Modell
- Schnelles, modellbasiertes **Ausmass nach eBKP-H**
  mit Anthropic's [Haiku](https://www.anthropic.com/claude/haiku) KI-Modell
- Visualisierung und Export mit **Streamlit**

---

## Struktur


![width:1000](Simplyfied.png)

---

## Revit

![height:200](pyRevit.png)

---

## Streamlit

![height:200](Kostenermittlung.png)

![width:1000](Klassifizierung.png)

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
- Prompt für eBKP-H Kategorisierung > Antwort in **JSON** Format
- richtige Kostenberechnung mit Kostenkatalog
- Manuelles Eintragen von Kosten und darstellen in der Auswertung

---

## Erfolge

- eBKP-H Kategorisierung mit KI
- Export der Elemente mit pyRevit
- übersichtliche Visualisierungen in Streamlit
- Export Kostenberechnung als PDF

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

![width:1000px](image.png)

---

!![width:1000px](image-1.png)

---

![width:1000px](image-2.png)

---

![width:1000px](image-3.png)

---

![width:1000px](image-4.png)

---

![width:1000px](image-5.png)

---

![width:1000px](image-6.png)

---

![width:1000px](image-7.png)

---

![width:1000px](image-8.png)

---

![width:1000px](image-9.png)

---

## Erkenntnisse

- ~~Einzelne Bauteil-Kategorien pro Liste Auswerten~~
  ➤ Alle Bauteil-Kategorien in einer Liste Auswerten
- Claude funktioniert viel besser mit `#TODO Änderung` als reinem umschreiben vom Problem das gelöst werden soll
- Gute Promts schreiben "Du bist ein Softewareentwickler und machst..."
- Teilsweise sinnvoll von neuem zu beginnen als der Fehler zu suchen und probieren zu beheben (Kostenberechnung)

---

### Projektziele erreicht

1. Alle Elemente in einer Liste exportieren
2. Elemente mit **eBKP-H-Code** klassifizieren
3. **Streamlit**-Dashboard erstellen
4. **Kostenberechnung** nach verschiedenen Genauigkeiten
5. Auswertung als **PDF** exportieren

---

### Erweiterung vom Projekt

1. Kostenberechnung auf Genauigkeit überprüfen ⇒ mit Experten sprechen
2. ArchiCAD Plugin erstellen
3. IFC Einlesen
4. Projektinformation aus den Projektfiles lesen
5. Ausführbare Datei erstellen (.exe und .app)

---

<!-- _header: "" -->
<!-- _footer: "" -->
<!-- _paginate: skip -->
<!-- _class: invert -->

> 
> Plans are nice and models are better,
> 
> but a running app is what actually changes how we build.
> 

— *Orlando & Nicole, HSLU*