"""
eBKP-H Referenz-Modul
Zentrale Funktionen für das Laden und Verarbeiten der eBKP-H.csv Daten
"""

import pandas as pd
import streamlit as st
import os
import re
from typing import Optional


@st.cache_data
def load_ebkp_catalog(csv_path: str = 'Helpers/eBKP-H.csv') -> pd.DataFrame:
    """
    Lädt den eBKP-H Katalog aus der CSV-Datei.

    Args:
        csv_path: Pfad zur eBKP-H.csv Datei (relativ oder absolut)

    Returns:
        DataFrame mit Spalten: Code, Description, Level
    """
    # Versuche verschiedene Pfade
    possible_paths = [
        csv_path,  # Relativer Pfad
        os.path.join(os.path.dirname(__file__), 'eBKP-H.csv'),  # Relativ zu diesem Modul
        '/Users/orlandobassi/Documents/GitHub/TA.BA_DT_PROGR/Helpers/eBKP-H.csv',  # Absoluter Pfad
    ]

    for path in possible_paths:
        if os.path.exists(path):
            try:
                df = pd.read_csv(path, encoding='utf-8-sig')

                # Validiere Struktur
                required_columns = ['Code', 'Description', 'Level']
                if not all(col in df.columns for col in required_columns):
                    st.warning(f"⚠️ CSV-Datei hat nicht die erwarteten Spalten: {df.columns}")
                    continue

                # Bereinige Daten
                df['Code'] = df['Code'].astype(str).str.strip()
                df['Description'] = df['Description'].astype(str).str.strip()
                df['Level'] = df['Level'].astype(int)

                return df

            except Exception as e:
                st.warning(f"⚠️ Fehler beim Laden von {path}: {e}")
                continue

    # Fallback: Leeres DataFrame mit korrekter Struktur
    st.error("❌ eBKP-H.csv konnte nicht geladen werden!")
    return pd.DataFrame(columns=['Code', 'Description', 'Level'])


def filter_by_levels(df: pd.DataFrame, max_levels: list[int]) -> pd.DataFrame:
    """
    Filtert den Katalog nach erlaubten Levels.

    Args:
        df: eBKP-H DataFrame
        max_levels: Liste der erlaubten Levels (z.B. [1, 2, 3])

    Returns:
        Gefiltertes DataFrame
    """
    if df.empty:
        return df

    return df[df['Level'].isin(max_levels)].copy()


def get_code_description(code: str, df: Optional[pd.DataFrame] = None) -> Optional[str]:
    """
    Gibt die Beschreibung für einen BKP-Code zurück.

    Args:
        code: BKP-Code (z.B. 'C13')
        df: Optional - eBKP-H DataFrame (wird geladen falls nicht angegeben)

    Returns:
        Beschreibung oder None falls Code nicht gefunden
    """
    if df is None:
        df = load_ebkp_catalog()

    if df.empty:
        return None

    code = str(code).strip()
    matches = df[df['Code'] == code]

    if len(matches) > 0:
        return matches.iloc[0]['Description']

    return None


def get_all_codes_by_level(level: int, df: Optional[pd.DataFrame] = None) -> list[str]:
    """
    Gibt alle Codes für ein bestimmtes Level zurück.

    Args:
        level: Level (1-5)
        df: Optional - eBKP-H DataFrame

    Returns:
        Liste von BKP-Codes
    """
    if df is None:
        df = load_ebkp_catalog()

    if df.empty:
        return []

    codes = df[df['Level'] == level]['Code'].tolist()
    return sorted(codes)


def get_hauptgruppen(df: Optional[pd.DataFrame] = None) -> dict[str, str]:
    """
    Gibt die Hauptgruppen (Level 1) zurück.

    Args:
        df: Optional - eBKP-H DataFrame

    Returns:
        Dictionary mit Code -> Beschreibung (z.B. {'C': 'Elektroinstallationen'})
    """
    if df is None:
        df = load_ebkp_catalog()

    if df.empty:
        # Fallback zu bekannten Hauptgruppen
        return {
            'A': 'Grundstück',
            'B': 'Vorbereitungsarbeiten',
            'C': 'Bauwerk - Rohbau',
            'D': 'Bauwerk - Technik',
            'E': 'Bauwerk - Ausbau',
            'F': 'Umgebung',
            'G': 'Baunebenkosten'
        }

    hauptgruppen = df[df['Level'] == 1]
    return dict(zip(hauptgruppen['Code'], hauptgruppen['Description']))


def validate_bkp_code(code: str, df: Optional[pd.DataFrame] = None) -> dict:
    """
    Validiert einen BKP-Code.

    Args:
        code: BKP-Code zum Validieren
        df: Optional - eBKP-H DataFrame

    Returns:
        Dictionary mit:
        - 'valid': bool - Ist der Code gültig?
        - 'message': str - Beschreibung oder Fehlermeldung
        - 'known_code': bool - Ist der Code im Katalog?
    """
    if not code or pd.isna(code):
        return {'valid': False, 'message': 'Leer', 'known_code': False}

    code = str(code).strip().upper()

    # Lade Katalog falls nicht angegeben
    if df is None:
        df = load_ebkp_catalog()

    # Prüfe ob Code im Katalog ist
    if not df.empty:
        matches = df[df['Code'] == code]
        if len(matches) > 0:
            description = matches.iloc[0]['Description']
            return {'valid': True, 'message': description, 'known_code': True}

    # Code nicht im Katalog - prüfe Format
    # Muss mit A-G beginnen
    if not re.match(r'^[A-G]', code):
        return {'valid': False, 'message': 'Muss mit A-G beginnen', 'known_code': False}

    # Format OK, aber nicht im Katalog
    return {'valid': True, 'message': 'Format OK, Code nicht im Katalog', 'known_code': False}


def get_codes_for_dropdown(df: Optional[pd.DataFrame] = None, max_levels: Optional[list[int]] = None) -> list[tuple[str, str]]:
    """
    Gibt eine Liste von (Code, "Code - Description") Tupeln für Dropdowns zurück.

    Args:
        df: Optional - eBKP-H DataFrame
        max_levels: Optional - Filtere nach Levels

    Returns:
        Liste von (code, label) Tupeln
    """
    if df is None:
        df = load_ebkp_catalog()

    if df.empty:
        return []

    # Filtere nach Levels falls angegeben
    if max_levels is not None:
        df = filter_by_levels(df, max_levels)

    # Erstelle Labels
    codes_with_labels = []
    for _, row in df.iterrows():
        code = row['Code']
        description = row['Description']
        label = f"{code} - {description}"
        codes_with_labels.append((code, label))

    return sorted(codes_with_labels, key=lambda x: x[0])
