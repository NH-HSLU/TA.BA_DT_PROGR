# TA.BA_DT_PROGR

## Abgaben

- Zwischenprüfung 1	[Milestone ZP1](https://github.com/NH-HSLU/TA.BA_DT_PROGR/milestone/1)
- Zwischenprüfung 2	[Milestone ZP2](https://github.com/NH-HSLU/TA.BA_DT_PROGR/milestone/2)
- Modulendprüfung		[Milestone MEP](https://github.com/NH-HSLU/TA.BA_DT_PROGR/milestone/3)

## Konzept

Der folgende Workflow zeigt eine übersicht der verschiedenen Schritte, welche unserer Applikation hat.

```mermaid
---
config:
  layout: elk
---
flowchart LR
    revit["BIM-Modell<br>in <b>Revit</b>"] --> auswerten["Auswertung<br>mit <b>pyRevit</b>"]
    auswerten --> auswertung["Auswertungen<br>als <b>CSV</b>"]
    auswertung --> darstellen["Darstellung<br>in <b>Streamlit</b>"]
    ergaenzen["Informationen<br>ergänzen"] --> n1["Export als <b>PDF</b>"]
    darstellen --> ergaenzen
    revit@{ shape: db}
    auswerten@{ shape: in-out}
    auswertung@{ shape: docs}
    darstellen@{ shape: event}
    ergaenzen@{ shape: in-out}
    n1@{ shape: docs}
```

## Datenstruktur

Für eine Effiziente Auswertung und Handhabung der Daten haben wir uns für den Datenaustausch für folgende Datanstruktur entschieden:

```mermaid
---
config:
  class:
    hideEmptyMembersBox: true
---
classDiagram
direction TB
    class data_holder {
        +String Export_Folder
        +List Elements
	    set_BPK(element)
	    get_Info(element)
    }
    class COMMON {
	    +String Level
	    +String ifcType
	    +String GUID
    }
    class WALL {
	    +Float Length
	    +Float Width
	    +Float Height
	    +Float Volume
	    +String Structure_Material
    }
    class ROOM {
	    +String Room_Number
	    +String Room_Name
	    +Float Area
    }
    class CELING {
	    +Float Thickness
	    +Float Area
	    +Float Volume
	    +String Structure_Material
    }

    COMMON -- WALL
    COMMON -- ROOM
    COMMON -- CELING
```

## Python Module

Die Pythonmodule sind für eine einfachere Handhabung und Modularität in folgende Files unterteilt:

```mermaid
---
config:
  theme: redux
  layout: dagre
  look: classic
---
flowchart TD
    n1["pyRevit"] --> n4["Überprüfen"] & n5["Auswertung"]
    n5 --> n10["CSV"]
    A(["MAIN"]) --> n2["Streamlit"] & n3["Processors"]
    n2 --> n6["Dashboard"] & n7["Eingabe"] & n8["Export"]
    n8 --> n9["PDF"]
    n3 --> n11["Verarbeitung<br>Auswertung"] & n12["PDF Exporter"] & n13["Input Handler"]
    n14["Revit"] --> n1
    n10@{ shape: doc}
    n9@{ shape: doc}
    n14@{ shape: db}
    style n10 stroke:#00C853,stroke-width:4px,stroke-dasharray: 0
    style A stroke-width:4px,stroke-dasharray: 0,stroke:#2962FF
    style n9 stroke:#D50000,stroke-width:4px,stroke-dasharray: 0
```
