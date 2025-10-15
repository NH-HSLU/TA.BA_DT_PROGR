# TA.BA_DT_PROGR

## Abgaben

- Zwischenprüfung 1	[Milestone ZP1](https://github.com/NH-HSLU/TA.BA_DT_PROGR/milestone/1)
- Zwischenprüfung 2	[Milestone ZP2](https://github.com/NH-HSLU/TA.BA_DT_PROGR/milestone/2)
- Modulendprüfung		[Milestone MEP](https://github.com/NH-HSLU/TA.BA_DT_PROGR/milestone/3)

## Themenfindung
- [Themenwahl](https://github.com/NH-HSLU/TA.BA_DT_PROGR/blob/6a5c4a6addcccbeecd7ccce33cee674238e628ed/THEMENWAHL.md)

## Konzept
Folgendes FlowChart soll zum Besseren Verstehen des Prozesses genommen werden. Die genaue Anleitung ist in der Wiki abgespeichert.
```mermaid
---
config:
  layout: dagre
  look: neo
  theme: mc
---
flowchart TD
 subgraph s1["Wandauswertung"]
        n7["Alle Wände finden"]
        n17["Untitled Node"]
        n18["Etage zuweisen"]
        n19["Material aus Wandtyp"]
        n20["Geometrie Analysieren"]
        n21["Untitled Node"]
  end
 subgraph s2["Elektro Auswertung"]
        n8["Untitled Node"]
        n11["Alle Elemente vom Gewerk Elektro finden"]
        n12["für alle Elemente den Container (Raum) finden und zuordnen"]
        n13["Untergewerk zuordnen"]
        n14["Zusammenfassen nach BKP"]
        n15["Untitled Node"]
        n16["Starkstrom<br>Beleuchtung<br>Kommunikation<br>Sicherheit<br>"]
  end
 subgraph s3["Auswertung Boden/Decke"]
        n22["Untitled Node"]
        n23["Alle Slabs finden"]
        n24["Etage Zuweisen"]
        n25["Geometrische Auswertung"]
        n26["Boden und Decke Separat"]
        n27["Untitled Node"]
  end
    n5["Untitled Node"] --> n1["REVIT"]
    n6["Fehlende Informationen ergänzen"] L_n6_n4_0@-.-> n4["Darstellung in Streamlit-Dashboard"]
    n3["Auswertungen"] L_n3_n6_0@-.-> n6
    n1 --> s1 & s2 & s3
    s1 --> n3
    s2 --> n3
    n4 --> n9["Untitled Node"]
    n8 --> n11
    n11 --> n12
    n12 --> n13
    n13 --> n14
    n14 --> n15
    n16 ~~~ n14
    n17 --> n7
    n7 --> n18
    n18 --> n20
    n19 --> n21
    n20 --> n19
    n22 --> n23
    n23 --> n24
    n24 --> n25
    n26 ~~~ n25
    n12 ~~~ n16
    n23 ~~~ n26
    n25 --> n27
    s3 L_s3_n3_0@--> n3
    n17@{ shape: start}
    n21@{ shape: stop}
    n8@{ shape: start}
    n15@{ shape: stop}
    n16@{ shape: comment}
    n22@{ shape: start}
    n26@{ shape: comment}
    n27@{ shape: stop}
    n5@{ shape: start}
    n1@{ shape: db}
    n6@{ shape: manual-input}
    n3@{ shape: docs}
    n9@{ shape: stop}
     n1:::Sky
    classDef Sky stroke-width:1px, stroke-dasharray:none, stroke:#374D7C, fill:#E2EBFF, color:#374D7C
    style s1 fill:transparent
    style s2 fill:transparent
    style s3 fill:transparent
    L_n6_n4_0@{ animation: slow } 
    L_n3_n6_0@{ animation: slow } 
    L_s3_n3_0@{ animation: none }
