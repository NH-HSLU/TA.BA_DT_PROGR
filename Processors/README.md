# Processors - eBKP-H Streamlit App

## Übersicht

Dieses Verzeichnis enthält die Streamlit Web-App zur Visualisierung von BKP-klassifizierten Baudaten nach dem eBKP-H (erweiterter Baukostenplan - Hochbau) Standard.

## Funktionen

Die App bietet folgende Features:

- **eBKP-H Gliederung**: Automatische Strukturierung nach Hauptgruppen (C, D, E, F, G)
- **Hierarchische Ansicht**: Aufklappbare Bereiche für Haupt- und Untergruppen
- **Zwischentotale**: Automatische Berechnung von Summen pro Gruppe
- **Visualisierungen**: Interaktive Diagramme (Pie-Charts, Bar-Charts)
- **Flexibel**: Unterstützt Kosten, Flächen und Mengenangaben
- **Export**: CSV-Export der gefilterten Daten

## Installation

Stellen Sie sicher, dass alle Abhängigkeiten installiert sind:

```bash
# Virtual Environment aktivieren
source ../.venv/bin/activate  # macOS/Linux
# ..\.venv\Scripts\activate    # Windows

# Requirements installieren (falls noch nicht geschehen)
pip install -r ../requirements.txt
```

## App starten

```bash
# Im Processors-Verzeichnis
streamlit run streamlit_app.py
```

Die App öffnet sich automatisch im Browser unter `http://localhost:8501`

## Verwendung

### 1. CSV-Datei vorbereiten

Ihre CSV-Datei muss mindestens folgende Spalte enthalten:

- **BKP_Code** (Pflicht): eBKP-H Code wie z.B. `C1.1`, `D2.3`, `E3.1`

Optionale Spalten:

- **BKP_Beschreibung**: Textuelle Beschreibung des BKP-Codes
- **Kosten**: Kosten in CHF (als Dezimalzahl)
- **Fläche (m²)** oder **Fläche**: Flächen in m²
- **Raum_Nummer**, **Raum_Name**: Raumzuordnung

**CSV-Format**: Semikolon-getrennt (`;`), UTF-8 Encoding

### 2. Beispieldaten testen

Eine Beispiel-CSV-Datei ist verfügbar unter:

```
Processors/beispiel_daten.csv
```

Diese Datei können Sie direkt in die App hochladen, um die Funktionalität zu testen.

### 3. Daten hochladen

1. Starten Sie die App
2. Klicken Sie in der Sidebar auf "CSV-Datei hochladen"
3. Wählen Sie Ihre CSV-Datei aus
4. Die Daten werden automatisch nach eBKP-H strukturiert

### 4. Daten analysieren

- **Übersicht**: Metriken zu Elementen, Codes, Hauptgruppen und Gesamtkosten
- **Visualisierungen**: Verteilung nach Hauptgruppen (Pie-Chart, Bar-Chart)
- **Detailansicht**: Klappen Sie die eBKP-H Hauptgruppen auf, um Details zu sehen
- **Zwischentotale**: Jede Gruppe zeigt automatisch die Summe
- **Rohdaten**: Vollständige Daten als Tabelle ansehen und exportieren

## eBKP-H Hauptgruppen

Die App unterstützt folgende Hauptgruppen:

| Code | Bezeichnung              | Beispiele                           |
|------|--------------------------|-------------------------------------|
| **C** | Bauwerk - Rohbau        | Fundamente, Wände, Decken          |
| **D** | Bauwerk - Technik       | Sanitär, Heizung, Elektro, Lüftung |
| **E** | Bauwerk - Ausbau        | Bodenbeläge, Wände, Türen, Fenster |
| **F** | Umgebung                | Aussenanlagen, Parkplätze          |
| **G** | Baunebenkosten          | Planung, Bauleitung                |

## Datenstruktur Beispiel

```csv
BKP_Code;BKP_Beschreibung;Kosten;Fläche (m²);Raum_Nummer;Raum_Name
C1.1;Baugrube;15000.00;120.50;-;-
D2.1;Sanitärinstallationen;12500.00;-;001;WC EG
E2.1;Bodenbeläge Keramik;6500.00;45.00;001;WC EG
```

## Integration mit pyRevit

Diese App ist für die Verwendung mit Daten aus pyRevit-Exports konzipiert:

1. Führen Sie pyRevit-Scripts in Revit aus (siehe `PyRevit_Extensions/` im DOODLES Branch)
2. Exportieren Sie die Daten als CSV
3. Stellen Sie sicher, dass die BKP-Zuordnung erfolgt ist (nutzen Sie `BKP_zuordnen.py`)
4. Laden Sie die CSV in die Streamlit-App

## Troubleshooting

**Problem**: CSV wird nicht geladen
- **Lösung**: Prüfen Sie, ob die Datei Semikolon-getrennt ist und UTF-8 Encoding hat

**Problem**: Keine BKP-Codes erkannt
- **Lösung**: Stellen Sie sicher, dass die Spalte `BKP_Code` heißt (exakt)

**Problem**: Kosten/Flächen werden nicht angezeigt
- **Lösung**: Spalten müssen genau `Kosten` oder `Fläche (m²)` heißen

## Weiterentwicklung

Geplante Features:

- [ ] Filter nach Räumen/Ebenen
- [ ] Kostenvergleich verschiedener Szenarien
- [ ] PDF-Export mit Berichten
- [ ] Integration mit BKP-Datenbank
- [ ] Automatische BKP-Zuordnung während Upload

## Lizenz

Universitätsprojekt - TA.BA_DT_PROGR
