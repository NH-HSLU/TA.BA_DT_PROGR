# Helpers - BKP Klassifizierung mit KI

Dieses Modul ermöglicht die automatische Klassifizierung von Revit Bauelementen nach e-BKP-h Standard mit Anthropic Claude AI.

## Installation

```bash
# Abhängigkeiten installieren
pip install -r requirements.txt
```

## Konfiguration

API Key in `.env` Datei (bereits konfiguriert):
```
ANTHROPIC_API_KEY=sk-ant-api03-...
```

## Verwendung

### 1. Einzelnes Element klassifizieren

```python
from Helpers.BKP_Classifier import BKPClassifier

classifier = BKPClassifier()
result = classifier.classify_element(
    element_type="Steckdose T13",
    category="Electrical Fixtures",
    family="Steckdose Standard"
)

print(f"BKP Code: {result['bkp_code']}")
print(f"Confidence: {result['confidence']:.0%}")
# Output: BKP Code: C13, Confidence: 95%
```

### 2. Mehrere Elemente (Batch - effizienter!)

```python
from Helpers.BKP_Classifier import BKPClassifier

classifier = BKPClassifier()
elements = [
    {'type': 'Steckdose', 'category': 'Electrical Fixtures'},
    {'type': 'LED Leuchte', 'category': 'Lighting Fixtures'},
    {'type': 'Wand Gips', 'category': 'Walls'},
]

results = classifier.classify_batch(elements)
for elem, result in zip(elements, results):
    print(f"{elem['type']} -> {result['bkp_code']} ({result['confidence']:.0%})")
```

### 3. CSV-Export aus pyRevit verarbeiten

```python
from Helpers.BKP_Classifier_Example import classify_csv_export

# CSV mit BKP-Codes anreichern
classify_csv_export(
    csv_path='export_raum_daten.csv',
    output_path='export_raum_daten_mit_bkp.csv'
)
```

Oder direkt per Kommandozeile:
```bash
python Helpers/BKP_Classifier_Example.py export_raum_daten.csv
```

### 4. Quick-Helper für einfache Nutzung

```python
from Helpers.BKP_Classifier import classify_revit_element

result = classify_revit_element("Steckdose", category="Electrical")
print(f"BKP: {result['bkp_code']}")
```

## e-BKP-h Codes (Auszug)

### Elektro (C)
- **C1**: Starkstrom
  - C11: Starkstromhauptverteilung
  - C12: Installationsverteilungen
  - C13: Steckdosen
  - C14: Leuchten
  - C15: Sicherheitsbeleuchtung
- **C2**: Schwachstrom
  - C21: Telefon/Daten
  - C22: Alarm/Sicherheit

### Haustechnik (D)
- **D1**: Heizung
- **D2**: Lüftung/Klima
- **D3**: Sanitär
  - D31: Kalt-/Warmwasser
  - D32: Abwasser

### Bauwerk (E/F)
- **E2**: Wände/Stützen
  - E21: Tragende Wände
  - E22: Trennwände
- **E3**: Decken
- **F1**: Fenster/Fenstertüren
- **F2**: Aussentüren
- **F3**: Innentüren

## Token-Optimierung

Das Modul ist für minimalen Token-Verbrauch optimiert:

1. **Haiku Model**: Verwendet `claude-3-5-haiku` (günstigstes Modell)
2. **Kurze Prompts**: Nur essenzielle Informationen
3. **System Prompt Caching**: BKP-Referenz wird gecacht
4. **Batch-Verarbeitung**: Mehrere Elemente in einer Anfrage
5. **Max Tokens**: Limitiert auf 100 (single) / 500 (batch)

**Geschätzte Kosten** (Stand Nov 2024):
- Einzelelement: ~$0.0001 pro Klassifizierung
- Batch (10 Elemente): ~$0.0005 für alle 10

## Integration mit pyRevit

Der BKP_Classifier kann direkt in pyRevit Scripts integriert werden:

```python
# In pyRevit script.py:
import sys
sys.path.append(r'C:/Pfad/zu/TA.BA_DT_PROGR')

from Helpers.BKP_Classifier import BKPClassifier

# Nach CSV-Export:
classifier = BKPClassifier()
# ... klassifizierung ...
```

## Output Format

Jede Klassifizierung liefert:

```python
{
    'bkp_code': 'C13',           # e-BKP-h Code
    'bkp_description': 'Steckdosen',  # Beschreibung
    'confidence': 0.95           # Sicherheit (0-1)
}
```

**Confidence Interpretation**:
- `>= 0.9`: Sehr sicher
- `0.7-0.9`: Sicher
- `0.5-0.7`: Unsicher, prüfen empfohlen
- `< 0.5`: Manuelle Überprüfung erforderlich

## Troubleshooting

**API Key Fehler**:
```
ValueError: ANTHROPIC_API_KEY nicht in .env gefunden
```
→ Prüfe dass `.env` Datei existiert und `ANTHROPIC_API_KEY` gesetzt ist

**Import Fehler**:
```
ModuleNotFoundError: No module named 'anthropic'
```
→ `pip install anthropic python-dotenv`

**JSON Parse Fehler**:
→ Classifier hat Fallback-Logik, sollte automatisch behandelt werden

## Beispiele

Siehe `BKP_Classifier_Example.py` für vollständige Beispiele.

Test der Klassifizierung:
```bash
python Helpers/BKP_Classifier.py
```
