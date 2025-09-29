# Themenwahl

Gemäss [Aufgabenstellung](AUFGABENSTELLUNG.md) soll ein eigenständiges Programm entwickelt werden, welches einen der folgenden Zwecke beinhaltet:

- Datenauswertung
- «IFC Editor»
- Einfaches «Model Checker/Qualifier»
- Daten-Visualisierung (Dashboards)
- Calculator(Wettbewerb, Kosten, Nachhaltigkeit, Kreislaufwirtschaft, etc.)

## FINAL

Ausmass mit Objektgliederung und BKP anhand PyRevit mit Fokus auf Architektur und Elektro.
Visualisierung der Kostenaufteilung nach BKP oder Räumlichkeit.

### Zusatz

Qualitätschecker der Attribute, ob alle benötigten Attribute für die saubere Auflistung angegeben und ausgefüllt sind.

## Konzepte

Wir haben uns für das Modul folgende Konzepte überlegt:

### Stückzahlauswertung / Ausmass

Die Elemente werden ausgelesen und nach BKP eingeordnet.
zudem soll eine Objektgliederung nach Gebäude, Etage und Raum möglich sein.
Mehr- und Minderkosten werden durch Varianten Berechnet und angezeigt.

Kostenermittlung, woher kommen die Preise?

### Energieberechnung nach SIA 2024

Die Flächen und Typen sollen direkt aus dem IFC modell gelesen werden.
Eigenverbrauchoptimierung von PVA und Speicher.

Anbindung an ein GIS für Solarberechnung?

### Wie BIM ich?

Für welchen Use-Case kann ich mein Modell nutzen?
Use-Case wählen und sehen was alles angepasst werden muss.

Wer stellt die Anforderungen der Use-Cases an das BIM-Modell?

### Wettbewerbschecker

Wurden alle Voraussetzungen an die Flächen eingehalten? Welche nicht?
Visualisierung der Raumanteile eventuell auch in 3D(?)

Pre-Checks, ob das Modell einen nutzbaren Otput generieren kann.
Kombination mit *Wie BIM ich?* möglich.

### CO₂-Quick-Estimator

Liefert kg CO₂e pro Etage und Gebäude.

### Collision-to-Cost

Aus einem BCF die clash-Region ermitteln und aufgrund der Elemente die Kosten für die Änderung der einzelnen Gewerke vorschlagend. Basierend auf Stundenansätzen.

Woher kriegen wir die Stundenansätze +- her?
