# Processors - eBKP-H Streamlit App

## Übersicht

Dieses Verzeichnis enthält die Streamlit Web-App zur Visualisierung von BKP-klassifizierten Baudaten nach dem eBKP-H (erweiterter Baukostenplan - Hochbau) Standard.

## Funktionen

Die App bietet folgende Features:

### eBKP-H Auswertung
- **eBKP-H Gliederung**: Automatische Strukturierung nach Hauptgruppen (C, D, E, F, G)
- **Hierarchische Ansicht**: Aufklappbare Bereiche für Haupt- und Untergruppen
- **Zwischentotale**: Automatische Berechnung von Summen pro Gruppe
- **Visualisierungen**: Interaktive Diagramme (Pie-Charts, Bar-Charts)
- **Flexibel**: Unterstützt Kosten, Flächen und Mengenangaben
- **Export**: CSV-Export der gefilterten Daten

### KI-Klassifizierung (NEU)
- **Automatische BKP-Zuordnung**: Mit Claude AI (Anthropic)
- **Batch-Verarbeitung**: Effiziente Klassifizierung mehrerer Elemente
- **Live-Monitoring**: Echtzeit-Anzeige der API-Responses während Verarbeitung
- **Konfidenz-Scores**: Bewertung der Klassifizierungsqualität
- **Debug-Modus**: Detaillierte API-Response-Logs

### BKP-Bearbeitung (NEU)
- **Manuelle Korrektur**: Bearbeiten Sie KI-Klassifizierungen
- **Inline-Editing**: Direkt in der Tabelle bearbeiten
- **Intelligente Filter**: Nach Konfidenz oder BKP-Gruppe filtern
- **Validierung**: Automatische Prüfung von BKP-Code-Format
- **Workflow-Integration**: Nahtloser Übergang zur Auswertung

### Dark Mode Support (NEU)
- Alle Seiten unterstützen automatisch Light und Dark Mode
- Native Streamlit-Komponenten für optimale Darstellung

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

### Workflow 1: Direkte Visualisierung (mit BKP-Codes)

Wenn Ihre Daten bereits BKP-klassifiziert sind:

1. **CSV-Datei vorbereiten**
   - Mindestens Spalte **BKP_Code** erforderlich
   - Optionale Spalten: BKP_Beschreibung, Kosten, Fläche, Raum_Nummer
   - Format: Semikolon-getrennt (`;`), UTF-8 Encoding

2. **Zur eBKP-H Auswertung gehen**
   - CSV hochladen
   - Automatische Strukturierung nach eBKP-H
   - Visualisierungen ansehen
   - Berichte exportieren

3. **Beispieldaten**: `Processors/beispiel_daten.csv`

### Workflow 2: KI-Klassifizierung + Bearbeitung + Visualisierung (NEU)

Wenn Ihre Daten noch keine BKP-Codes haben:

1. **API-Key konfigurieren** (Seite "Einstellungen")
   - Anthropic API-Key eingeben
   - Key validieren
   - Oder `.env` Datei verwenden: `ANTHROPIC_API_KEY=sk-ant-...`

2. **KI-Klassifizierung** (Seite "KI Klassifizierung")
   - CSV ohne BKP-Codes hochladen
   - Spalten zuordnen (Typ, Kategorie, Familie)
   - Batch-Modus wählen (empfohlen)
   - Klassifizierung starten
   - **Live-Monitoring**: Sehen Sie API-Responses in Echtzeit
   - Ergebnisse prüfen (Tab "Ergebnisse")

3. **BKP-Codes bearbeiten** (Seite "BKP Bearbeiten") - OPTIONAL
   - Automatisch geladen von KI-Klassifizierung
   - Filtern Sie nach niedriger Konfidenz
   - Bearbeiten Sie Codes direkt in der Tabelle
   - Validierung prüft Code-Format
   - Änderungen speichern

4. **Visualisierung** (Seite "eBKP-H Auswertung")
   - Daten automatisch verfügbar
   - Hierarchische Ansicht
   - Interaktive Diagramme
   - CSV-Export

5. **Beispieldaten**: `Processors/muster_ki_klassifizierung.csv`

### Testdaten

- **`beispiel_daten.csv`**: 40 Einträge MIT BKP-Codes → für Auswertung
- **`muster_ki_klassifizierung.csv`**: 30 Einträge OHNE BKP-Codes → für KI-Klassifizierung

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

## KI-Klassifizierung Details

### API-Key Management
- **Session State**: Temporär für aktuelle Sitzung (Seite "Einstellungen")
- **`.env` Datei**: Persistent (empfohlen für Entwicklung)

### Kostenabschätzung
Das Tool verwendet Claude 3.5 Haiku:
- **Input**: ~$0.80 / 1M tokens
- **Output**: ~$4.00 / 1M tokens
- **Pro Element**: ~$0.0001 (Batch), ~$0.0002 (Einzeln)

### Live-Monitoring
Die App zeigt während der Klassifizierung:
- **Fortschrittsbalken**: Aktuelle Position
- **Status-Text**: Aktuelles Element/Batch
- **Live-Responses**: Letzte 5 API-Antworten
- **Tab "KI Responses"**: Alle Details mit Raw JSON

### Confidence Scores
- **≥ 0.9**: Sehr sicher
- **0.7 - 0.9**: Sicher
- **0.5 - 0.7**: Unsicher (Überprüfung empfohlen)
- **< 0.5**: Manuelle Korrektur erforderlich

## Dark Mode

Alle Seiten der App unterstützen automatisch Light und Dark Mode:
- Native Streamlit-Komponenten passen sich automatisch an
- Keine fixen Farben, die in Dark Mode unleserlich sind
- Optimale Kontraste in beiden Modi

## Weiterentwicklung

Geplante Features:

- [ ] Filter nach Räumen/Ebenen
- [ ] Kostenvergleich verschiedener Szenarien
- [ ] PDF-Export mit Berichten
- [ ] Integration mit erweiterter BKP-Datenbank
- [x] Automatische BKP-Zuordnung mit KI ✅
- [x] Manuelle BKP-Bearbeitung ✅
- [x] Live API-Response Monitoring ✅
- [x] Dark Mode Support ✅

## Lizenz

Universitätsprojekt - TA.BA_DT_PROGR
