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
        # Fallback zu bekannten Hauptgruppen (inkl. Zuschläge)
        return {
            'A': 'Grundstück',
            'B': 'Vorbereitungsarbeiten',
            'C': 'Bauwerk - Rohbau',
            'D': 'Bauwerk - Technik',
            'E': 'Bauwerk - Ausbau',
            'F': 'Umgebung',
            'G': 'Baunebenkosten',
            'H': 'Kunstbauten / Spezialbauten',
            'I': 'Verkehrsanlagen',
            'J': 'Wald- und Landwirtschaft',
            'V': 'Provisionen / Versicherungen',
            'W': 'Wertanpassung',
            'Y': 'Ausschreibung',
            'Z': 'Zusätzliche Kosten / Reserve'
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
    # Muss mit A-J, V, W, Y oder Z beginnen (alle eBKP-H Hauptgruppen)
    if not re.match(r'^[A-JVWYZ]', code):
        return {'valid': False, 'message': 'Muss mit A-J, V, W, Y oder Z beginnen', 'known_code': False}

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


# ============================================================================
# eBKP-H KOSTENHIERARCHIE nach SIA 102
# ============================================================================

# Hauptgruppen mit vollständiger Beschreibung
EBKP_MAIN_GROUPS = {
    'A': 'Grundstück',
    'B': 'Vorbereitungsarbeiten',
    'C': 'Bauwerk - Rohbau',
    'D': 'Bauwerk - Technik',
    'E': 'Bauwerk - Ausbau',
    'F': 'Umgebung',
    'G': 'Baunebenkosten',
    'H': 'Kunstbauten / Spezialbauten',
    'I': 'Verkehrsanlagen',
    'J': 'Wald- und Landwirtschaft',
    'V': 'Provisionen / Versicherungen',
    'W': 'Wertanpassung',
    'Y': 'Ausschreibung',
    'Z': 'Zusätzliche Kosten / Reserve'
}

# Kostenhierarchie für die Berechnung
EBKP_COST_HIERARCHY = {
    # Bauwerkskosten = C + D + E + F + G
    'bauwerkskosten': ['C', 'D', 'E', 'F', 'G'],
    # Erstellungskosten Basis = B + Bauwerkskosten + H + I + J
    'erstellungskosten_basis': ['B', 'H', 'I', 'J'],
    # Erstellungskosten Zuschläge (prozentual auf Basis)
    'erstellungskosten_zuschlaege': ['V', 'W'],
    # Anlagekosten Basis = A
    'anlagekosten_basis': ['A'],
    # Anlagekosten Zuschläge (prozentual auf Erstellungskosten)
    'anlagekosten_zuschlaege': ['Y', 'Z']
}

# Beschreibungen für die Kostenhierarchie
EBKP_COST_LABELS = {
    'bauwerkskosten': 'Bauwerkskosten (C-G)',
    'erstellungskosten': 'Erstellungskosten (B-J, V, W)',
    'anlagekosten': 'Anlagekosten (Total)'
}


# ============================================================================
# HIERARCHISCHER KENNWERT-LOOKUP
# ============================================================================

def _build_kennwert_result(row: 'pd.Series', cost_col: str, level: str) -> dict:
    """
    Helper: Baut Result-Dict aus DataFrame-Zeile.

    Args:
        row: Zeile aus Kennwerte-DataFrame
        cost_col: Spaltenname für Kostenfeld (tief/mittel/hoch)
        level: Match-Level ('exact', 'subgroup', 'hauptgruppe')

    Returns:
        Dict mit code, description, unit, value, level_matched, anmerkungen
    """
    value = row.get(cost_col, 0)
    if pd.isna(value) or value == '':
        value = 0.0
    else:
        try:
            value = float(value)
        except (ValueError, TypeError):
            value = 0.0

    return {
        'code': row.get('eBKP-H Code', ''),
        'description': row.get('Kostengruppe / Position', ''),
        'unit': row.get('Kennwert Einheit', ''),
        'value': value,
        'level_matched': level,
        'anmerkungen': row.get('Anmerkungen', '')
    }


def get_kennwert_hierarchical(
    bkp_code: str,
    kennwerte_df: 'pd.DataFrame',
    cost_level: str = 'mittel'
) -> Optional[dict]:
    """
    Hierarchischer Lookup für Kostenkennwerte.

    Lookup-Reihenfolge:
    1. Exakter Match (z.B. E02.02)
    2. Übergeordnete Untergruppe (z.B. E02 von E02.02)
    3. Hauptgruppe (z.B. E von E02 oder E02.02)

    Args:
        bkp_code: eBKP-H Code zum Nachschlagen (z.B. 'E02.02', 'D01.05')
        kennwerte_df: DataFrame aus 'eBKP-H Kostenplan mit Kennwerten.csv'
        cost_level: 'tief', 'mittel', oder 'hoch'

    Returns:
        Dict mit:
        - 'code': Gefundener Code
        - 'description': Kostengruppe / Position
        - 'unit': Kennwert Einheit
        - 'value': CHF/Einheit für gewählte Stufe
        - 'level_matched': 'exact', 'subgroup', oder 'hauptgruppe'
        - 'anmerkungen': Anmerkungen (optional)

        None falls kein Match auf irgendeiner Ebene gefunden.
    """
    if not bkp_code or pd.isna(bkp_code):
        return None

    code = str(bkp_code).strip().upper()

    # Mapping für Kostenspalten
    cost_col_map = {
        'tief': 'Kennwert tief CHF/Einheit',
        'mittel': 'Kennwert mittel CHF/Einheit',
        'hoch': 'Kennwert hoch CHF/Einheit'
    }
    cost_col = cost_col_map.get(cost_level, cost_col_map['mittel'])

    # Level 1: Exakter Match (z.B. E02.02)
    match = kennwerte_df[kennwerte_df['eBKP-H Code'] == code]
    if not match.empty:
        return _build_kennwert_result(match.iloc[0], cost_col, 'exact')

    # Level 2: Untergruppe Match (z.B. E02 von E02.02)
    if '.' in code:
        subgroup = code.split('.')[0]
        match = kennwerte_df[kennwerte_df['eBKP-H Code'] == subgroup]
        if not match.empty:
            return _build_kennwert_result(match.iloc[0], cost_col, 'subgroup')

    # Level 3: Hauptgruppe (z.B. E von E02 oder E02.02)
    hauptgruppe = code[0] if code else None
    if hauptgruppe:
        match = kennwerte_df[kennwerte_df['eBKP-H Code'] == hauptgruppe]
        if not match.empty:
            return _build_kennwert_result(match.iloc[0], cost_col, 'hauptgruppe')

    return None


def parse_unit_type(unit_string: str) -> dict:
    """
    Analysiert die 'Kennwert Einheit' Spalte um die Berechnungsmethode zu bestimmen.

    Args:
        unit_string: Einheiten-String aus der CSV (z.B. 'm² Grundfläche', '% der Kosten')

    Returns:
        Dict mit:
        - 'type': 'area', 'linear', 'percentage', 'lump_sum', 'piece', 'technical', 'unknown'
        - 'base_unit': Original Einheiten-String
        - 'multiplier_field': Welches Eingabefeld für Berechnung zu verwenden ist
        - 'percentage_base': Für Prozent-Typen, worauf sie basieren
    """
    if not unit_string or pd.isna(unit_string):
        return {'type': 'unknown', 'base_unit': '', 'multiplier_field': None}

    unit = str(unit_string).lower().strip()

    # Flächenbasierte Einheiten
    if 'm²' in unit or 'm2' in unit:
        subtypes = {
            'grundfläche': 'floor_area',
            'fassadenfläche': 'facade_area',
            'wandfläche': 'wall_area',
            'dachfläche': 'roof_area',
            'geschossfläche': 'storey_area',
            'böschungsfläche': 'slope_area',
            'baustelle': 'site_area',
            'nutzfläche': 'usable_area',
            'heizfläche': 'heating_area',
            'lauffläche': 'walking_area',
            'treppenfläche': 'stair_area',
            'fläche': 'generic_area'
        }
        for key, field in subtypes.items():
            if key in unit:
                return {'type': 'area', 'base_unit': unit, 'multiplier_field': field}
        return {'type': 'area', 'base_unit': unit, 'multiplier_field': 'generic_area'}

    # Lineare Einheiten
    if 'm laufmeter' in unit or 'längenmass' in unit or 'm perimeter' in unit or 'm pfahllänge' in unit:
        return {'type': 'linear', 'base_unit': unit, 'multiplier_field': 'length'}

    # Prozentbasierte Einheiten
    if '%' in unit:
        if 'erstellungskosten' in unit:
            return {'type': 'percentage', 'base_unit': unit, 'percentage_base': 'erstellungskosten'}
        elif 'gesamtbaukosten' in unit or 'baukosten' in unit:
            return {'type': 'percentage', 'base_unit': unit, 'percentage_base': 'baukosten'}
        elif 'umgebungskosten' in unit:
            return {'type': 'percentage', 'base_unit': unit, 'percentage_base': 'umgebungskosten'}
        elif 'grundstückkosten' in unit or 'grundstück' in unit:
            return {'type': 'percentage', 'base_unit': unit, 'percentage_base': 'grundstueck'}
        elif 'kaufpreis' in unit or 'verkaufspreis' in unit or 'erlös' in unit:
            return {'type': 'percentage', 'base_unit': unit, 'percentage_base': 'verkaufspreis'}
        elif 'betriebskosten' in unit or 'betriebserlös' in unit:
            return {'type': 'percentage', 'base_unit': unit, 'percentage_base': 'betriebskosten'}
        elif 'c-kosten' in unit:
            return {'type': 'percentage', 'base_unit': unit, 'percentage_base': 'c_kosten'}
        elif 'kosten a01' in unit:
            return {'type': 'percentage', 'base_unit': unit, 'percentage_base': 'a01_kosten'}
        elif 'kosten' in unit:
            return {'type': 'percentage', 'base_unit': unit, 'percentage_base': 'referenz_kosten'}
        elif 'pro jahr' in unit:
            return {'type': 'percentage_yearly', 'base_unit': unit, 'percentage_base': 'yearly'}
        return {'type': 'percentage', 'base_unit': unit, 'percentage_base': 'total'}

    # Pauschal
    if 'pauschal' in unit:
        return {'type': 'lump_sum', 'base_unit': unit, 'multiplier_field': 'count'}

    # Stück/Punkte
    if 'stück' in unit or 'punkte' in unit:
        return {'type': 'piece', 'base_unit': unit, 'multiplier_field': 'count'}

    # Technische Einheiten
    if 'kw' in unit and 'kwh' not in unit:
        return {'type': 'technical', 'base_unit': unit, 'multiplier_field': 'kw'}
    if 'kwh' in unit:
        return {'type': 'technical', 'base_unit': unit, 'multiplier_field': 'kwh'}
    if 'liter' in unit:
        return {'type': 'technical', 'base_unit': unit, 'multiplier_field': 'liter'}
    if 'm³' in unit or 'm3' in unit:
        return {'type': 'technical', 'base_unit': unit, 'multiplier_field': 'm3'}
    if 'm³/tag' in unit:
        return {'type': 'technical', 'base_unit': unit, 'multiplier_field': 'm3_day'}
    if 'm²/h' in unit or 'm³/h' in unit:
        return {'type': 'technical', 'base_unit': unit, 'multiplier_field': 'flow_rate'}

    return {'type': 'unknown', 'base_unit': unit, 'multiplier_field': None}
