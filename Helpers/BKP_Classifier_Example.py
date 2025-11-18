"""
Beispiel: BKP Klassifizierung für Revit CSV-Export

Zeigt wie man den BKP_Classifier mit pyRevit-CSV-Daten verwendet.
"""

import pandas as pd
from BKP_Classifier import BKPClassifier


def classify_csv_export(csv_path: str, output_path: str):
    """
    Liest einen pyRevit CSV-Export und fügt BKP-Klassifizierung hinzu.

    Args:
        csv_path: Pfad zur Input-CSV (aus pyRevit Export)
        output_path: Pfad für Output-CSV mit BKP-Codes
    """
    # CSV einlesen
    df = pd.read_csv(csv_path, sep=';', encoding='utf-8-sig')

    print(f"Verarbeite {len(df)} Elemente...")

    # Classifier initialisieren
    classifier = BKPClassifier()

    # Batch-Verarbeitung für Effizienz (max 10 Elemente pro Batch)
    batch_size = 10
    all_results = []

    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size]

        # Batch-Elemente vorbereiten
        batch_elements = []
        for _, row in batch.iterrows():
            element = {
                'type': row.get('Kategorie', '') or row.get('ifcType', ''),
                'category': row.get('Kategorie', ''),
                'family': row.get('Family', '') or row.get('Typ', ''),
            }
            batch_elements.append(element)

        # Klassifizieren
        results = classifier.classify_batch(batch_elements)
        all_results.extend(results)

        print(f"  Batch {i//batch_size + 1}/{(len(df)-1)//batch_size + 1} fertig")

    # Ergebnisse zum DataFrame hinzufügen
    df['BKP_Code'] = [r['bkp_code'] for r in all_results]
    df['BKP_Beschreibung'] = [r['bkp_description'] for r in all_results]
    df['BKP_Confidence'] = [r['confidence'] for r in all_results]

    # Speichern
    df.to_csv(output_path, sep=';', index=False, encoding='utf-8-sig')
    print(f"\nGespeichert: {output_path}")

    # Statistik ausgeben
    print(f"\nKlassifizierung abgeschlossen:")
    print(f"  Durchschnittliche Confidence: {df['BKP_Confidence'].mean():.1%}")
    print(f"  Eindeutige BKP-Codes: {df['BKP_Code'].nunique()}")
    print(f"\nTop 5 BKP-Codes:")
    print(df['BKP_Code'].value_counts().head())


def classify_single_elements():
    """Beispiel für Einzelklassifizierung."""
    classifier = BKPClassifier()

    # Beispiel: Elektrische Elemente
    elements = [
        {
            'type': 'Steckdose T13',
            'category': 'Electrical Fixtures',
            'info': 'Standard Wandsteckdose'
        },
        {
            'type': 'LED Panel',
            'category': 'Lighting Fixtures',
            'family': 'LED Deckenleuchte 60x60'
        },
        {
            'type': 'Brandmelder',
            'category': 'Security Devices',
        },
        {
            'type': 'Netzwerkdose CAT6',
            'category': 'Communication Outlets',
        }
    ]

    print("=== Einzelklassifizierung ===\n")
    for elem in elements:
        result = classifier.classify_element(
            elem['type'],
            category=elem.get('category'),
            family=elem.get('family'),
            additional_info=elem.get('info')
        )

        print(f"Element: {elem['type']}")
        print(f"  BKP Code:   {result['bkp_code']}")
        print(f"  Confidence: {result['confidence']:.0%}")
        print(f"  Beschreibung: {result['bkp_description']}")
        print()


def add_bkp_to_existing_csv(csv_path: str):
    """
    Fügt BKP-Klassifizierung zu einer existierenden CSV hinzu (In-Place).
    Überspringt bereits klassifizierte Zeilen.
    """
    df = pd.read_csv(csv_path, sep=';', encoding='utf-8-sig')

    # Prüfe ob BKP_Code Spalte existiert
    if 'BKP_Code' not in df.columns:
        df['BKP_Code'] = None
        df['BKP_Confidence'] = None
        df['BKP_Beschreibung'] = None

    # Nur nicht-klassifizierte Elemente verarbeiten
    to_classify = df[df['BKP_Code'].isna()]

    if len(to_classify) == 0:
        print("Alle Elemente bereits klassifiziert!")
        return

    print(f"Klassifiziere {len(to_classify)} von {len(df)} Elementen...")

    classifier = BKPClassifier()

    for idx, row in to_classify.iterrows():
        result = classifier.classify_element(
            row.get('Kategorie', '') or row.get('ifcType', ''),
            category=row.get('Kategorie'),
            family=row.get('Family') or row.get('Typ')
        )

        df.at[idx, 'BKP_Code'] = result['bkp_code']
        df.at[idx, 'BKP_Confidence'] = result['confidence']
        df.at[idx, 'BKP_Beschreibung'] = result['bkp_description']

    # Speichern
    df.to_csv(csv_path, sep=';', index=False, encoding='utf-8-sig')
    print(f"Aktualisiert: {csv_path}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # CSV-Datei als Argument übergeben
        input_csv = sys.argv[1]
        output_csv = input_csv.replace('.csv', '_mit_BKP.csv')

        classify_csv_export(input_csv, output_csv)
    else:
        # Demo-Modus
        print("Demo: Einzelklassifizierung\n")
        classify_single_elements()

        print("\n" + "="*50)
        print("Verwendung mit CSV:")
        print("  python BKP_Classifier_Example.py <input.csv>")
        print("\nOder direkt in Python:")
        print("  from BKP_Classifier_Example import classify_csv_export")
        print("  classify_csv_export('export.csv', 'export_mit_bkp.csv')")
