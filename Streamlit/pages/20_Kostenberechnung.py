"""
Kostenberechnung basierend auf eBKP-H Klassifizierung und Kennwerten

Berechnet Kosten mit hierarchischem Lookup:
1. Exakter Match (z.B. E02.02)
2. Untergruppe (z.B. E02)
3. Hauptgruppe (z.B. E)

Kostengruppen:
- Bauwerkskosten: C + D + E + F + G
- Erstellungskosten: B + Bauwerkskosten + H + I + J + V + W
- Anlagekosten: A + Erstellungskosten + Y + Z
"""

from __future__ import annotations
import streamlit as st
import pandas as pd
import sys
import os
from pathlib import Path
from typing import Tuple, List, Dict, Optional, Any
from dataclasses import asdict
from datetime import datetime
from io import BytesIO

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate,
        Table,
        TableStyle,
        Paragraph,
        Spacer,
        PageBreak,
        KeepTogether,
        Image,
    )
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Pfad zum Logo
LOGO_PATH = Path(__file__).parent.parent / 'Logo_dunkel.png'

# Füge Parent-Verzeichnis zum Path hinzu für Imports
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Füge helpers_shared zum Path hinzu
helpers_shared_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'helpers_shared'))
if helpers_shared_dir not in sys.path:
    sys.path.insert(0, helpers_shared_dir)

try:
    from helpers.sidebar_navigation import render_sidebar, render_page_header, render_divider, render_page_footer
    from helpers.notifications import toast, NotificationType
    from helpers.session_state import (
        init_session_state,
        get_state,
        set_state,
        DATA_CLASSIFICATION_RESULTS,
        CFG_COST_ESTIMATION_CONFIG,
        DATA_PROJEKT_DATEN,
        DATA_CUSTOM_KENNWERTE,
        CFG_USE_CUSTOM_KENNWERTE,
        has_classification_results
    )
except ImportError as e:
    st.error(f"Module konnten nicht importiert werden: {e}")
    st.stop()

try:
    from ebkp_reference import (
        get_kennwert_hierarchical,
        parse_unit_type,
        EBKP_MAIN_GROUPS
    )
except ImportError as e:
    st.error(f"ebkp_reference konnte nicht importiert werden: {e}")
    st.stop()

# ============================================================================
# PDF STYLING KONSTANTEN
# ============================================================================

# Farbschema für das PDF-Layout (professionell)
COLOR_PRIMARY_HEADER = "#1f4788"     # Dunkles Blau für Haupttitel
COLOR_SECONDARY_HEADER = "#366092"   # Mittleres Blau für Tabellenkopf
COLOR_ACCENT = "#d4e6f1"             # Helles Blau für Hervorhebungen
COLOR_BACKGROUND_ALT = "#f9f9f9"     # Sehr helles Grau für Zeilenalternation
COLOR_TEXT_DARK = "#1a1a1a"          # Dunkles Grau für Text
COLOR_TEXT_LIGHT = "#666666"         # Mittleres Grau für Zusatztext

# Abstände für PDF (in cm)
MARGIN_TOP = 1.5
MARGIN_BOTTOM = 1.5
MARGIN_LEFT = 1.5
MARGIN_RIGHT = 1.5
SPACING_SECTION = 0.8
SPACING_SUBSECTION = 0.3

# Seiten-Konfiguration
st.set_page_config(
    page_title="Kostenberechnung",
    page_icon="💰",
    layout="wide"
)

# Initialize Session State
init_session_state()

# Render gemeinsame Sidebar
render_sidebar()

# ============================================================================
# HILFSFUNKTIONEN
# ============================================================================

def format_currency(value: float) -> str:
    """Formatiert Betrag als Schweizer Franken."""
    if pd.isna(value):
        return "0.00 CHF"
    return f"{value:,.2f} CHF".replace(',', "'")


def format_tolerance(tolerance: int) -> str:
    """Formatiert Toleranz als Prozentangabe."""
    return f"± {tolerance}%"


def calculate_cost_with_tolerance(betrag: float, tolerance: int) -> Tuple[float, float]:
    """Berechnet Min/Max basierend auf Toleranz."""
    if tolerance == 0:
        return betrag, betrag
    tolerance_amount = betrag * (tolerance / 100)
    return betrag - tolerance_amount, betrag + tolerance_amount


@st.cache_data
def load_kennwerte_from_file() -> pd.DataFrame:
    """Lädt die Kennwerte CSV aus dem Standardverzeichnis."""
    csv_path = Path(__file__).parent.parent / 'eBKP-H Kostenplan mit Kennwerten.csv'

    if not csv_path.exists():
        st.error(f"Kennwerte-Datei nicht gefunden: {csv_path}")
        return pd.DataFrame()

    try:
        df = pd.read_csv(csv_path, sep=';', encoding='utf-8-sig')
        # Filtere leere Zeilen
        df = df[df['eBKP-H Code'].notna() & (df['eBKP-H Code'] != '')]
        return df
    except Exception as e:
        st.error(f"Fehler beim Laden der Kennwerte: {e}")
        return pd.DataFrame()


# Erwartete Spalten für Kennwerte CSV
KENNWERTE_REQUIRED_COLUMNS = ['eBKP-H Code', 'Kennwert Einheit']
KENNWERTE_COST_COLUMNS = ['Kennwert tief CHF/Einheit', 'Kennwert mittel CHF/Einheit', 'Kennwert hoch CHF/Einheit']
KENNWERTE_OPTIONAL_COLUMNS = ['Kostengruppe / Position', 'Anmerkungen']


def validate_kennwerte_csv(df: pd.DataFrame) -> Tuple[bool, str, pd.DataFrame]:
    """
    Validiert eine benutzerdefinierte Kennwerte-CSV.

    Args:
        df: DataFrame aus hochgeladener CSV

    Returns:
        Tuple aus (ist_valid, fehlermeldung, normalisierter_df)
    """
    if df.empty:
        return False, "CSV ist leer", df

    # Prüfe erforderliche Spalten
    missing_required = [col for col in KENNWERTE_REQUIRED_COLUMNS if col not in df.columns]
    if missing_required:
        return False, f"Fehlende Pflichtspalten: {', '.join(missing_required)}", df

    # Prüfe Kostenspalten (mindestens eine muss vorhanden sein)
    available_cost_cols = [col for col in KENNWERTE_COST_COLUMNS if col in df.columns]
    if not available_cost_cols:
        return False, f"Mindestens eine Kostenspalte erforderlich: {', '.join(KENNWERTE_COST_COLUMNS)}", df

    # Normalisiere DataFrame
    df_normalized = df.copy()

    # Filtere leere Zeilen
    df_normalized = df_normalized[df_normalized['eBKP-H Code'].notna() & (df_normalized['eBKP-H Code'] != '')]

    # Füge fehlende Kostenspalten mit 0 hinzu
    for col in KENNWERTE_COST_COLUMNS:
        if col not in df_normalized.columns:
            df_normalized[col] = 0.0

    # Füge fehlende optionale Spalten hinzu
    for col in KENNWERTE_OPTIONAL_COLUMNS:
        if col not in df_normalized.columns:
            df_normalized[col] = ''

    # Konvertiere Kostenspalten zu numerisch
    for col in KENNWERTE_COST_COLUMNS:
        df_normalized[col] = pd.to_numeric(df_normalized[col], errors='coerce').fillna(0.0)

    return True, f"✅ {len(df_normalized)} Kennwerte-Einträge validiert", df_normalized


def render_kennwerte_section(default_kennwerte_df: pd.DataFrame) -> pd.DataFrame:
    """
    Rendert den Kennwerte-Verwaltungsbereich.

    Args:
        default_kennwerte_df: Standard-Kennwerte aus der Datei

    Returns:
        DataFrame mit den zu verwendenden Kennwerten
    """
    st.subheader("📊 Kennwerte-Katalog")

    # Aktuellen Status prüfen
    use_custom = get_state(CFG_USE_CUSTOM_KENNWERTE, False)
    custom_kennwerte = get_state(DATA_CUSTOM_KENNWERTE)

    # Tabs für Standard vs. Eigene Kennwerte
    tab_default, tab_custom = st.tabs([
        "📋 Standard-Kennwerte",
        "📤 Eigene Kennwerte importieren"
    ])

    with tab_default:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"📚 {len(default_kennwerte_df)} Standard-Kennwerte aus eBKP-H Katalog")
        with col2:
            if use_custom and custom_kennwerte is not None:
                if st.button("🔄 Standard verwenden", help="Zurück zu Standard-Kennwerten"):
                    set_state(CFG_USE_CUSTOM_KENNWERTE, False)
                    set_state('cost_results_df', None)
                    set_state('cost_summaries', None)
                    st.rerun()

        with st.expander("Standard-Kennwerte anzeigen", expanded=False):
            # Zeige Filteroptionen
            hauptgruppen = sorted(default_kennwerte_df['eBKP-H Code'].apply(
                lambda x: str(x)[0] if pd.notna(x) and x else ''
            ).unique())
            hauptgruppen = [h for h in hauptgruppen if h]

            selected_hg = st.multiselect(
                "Nach Hauptgruppe filtern",
                options=hauptgruppen,
                default=[],
                key='filter_default_hg'
            )

            if selected_hg:
                filtered_df = default_kennwerte_df[default_kennwerte_df['eBKP-H Code'].apply(
                    lambda x: str(x)[0] in selected_hg if pd.notna(x) and x else False
                )]
            else:
                filtered_df = default_kennwerte_df

            st.dataframe(
                filtered_df[['eBKP-H Code', 'Kostengruppe / Position', 'Kennwert Einheit',
                            'Kennwert tief CHF/Einheit', 'Kennwert mittel CHF/Einheit',
                            'Kennwert hoch CHF/Einheit']],
                hide_index=True,
                height=300
            )

    with tab_custom:
        st.markdown("""
        **Eigene Kennwerte verwenden:**

        Laden Sie Ihre büro-spezifischen Kennwerte hoch. Die CSV muss folgende Spalten enthalten:

        | Spalte | Erforderlich | Beschreibung |
        |--------|--------------|--------------|
        | `eBKP-H Code` | ✅ | z.B. C02.01, D01, E |
        | `Kennwert Einheit` | ✅ | z.B. m² Fläche, Stück, % |
        | `Kennwert tief CHF/Einheit` | ⚡ | Minimum-Kosten |
        | `Kennwert mittel CHF/Einheit` | ⚡ | Durchschnitts-Kosten |
        | `Kennwert hoch CHF/Einheit` | ⚡ | Maximum-Kosten |
        | `Kostengruppe / Position` | ❌ | Beschreibung (optional) |

        ⚡ = Mindestens eine Kostenspalte erforderlich
        """)

        # Download Template Button
        col1, col2 = st.columns(2)

        with col1:
            # Download komplette Standard-Kennwerte
            full_csv = default_kennwerte_df.to_csv(index=False, sep=';', encoding='utf-8')
            st.download_button(
                "📥 Standard-Kennwerte herunterladen",
                data=full_csv,
                file_name="eBKP-H_Kennwerte_Standard.csv",
                mime="text/csv",
                help="Kompletter Standard-Katalog als Basis"
            )

        # Upload eigene Kennwerte
        uploaded_kennwerte = st.file_uploader(
            "Eigene Kennwerte-CSV hochladen",
            type=['csv'],
            help="CSV mit Ihren büro-spezifischen Kennwerten",
            key='kennwerte_uploader'
        )

        if uploaded_kennwerte:
            try:
                # Versuche verschiedene Trennzeichen
                content = uploaded_kennwerte.getvalue().decode('utf-8-sig')
                sep = ';' if ';' in content[:1000] else ','

                uploaded_kennwerte.seek(0)
                df_upload = pd.read_csv(uploaded_kennwerte, sep=sep, encoding='utf-8-sig')

                # Validiere
                is_valid, message, df_normalized = validate_kennwerte_csv(df_upload)

                if is_valid:
                    st.success(message)

                    with st.expander("Vorschau der importierten Kennwerte", expanded=True):
                        st.dataframe(
                            df_normalized[['eBKP-H Code', 'Kostengruppe / Position', 'Kennwert Einheit',
                                          'Kennwert tief CHF/Einheit', 'Kennwert mittel CHF/Einheit',
                                          'Kennwert hoch CHF/Einheit']].head(20),
                            hide_index=True
                        )

                    # Vergleich mit Standard
                    custom_codes = set(df_normalized['eBKP-H Code'].unique())
                    default_codes = set(default_kennwerte_df['eBKP-H Code'].unique())
                    overlap = custom_codes & default_codes
                    new_codes = custom_codes - default_codes

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Eigene Einträge", len(custom_codes))
                    with col2:
                        st.metric("Überschrieben", len(overlap), help="Codes die Standard-Kennwerte ersetzen")
                    with col3:
                        st.metric("Neue Codes", len(new_codes), help="Codes die nicht im Standard sind")

                    # Aktivieren Button
                    if st.button("✅ Eigene Kennwerte aktivieren", type="primary"):
                        set_state(DATA_CUSTOM_KENNWERTE, df_normalized)
                        set_state(CFG_USE_CUSTOM_KENNWERTE, True)
                        set_state('cost_results_df', None)
                        set_state('cost_summaries', None)
                        st.success("✅ Eigene Kennwerte aktiviert!")
                        st.rerun()
                else:
                    st.error(message)
                    st.info(f"Gefundene Spalten: {list(df_upload.columns)}")

            except Exception as e:
                st.error(f"❌ Fehler beim Laden: {e}")

        # Zeige aktive eigene Kennwerte
        if use_custom and custom_kennwerte is not None:
            st.divider()
            st.success(f"🟢 **Eigene Kennwerte aktiv** ({len(custom_kennwerte)} Einträge)")

            with st.expander("Aktive eigene Kennwerte anzeigen"):
                st.dataframe(
                    custom_kennwerte[['eBKP-H Code', 'Kostengruppe / Position', 'Kennwert Einheit',
                                     'Kennwert tief CHF/Einheit', 'Kennwert mittel CHF/Einheit',
                                     'Kennwert hoch CHF/Einheit']],
                    hide_index=True,
                    height=300
                )

            if st.button("🗑️ Eigene Kennwerte löschen", type="secondary"):
                set_state(DATA_CUSTOM_KENNWERTE, None)
                set_state(CFG_USE_CUSTOM_KENNWERTE, False)
                set_state('cost_results_df', None)
                set_state('cost_summaries', None)
                st.rerun()

    # Rückgabe der aktiven Kennwerte
    if use_custom and custom_kennwerte is not None:
        return custom_kennwerte
    return default_kennwerte_df


# ============================================================================
# KOSTENBERECHNUNG ENGINE
# ============================================================================

def calculate_element_cost(
    bkp_code: str,
    quantity: float,
    kennwerte_df: pd.DataFrame,
    cost_level: str = 'mittel',
    reference_costs: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Berechnet Kosten für ein einzelnes Element mit hierarchischem Lookup.

    Args:
        bkp_code: eBKP-H Code
        quantity: Menge (Fläche, Länge, Stück, etc.)
        kennwerte_df: Kennwerte-Referenz DataFrame
        cost_level: 'tief', 'mittel', 'hoch'
        reference_costs: Dict mit Basiskosten für Prozent-Berechnungen

    Returns:
        Dict mit cost, unit_cost, unit, matched_code, match_level, calculation_type
    """
    kennwert = get_kennwert_hierarchical(bkp_code, kennwerte_df, cost_level)

    if kennwert is None:
        return {
            'cost': 0.0,
            'unit_cost': 0.0,
            'unit': 'N/A',
            'matched_code': None,
            'match_level': 'none',
            'calculation_type': 'no_match',
            'description': ''
        }

    unit_info = parse_unit_type(kennwert['unit'])
    unit_cost = kennwert['value']

    if unit_info['type'] == 'percentage' or unit_info['type'] == 'percentage_yearly':
        # Berechnung basierend auf Referenzkosten
        base = 0.0
        if reference_costs:
            percentage_base = unit_info.get('percentage_base', 'total')
            base = reference_costs.get(percentage_base, reference_costs.get('total', 0))
        cost = base * (unit_cost / 100) * max(1, quantity)
        calc_type = f"percentage_{unit_info.get('percentage_base', 'total')}"
    elif unit_info['type'] == 'lump_sum':
        # Pauschal: Einheitspreis mal Anzahl (meist 1)
        cost = unit_cost * max(1, quantity)
        calc_type = 'lump_sum'
    else:
        # Standard: Menge mal Einheitspreis
        cost = quantity * unit_cost
        calc_type = unit_info['type']

    return {
        'cost': cost,
        'unit_cost': unit_cost,
        'unit': kennwert['unit'],
        'matched_code': kennwert['code'],
        'match_level': kennwert['level_matched'],
        'calculation_type': calc_type,
        'description': kennwert['description']
    }


def calculate_cost_hierarchy_sum(df: pd.DataFrame, groups: List[str]) -> float:
    """
    Berechnet Summe der Kosten für bestimmte Hauptgruppen.

    Args:
        df: DataFrame mit 'BKP_Code' und 'Einzelkosten' Spalten
        groups: Liste der Hauptgruppen (z.B. ['C', 'D', 'E', 'F', 'G'])

    Returns:
        Summe der Kosten für Elemente in den angegebenen Gruppen
    """
    if df.empty or 'Einzelkosten' not in df.columns:
        return 0.0

    mask = df['BKP_Code'].apply(
        lambda x: str(x)[0].upper() in groups if pd.notna(x) and x else False
    )
    return df.loc[mask, 'Einzelkosten'].sum()


def calculate_all_costs(
    df: pd.DataFrame,
    kennwerte_df: pd.DataFrame,
    cost_level: str = 'mittel',
    quantity_column: str = 'Menge',
    project_areas: Optional[Dict[str, float]] = None
) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """
    Berechnet Kosten für alle Elemente im DataFrame.

    Zwei-Pass-Berechnung:
    1. Pass: Direkte Kosten (nicht-prozentual)
    2. Pass: Prozentuale Kosten basierend auf Pass-1-Summen

    Args:
        df: DataFrame mit BKP_Code und optional Mengen
        kennwerte_df: Kennwerte-Referenz DataFrame
        cost_level: 'tief', 'mittel', 'hoch'
        quantity_column: Name der Mengenspalte
        project_areas: Globale Projektflächen falls keine Mengen vorhanden

    Returns:
        Tuple aus:
        - DataFrame mit zusätzlichen Kostenspalten
        - Dict mit Kostenzusammenfassungen nach Hierarchie
    """
    df = df.copy()

    # Initialisiere Kostenspalten
    df['Einzelkosten'] = 0.0
    df['Berechnungsart'] = ''
    df['Matched_Code'] = ''
    df['Match_Level'] = ''
    df['Einheit_Kennwert'] = ''

    # Stelle sicher dass Mengenspalte existiert
    if quantity_column not in df.columns:
        df[quantity_column] = 1.0
        # Verwende project_areas falls vorhanden
        if project_areas:
            default_area = project_areas.get('geschossflaeche', 1.0)
            df[quantity_column] = default_area

    # Listen für Pass 2 (prozentuale Kosten)
    percentage_rows = []

    # === PASS 1: Nicht-prozentuale Kosten ===
    for idx, row in df.iterrows():
        bkp_code = row.get('BKP_Code', '')
        if not bkp_code or pd.isna(bkp_code):
            continue

        # Bestimme Menge
        quantity = row.get(quantity_column, 1.0)
        if pd.isna(quantity) or quantity == 0:
            quantity = 1.0

        # Hole Kennwert
        kennwert = get_kennwert_hierarchical(bkp_code, kennwerte_df, cost_level)

        if kennwert is None:
            df.at[idx, 'Match_Level'] = 'none'
            continue

        unit_info = parse_unit_type(kennwert['unit'])

        # Prozentuale Kosten für Pass 2 sammeln
        if unit_info['type'] in ['percentage', 'percentage_yearly']:
            percentage_rows.append((idx, kennwert, unit_info, quantity))
            df.at[idx, 'Einheit_Kennwert'] = kennwert['unit']
            df.at[idx, 'Matched_Code'] = kennwert['code']
            continue

        # Berechne direkte Kosten
        result = calculate_element_cost(bkp_code, quantity, kennwerte_df, cost_level)
        df.at[idx, 'Einzelkosten'] = result['cost']
        df.at[idx, 'Berechnungsart'] = result['calculation_type']
        df.at[idx, 'Matched_Code'] = result['matched_code'] or ''
        df.at[idx, 'Match_Level'] = result['match_level']
        df.at[idx, 'Einheit_Kennwert'] = result['unit']

    # Berechne Zwischensummen für Prozent-Basis
    bauwerkskosten = calculate_cost_hierarchy_sum(df, ['C', 'D', 'E', 'F', 'G'])
    erstellungskosten_basis = calculate_cost_hierarchy_sum(df, ['B', 'H', 'I', 'J'])
    grundstueck_kosten = calculate_cost_hierarchy_sum(df, ['A'])
    umgebungskosten = calculate_cost_hierarchy_sum(df, ['I'])
    c_kosten = calculate_cost_hierarchy_sum(df, ['C'])

    reference_costs = {
        'bauwerkskosten': bauwerkskosten,
        'baukosten': bauwerkskosten,
        'erstellungskosten': bauwerkskosten + erstellungskosten_basis,
        'referenz_kosten': df['Einzelkosten'].sum(),
        'total': df['Einzelkosten'].sum(),
        'umgebungskosten': umgebungskosten,
        'grundstueck': grundstueck_kosten,
        'a01_kosten': grundstueck_kosten,
        'c_kosten': c_kosten,
        'verkaufspreis': df['Einzelkosten'].sum() * 1.1,  # Schätzung
        'betriebskosten': df['Einzelkosten'].sum() * 0.05  # Schätzung
    }

    # === PASS 2: Prozentuale Kosten ===
    for idx, kennwert, unit_info, quantity in percentage_rows:
        percentage_base = unit_info.get('percentage_base', 'total')
        base = reference_costs.get(percentage_base, reference_costs['total'])
        cost = base * (kennwert['value'] / 100)

        df.at[idx, 'Einzelkosten'] = cost
        df.at[idx, 'Berechnungsart'] = f"percentage_{percentage_base}"
        df.at[idx, 'Match_Level'] = kennwert['level_matched']

    # === Berechne finale Zusammenfassungen ===
    bauwerkskosten_final = calculate_cost_hierarchy_sum(df, ['C', 'D', 'E', 'F', 'G'])

    # Erstellungskosten = B + Bauwerkskosten + H + I + J + V + W
    erstellungskosten_components = calculate_cost_hierarchy_sum(df, ['B', 'H', 'I', 'J', 'V', 'W'])
    erstellungskosten_final = bauwerkskosten_final + erstellungskosten_components

    # Anlagekosten = A + Erstellungskosten + Y + Z
    anlagekosten_components = calculate_cost_hierarchy_sum(df, ['A', 'Y', 'Z'])
    anlagekosten_final = erstellungskosten_final + anlagekosten_components

    summaries = {
        'bauwerkskosten': bauwerkskosten_final,
        'erstellungskosten': erstellungskosten_final,
        'anlagekosten': anlagekosten_final,
        'total': df['Einzelkosten'].sum()
    }

    return df, summaries


# ============================================================================
# UI KOMPONENTEN
# ============================================================================

def render_config_section() -> str:
    """Konfigurationsbereich für Kostenstufen-Auswahl."""
    st.subheader("⚙️ Einstellungen")

    col1, col2, col3 = st.columns(3)

    with col1:
        cost_level = st.selectbox(
            "Kostenstufe",
            options=['tief', 'mittel', 'hoch'],
            index=1,
            help="tief = Minimum, mittel = Durchschnitt, hoch = Maximum",
            key='cost_level_select'
        )
        set_state('selected_cost_level', cost_level)

    with col2:
        config = get_state(CFG_COST_ESTIMATION_CONFIG)
        if config:
            tolerance = config.get('tolerance', 0)
            st.metric("Toleranz", format_tolerance(tolerance))
        else:
            st.info("Kostenermittlungsart nicht gewählt")
            tolerance = 0

    with col3:
        st.checkbox(
            "Projektspezifische Kennwerte",
            value=False,
            disabled=True,
            help="Ermöglicht Anpassung der Standard-Kennwerte (coming soon)",
            key='use_project_rates'
        )

    return cost_level


def render_quantity_input_section(df: pd.DataFrame) -> pd.DataFrame:
    """Bereich für Mengeneingabe/-bearbeitung."""
    st.subheader("📐 Mengenangaben")

    has_quantity = 'Menge' in df.columns
    has_unit = 'Einheit' in df.columns

    if has_quantity and df['Menge'].notna().sum() > 0:
        st.success(f"✅ Mengen aus Klassifizierung übernommen ({df['Menge'].notna().sum()} Positionen)")

        if st.checkbox("Mengen bearbeiten", key='edit_quantities'):
            display_cols = ['BKP_Code', 'BKP_Beschreibung', 'Menge']
            if has_unit:
                display_cols.append('Einheit')

            edited_df = st.data_editor(
                df[display_cols].head(50),
                column_config={
                    'Menge': st.column_config.NumberColumn(
                        'Menge',
                        min_value=0,
                        format="%.2f"
                    ),
                    'BKP_Code': st.column_config.TextColumn('BKP Code', disabled=True),
                    'BKP_Beschreibung': st.column_config.TextColumn('Beschreibung', disabled=True),
                },
                hide_index=True,
                key='quantity_editor'
            )
            # Update df mit bearbeiteten Werten
            for col in ['Menge']:
                if col in edited_df.columns:
                    df.loc[df.index[:len(edited_df)], col] = edited_df[col].values
    else:
        st.warning("⚠️ Keine Mengenangaben in den Daten gefunden.")
        st.info("Bitte geben Sie globale Projektflächen ein:")

        col1, col2 = st.columns(2)
        with col1:
            grundflaeche = st.number_input("Grundfläche (m²)", min_value=0.0, value=500.0, key='grundflaeche')
            geschossflaeche = st.number_input("Geschossfläche (m²)", min_value=0.0, value=1000.0, key='geschossflaeche')
        with col2:
            fassadenflaeche = st.number_input("Fassadenfläche (m²)", min_value=0.0, value=800.0, key='fassadenflaeche')
            dachflaeche = st.number_input("Dachfläche (m²)", min_value=0.0, value=500.0, key='dachflaeche')

        set_state('project_areas', {
            'grundflaeche': grundflaeche,
            'geschossflaeche': geschossflaeche,
            'fassadenflaeche': fassadenflaeche,
            'dachflaeche': dachflaeche
        })

        # Setze Default-Mengen basierend auf Einheit
        if 'Menge' not in df.columns:
            df['Menge'] = 1.0

    return df


def render_results_section(results_df: pd.DataFrame, summaries: Dict[str, float]):
    """Zeigt Berechnungsergebnisse an."""
    st.subheader("📊 Ergebnisse")

    # Toleranz holen
    config = get_state(CFG_COST_ESTIMATION_CONFIG)
    tolerance = config.get('tolerance', 0) if config else 0

    # === Kostenübersicht ===
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Bauwerkskosten",
            format_currency(summaries['bauwerkskosten']),
            help="Kosten C-G: Konstruktion, Technik, Ausbau, Bedachung, Ausbau Gebäude"
        )

    with col2:
        st.metric(
            "Erstellungskosten",
            format_currency(summaries['erstellungskosten']),
            help="B + Bauwerkskosten + H, I, J + Zuschläge V, W"
        )

    with col3:
        st.metric(
            "Anlagekosten",
            format_currency(summaries['anlagekosten']),
            help="A + Erstellungskosten + Zuschläge Y, Z"
        )

    with col4:
        total = summaries['total']
        if tolerance > 0:
            min_val, _ = calculate_cost_with_tolerance(total, tolerance)
            delta_str = f"± {format_currency(total - min_val)}"
        else:
            delta_str = None

        st.metric(
            "Total",
            format_currency(total),
            delta=delta_str
        )

    render_divider("section")

    # === Aufgliederung nach Hauptgruppen ===
    st.subheader("📋 Aufgliederung nach Hauptgruppen")

    # Füge Hauptgruppe hinzu
    results_df['Hauptgruppe'] = results_df['BKP_Code'].apply(
        lambda x: str(x)[0].upper() if pd.notna(x) and x else 'Unbekannt'
    )

    # Gruppiere nach Hauptgruppe
    for hg in sorted(results_df['Hauptgruppe'].unique()):
        if hg == 'Unbekannt' or hg not in EBKP_MAIN_GROUPS:
            continue

        hg_df = results_df[results_df['Hauptgruppe'] == hg]
        hg_total = hg_df['Einzelkosten'].sum()
        hg_count = len(hg_df)
        hg_name = EBKP_MAIN_GROUPS.get(hg, 'Unbekannt')

        # Bestimme Kostengruppen-Zugehörigkeit
        if hg in ['C', 'D', 'E', 'F', 'G']:
            badge = "🏗️ Bauwerkskosten"
        elif hg in ['B', 'H', 'I', 'J', 'V', 'W']:
            badge = "🔧 Erstellungskosten"
        elif hg in ['A', 'Y', 'Z']:
            badge = "💰 Anlagekosten"
        else:
            badge = ""

        with st.expander(
            f"**{hg}** - {hg_name}: {format_currency(hg_total)} ({hg_count} Positionen) {badge}",
            expanded=hg_total > 0
        ):
            display_cols = ['BKP_Code', 'BKP_Beschreibung', 'Menge', 'Matched_Code', 'Match_Level', 'Einzelkosten']
            display_cols = [c for c in display_cols if c in hg_df.columns]

            st.dataframe(
                hg_df[display_cols],
                column_config={
                    'Einzelkosten': st.column_config.NumberColumn(
                        'Kosten CHF',
                        format="%.2f"
                    ),
                    'Match_Level': st.column_config.TextColumn('Lookup'),
                },
                hide_index=True
            )


def render_export_section(results_df: pd.DataFrame, summaries: Dict[str, float]):
    """Export-Optionen."""
    st.subheader("📤 Export")

    col1, col2 = st.columns(2)

    with col1:
        # CSV Export
        csv = results_df.to_csv(index=False, sep=';', encoding='utf-8-sig')
        st.download_button(
            "📄 CSV herunterladen",
            data=csv,
            file_name=f"Kostenberechnung_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

    with col2:
        # PDF Export
        if REPORTLAB_AVAILABLE:
            if st.button("📑 PDF generieren"):
                with st.spinner("PDF wird erstellt..."):
                    pdf_buffer = generate_cost_report_pdf(results_df, summaries)
                    if pdf_buffer:
                        st.download_button(
                            "📥 PDF herunterladen",
                            data=pdf_buffer,
                            file_name=f"Kostenberechnung_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf"
                        )
        else:
            st.warning("ReportLab nicht installiert. PDF-Export nicht verfügbar.")


def get_pdf_custom_styles() -> Dict[str, ParagraphStyle]:
    """
    Definiert ein konsistentes, professionelles Style-Set für alle
    Textabschnitte im PDF.

    Returns:
        Dictionary mit benannten ParagraphStyle-Objekten
    """
    base_styles = getSampleStyleSheet()

    custom_styles = {
        "title": ParagraphStyle(
            "CustomTitle",
            parent=base_styles["Heading1"],
            fontSize=28,
            textColor=colors.HexColor(COLOR_PRIMARY_HEADER),
            spaceAfter=8,
            spaceBefore=0,
            alignment=0,  # Links
            fontName="Helvetica-Bold",
        ),
        "subtitle": ParagraphStyle(
            "CustomSubtitle",
            parent=base_styles["Normal"],
            fontSize=11,
            textColor=colors.HexColor(COLOR_TEXT_LIGHT),
            spaceAfter=20,
            alignment=0,
        ),
        "heading_section": ParagraphStyle(
            "HeadingSection",
            parent=base_styles["Heading2"],
            fontSize=14,
            textColor=colors.HexColor(COLOR_SECONDARY_HEADER),
            spaceAfter=12,
            spaceBefore=8,
            fontName="Helvetica-Bold",
        ),
        "heading_subsection": ParagraphStyle(
            "HeadingSubsection",
            parent=base_styles["Heading3"],
            fontSize=11,
            textColor=colors.HexColor(COLOR_SECONDARY_HEADER),
            spaceAfter=8,
            spaceBefore=4,
            fontName="Helvetica-Bold",
        ),
        "normal": ParagraphStyle(
            "CustomNormal",
            parent=base_styles["Normal"],
            fontSize=10,
            textColor=colors.HexColor(COLOR_TEXT_DARK),
            alignment=0,
        ),
        "small": ParagraphStyle(
            "SmallText",
            parent=base_styles["Normal"],
            fontSize=8,
            textColor=colors.HexColor(COLOR_TEXT_LIGHT),
            alignment=0,
        ),
        "footer": ParagraphStyle(
            "FooterText",
            parent=base_styles["Normal"],
            fontSize=8,
            textColor=colors.HexColor(COLOR_TEXT_LIGHT),
            alignment=1,  # Zentriert
            spaceAfter=4,
        ),
    }
    return custom_styles


def create_pdf_project_info_table(projekt_daten: Any) -> Table:
    """
    Erzeugt eine formatierte Tabelle mit Projektinformationen.

    Args:
        projekt_daten: ProjektDaten-Objekt mit objekt, bauherr, baumanagement

    Returns:
        ReportLab Table mit Projekt-Metadaten
    """
    # Daten vorbereiten - mit sicheren Attributzugriffen
    objekt = getattr(projekt_daten, 'objekt', None)
    bauherr = getattr(projekt_daten, 'bauherr', None)
    baumanagement = getattr(projekt_daten, 'baumanagement', None)

    project_data = [
        # OBJEKT-Bereich
        ["OBJEKT", "Projektname", getattr(objekt, 'projektname', 'N/A') if objekt else 'N/A'],
        ["", "Adresse", getattr(objekt, 'adresse', '') if objekt else ''],
        ["", "PLZ/Ort", getattr(objekt, 'plz_ort', '') if objekt else ''],
    ]

    if bauherr:
        project_data.extend([
            # BAUHERR-Bereich
            ["BAUHERR", "Name", getattr(bauherr, 'name', '') if bauherr else ''],
            ["", "Adresse", getattr(bauherr, 'adresse', '') if bauherr else ''],
            ["", "PLZ/Ort", getattr(bauherr, 'plz_ort', '') if bauherr else ''],
        ])

    if baumanagement:
        project_data.extend([
            # BAUMANAGEMENT-Bereich
            ["BAUMANAGEMENT", "Firma", getattr(baumanagement, 'firma', '') if baumanagement else ''],
            ["", "Kontaktperson", getattr(baumanagement, 'kontaktperson', '') if baumanagement else ''],
            ["", "Adresse", getattr(baumanagement, 'adresse', '') if baumanagement else ''],
            ["", "PLZ/Ort", getattr(baumanagement, 'plz_ort', '') if baumanagement else ''],
        ])

    table = Table(project_data, colWidths=[4 * cm, 3 * cm, 11.5 * cm])

    style_commands = [
        # Textfarben und Schriftarten
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor(COLOR_TEXT_DARK)),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        # Ausrichtung
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        # Padding
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        # Rahmen um OBJEKT-Bereich
        ("BOX", (0, 0), (-1, 2), 1.5, colors.HexColor(COLOR_SECONDARY_HEADER)),
    ]

    # Dynamische Rahmen basierend auf vorhandenen Daten
    if bauherr:
        style_commands.append(("BOX", (0, 3), (-1, 5), 1.5, colors.HexColor(COLOR_SECONDARY_HEADER)))
    if baumanagement:
        start_row = 6 if bauherr else 3
        style_commands.append(("BOX", (0, start_row), (-1, start_row + 3), 1.5, colors.HexColor(COLOR_SECONDARY_HEADER)))

    table.setStyle(TableStyle(style_commands))
    return table


def create_pdf_cost_summary_table(summaries: Dict[str, float], tolerance: int = 0) -> Table:
    """
    Erzeugt eine Kostenzusammenfassungs-Tabelle mit Zwischen- und
    Endsummen sowie Toleranzbereich.

    Args:
        summaries: Dict mit Kostenwerten (bauwerkskosten, erstellungskosten, anlagekosten, total)
        tolerance: Toleranzprozentsatz

    Returns:
        ReportLab Table mit Kostenzusammenfassung
    """
    total = summaries.get('total', summaries.get('anlagekosten', 0))
    if tolerance > 0:
        min_val, max_val = calculate_cost_with_tolerance(total, tolerance)
    else:
        min_val, max_val = total, total

    summary_data = [
        ["POSITION", "BETRAG CHF"],
        ["Bauwerkskosten (C-G)", format_currency(summaries.get('bauwerkskosten', 0))],
        ["Erstellungskosten (B-W)", format_currency(summaries.get('erstellungskosten', 0))],
        ["Anlagekosten (Total)", format_currency(summaries.get('anlagekosten', 0))],
        ["Toleranzbereich (min)", format_currency(min_val)],
        ["Toleranzbereich (max)", format_currency(max_val)],
    ]

    table = Table(summary_data, colWidths=[12 * cm, 6.5 * cm])

    table.setStyle(
        TableStyle(
            [
                # Kopfzeile
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(COLOR_SECONDARY_HEADER)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("ALIGN", (0, 0), (0, 0), "LEFT"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
                # Datenzeilen
                ("BACKGROUND", (0, 1), (-1, 2), colors.white),
                ("BACKGROUND", (0, 3), (-1, 3), colors.HexColor(COLOR_ACCENT)),
                ("BACKGROUND", (0, 4), (-1, 5), colors.HexColor(COLOR_BACKGROUND_ALT)),
                ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor(COLOR_TEXT_DARK)),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTNAME", (0, 3), (-1, 3), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (0, 1), (0, -1), "LEFT"),
                ("ALIGN", (1, 1), (1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def create_pdf_detail_table(results_df: pd.DataFrame) -> Tuple[Table, int]:
    """
    Erzeugt eine detaillierte Kostenberechnung-Tabelle mit aggregierten Positionen.

    Jeder eBKP-H Code erscheint nur einmal mit summierten Mengen und Kosten.

    Args:
        results_df: DataFrame mit Spalten:
                 ['BKP_Code', 'BKP_Beschreibung', 'Menge', 'Einheit_Kennwert',
                  'Einzelkosten', 'Match_Level']

    Returns:
        Tuple aus (Table-Objekt, Anzahl eindeutige Positionen mit Kosten)
    """
    # Filtere nur Positionen mit Einzelkosten > 0
    df_with_costs = results_df[results_df.get("Einzelkosten", pd.Series([0])) > 0].copy()

    if df_with_costs.empty:
        # Leere Tabelle zurückgeben
        table_data = [["eBKP-H", "Beschreibung", "Menge", "Einheit", "Kosten CHF"]]
        table = Table(table_data, colWidths=[2 * cm, 8 * cm, 2 * cm, 3 * cm, 3.5 * cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(COLOR_SECONDARY_HEADER)),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ]))
        return table, 0

    # === AGGREGATION: Gruppiere nach BKP_Code ===
    # Für jede Position: Summiere Menge und Einzelkosten, behalte erste Beschreibung/Einheit
    aggregated = df_with_costs.groupby('BKP_Code', as_index=False).agg({
        'BKP_Beschreibung': 'first',
        'Menge': 'sum',
        'Einheit_Kennwert': 'first',
        'Einzelkosten': 'sum',
        'Match_Level': 'first'
    })

    # Sortiere nach BKP_Code
    aggregated = aggregated.sort_values('BKP_Code').reset_index(drop=True)

    # Tabellenheader
    table_data = [
        [
            "eBKP-H",
            "Beschreibung",
            "Menge",
            "Einheit",
            "Kosten CHF",
        ]
    ]

    # Datenzellen aus aggregierten Daten
    for _, row in aggregated.iterrows():
        # Beschreibung kürzen falls zu lang
        beschreibung = str(row.get("BKP_Beschreibung", ""))[:50]

        menge = f"{row.get('Menge', 0):.2f}".rstrip("0").rstrip(".")
        einheit = str(row.get("Einheit_Kennwert", ""))[:15]
        kosten = format_currency(row.get("Einzelkosten", 0))

        table_data.append(
            [
                str(row.get("BKP_Code", ""))[:10],
                beschreibung,
                menge,
                einheit,
                kosten,
            ]
        )

    # Tabelle mit optimalen Spaltenbreiten (5 Spalten ohne Match)
    table = Table(
        table_data,
        colWidths=[2 * cm, 8 * cm, 2 * cm, 3 * cm, 3.5 * cm],
    )

    # Stil für Zeilen-Alternation
    row_colors = [
        colors.white,
        colors.HexColor(COLOR_BACKGROUND_ALT),
    ]

    style_list = [
        # Kopfzeile
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(COLOR_SECONDARY_HEADER)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
    ]

    # Zeilen-Alternation
    for row_idx in range(1, len(table_data)):
        color = row_colors[row_idx % 2]
        style_list.append(
            ("BACKGROUND", (0, row_idx), (-1, row_idx), color)
        )

    # Allgemeine Datenzeilen-Styles
    style_list.extend(
        [
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor(COLOR_TEXT_DARK)),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            # Ausrichtung für Spalten
            ("ALIGN", (0, 1), (0, -1), "CENTER"),   # Code
            ("ALIGN", (1, 1), (1, -1), "LEFT"),     # Beschreibung
            ("ALIGN", (2, 1), (2, -1), "RIGHT"),    # Menge
            ("ALIGN", (3, 1), (3, -1), "CENTER"),   # Einheit
            ("ALIGN", (4, 1), (4, -1), "RIGHT"),    # Kosten
            ("VALIGN", (0, 1), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]
    )

    table.setStyle(TableStyle(style_list))
    return table, len(aggregated)


def generate_cost_report_pdf(
    results_df: pd.DataFrame,
    summaries: Dict[str, float]
) -> BytesIO:
    """
    Generiert ein professionelles PDF-Dokument der Kostenberechnung
    im BKP-Stil mit Projektinformationen, Kostenzusammenfassung und
    detaillierter Positionalaufschlüsselung.

    Args:
        results_df: DataFrame mit Kostenpositionen
        summaries: Dict mit Kostenwerten

    Returns:
        BytesIO-Buffer mit PDF-Inhalt, oder None bei Fehler
    """
    if not REPORTLAB_AVAILABLE:
        return None

    try:
        # PDF-Konfiguration
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=MARGIN_RIGHT * cm,
            leftMargin=MARGIN_LEFT * cm,
            topMargin=MARGIN_TOP * cm,
            bottomMargin=MARGIN_BOTTOM * cm,
        )

        # Elemente für Dokument
        elements = []
        styles = get_pdf_custom_styles()

        # Hole Konfiguration
        config = get_state(CFG_COST_ESTIMATION_CONFIG)
        tolerance = config.get('tolerance', 0) if config else 0
        projekt_daten = get_state(DATA_PROJEKT_DATEN)

        # =========================================================
        # TITEL & LOGO
        # =========================================================
        # Logo und Titel nebeneinander in einer Tabelle
        title_content = [
            [Paragraph("Kostenberechnung eBKP-H", styles["title"])]
        ]
        subtitle_content = Paragraph(
            f"Erstellt am {datetime.now().strftime('%d.%m.%Y um %H:%M Uhr')}",
            styles["subtitle"],
        )

        # Versuche Logo zu laden
        if LOGO_PATH.exists():
            try:
                logo = Image(str(LOGO_PATH), width=3 * cm, height=3 * cm)
                logo.hAlign = 'RIGHT'

                # Titel-Tabelle mit Logo rechts
                header_table = Table(
                    [[title_content[0][0], logo]],
                    colWidths=[14 * cm, 4 * cm]
                )
                header_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                    ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                    ('TOPPADDING', (0, 0), (-1, -1), 0),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ]))
                elements.append(header_table)
            except Exception:
                # Fallback: Nur Titel ohne Logo
                elements.append(Paragraph("Kostenberechnung eBKP-H", styles["title"]))
        else:
            # Kein Logo vorhanden
            elements.append(Paragraph("Kostenberechnung eBKP-H", styles["title"]))

        elements.append(subtitle_content)
        elements.append(Spacer(1, SPACING_SECTION * cm))

        # =========================================================
        # PROJEKTINFORMATIONEN (falls vorhanden)
        # =========================================================
        if projekt_daten and hasattr(projekt_daten, 'objekt'):
            elements.append(
                Paragraph("Projektinformationen", styles["heading_section"])
            )
            project_table = create_pdf_project_info_table(projekt_daten)
            elements.append(project_table)
            elements.append(Spacer(1, SPACING_SECTION * cm))

        # =========================================================
        # KOSTENERMITTLUNGS-KONFIGURATION (falls vorhanden)
        # =========================================================
        if config and config.get('selected'):
            elements.append(
                Paragraph("Kostenermittlung & Parameter", styles["heading_section"])
            )

            config_data = [
                ["Parameter", "Wert"],
                ["Kostenermittlungsart", config.get("name", "N/A")],
                ["Toleranz", f"± {config.get('tolerance', 0)}%"],
                ["Projektphase", f"{config.get('project_phase', 'N/A')} ({config.get('phase_code', 'N/A')})"],
                ["eBKP-Klassifizierungstiefe", config.get("ebkp_depth", "N/A")],
            ]

            config_table = Table(config_data, colWidths=[6 * cm, 10 * cm])
            config_table.setStyle(
                TableStyle(
                    [
                        # Kopfzeile
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(COLOR_SECONDARY_HEADER)),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 9),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                        ("TOPPADDING", (0, 0), (-1, 0), 6),
                        # Datenzeilen
                        ("BACKGROUND", (0, 1), (0, -1), colors.HexColor(COLOR_ACCENT)),
                        ("BACKGROUND", (1, 1), (-1, -1), colors.white),
                        ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor(COLOR_TEXT_DARK)),
                        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 1), (-1, -1), 9),
                        ("ALIGN", (0, 1), (0, -1), "LEFT"),
                        ("ALIGN", (1, 1), (1, -1), "LEFT"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
                    ]
                )
            )
            elements.append(config_table)
            elements.append(Spacer(1, SPACING_SECTION * cm))

        # =========================================================
        # KOSTENZUSAMMENFASSUNG
        # =========================================================
        elements.append(
            Paragraph("Kostenzusammenfassung", styles["heading_section"])
        )
        summary_table = create_pdf_cost_summary_table(summaries, tolerance)
        elements.append(summary_table)
        elements.append(Spacer(1, SPACING_SECTION * cm))

        # =========================================================
        # DETAILLIERTE KOSTENBERECHNUNG
        # =========================================================
        elements.append(
            Paragraph("Detaillierte Kostenberechnung", styles["heading_section"])
        )

        detail_table, positions_with_costs = create_pdf_detail_table(results_df)

        elements.append(detail_table)
        elements.append(Spacer(1, SPACING_SUBSECTION * cm))
        elements.append(
            Paragraph(f"Total: {positions_with_costs} Positionen mit Kosten", styles["small"])
        )
        elements.append(Spacer(1, SPACING_SECTION * cm))

        # =========================================================
        # AUFGLIEDERUNG NACH HAUPTGRUPPEN
        # =========================================================
        elements.append(PageBreak())
        elements.append(
            Paragraph("Aufgliederung nach Hauptgruppen", styles["heading_section"])
        )

        # Füge Hauptgruppe hinzu
        results_df_copy = results_df.copy()
        results_df_copy['Hauptgruppe'] = results_df_copy['BKP_Code'].apply(
            lambda x: str(x)[0].upper() if pd.notna(x) and x else 'X'
        )

        for hg in sorted(results_df_copy['Hauptgruppe'].unique()):
            if hg == 'X' or hg not in EBKP_MAIN_GROUPS:
                continue

            hg_df = results_df_copy[results_df_copy['Hauptgruppe'] == hg]
            hg_total = hg_df['Einzelkosten'].sum()
            hg_name = EBKP_MAIN_GROUPS.get(hg, 'Unbekannt')

            if hg_total == 0:
                continue

            # Aggregiere Positionen innerhalb der Hauptgruppe
            hg_aggregated = hg_df.groupby('BKP_Code', as_index=False).agg({
                'BKP_Beschreibung': 'first',
                'Menge': 'sum',
                'Einzelkosten': 'sum'
            }).sort_values('BKP_Code')

            # Kostengruppen-Badge
            if hg in ['C', 'D', 'E', 'F', 'G']:
                badge = "(Bauwerkskosten)"
            elif hg in ['B', 'H', 'I', 'J', 'V', 'W']:
                badge = "(Erstellungskosten)"
            elif hg in ['A', 'Y', 'Z']:
                badge = "(Anlagekosten)"
            else:
                badge = ""

            elements.append(
                Paragraph(
                    f"<b>{hg} - {hg_name}</b>: {format_currency(hg_total)} ({len(hg_aggregated)} Positionen) {badge}",
                    styles["heading_subsection"]
                )
            )

            # Mini-Tabelle für diese Gruppe (aggregiert)
            group_table_data = [['Code', 'Beschreibung', 'Menge', 'Kosten CHF']]
            for _, row in hg_aggregated.head(15).iterrows():  # Max 15 eindeutige Positionen pro Gruppe
                group_table_data.append([
                    str(row.get('BKP_Code', ''))[:10],
                    str(row.get('BKP_Beschreibung', ''))[:40],
                    f"{row.get('Menge', 1):.1f}",
                    format_currency(row.get('Einzelkosten', 0))
                ])

            if len(hg_aggregated) > 15:
                group_table_data.append(['...', f'und {len(hg_aggregated) - 15} weitere', '', ''])

            group_table = Table(group_table_data, colWidths=[2.5 * cm, 8 * cm, 2 * cm, 3.5 * cm])
            group_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLOR_ACCENT)),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
                ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))

            elements.append(group_table)
            elements.append(Spacer(1, SPACING_SUBSECTION * cm))

        # =========================================================
        # FOOTER
        # =========================================================
        elements.append(Spacer(1, SPACING_SECTION * cm))
        footer_text = (
            "Diese Kostenberechnung basiert auf Kennwerten und dient als Schätzung. "
            "Die tatsächlichen Kosten können abweichen. Das Programm eBKP+ übernimmt "
            f"keine Haftung. Stand: {datetime.now().strftime('%d.%m.%Y')}"
        )
        elements.append(Paragraph(footer_text, styles["footer"]))

        # =========================================================
        # PDF GENERIEREN
        # =========================================================
        doc.build(elements)
        buffer.seek(0)
        return buffer

    except Exception as error:
        st.error(f"❌ Fehler bei PDF-Generierung: {str(error)}")
        return None


# ============================================================================
# HAUPTSEITE
# ============================================================================

def normalize_bkp_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalisiert BKP-Spaltennamen auf Standard-Format.

    Unterstützt verschiedene Spaltennamen:
    - BKP_Code, eBKP_Code, eBKP-H Code, bkp_code, Code
    - BKP_Beschreibung, eBKP_Beschreibung, Beschreibung, Description
    """
    df = df.copy()

    # BKP Code normalisieren
    code_columns = ['BKP_Code', 'eBKP_Code', 'eBKP-H Code', 'bkp_code', 'Code', 'code', 'eBKP-H_Code']
    for col in code_columns:
        if col in df.columns and 'BKP_Code' not in df.columns:
            df['BKP_Code'] = df[col]
            break

    # Beschreibung normalisieren
    desc_columns = ['BKP_Beschreibung', 'eBKP_Beschreibung', 'Beschreibung', 'Description', 'description', 'Kostengruppe / Position']
    for col in desc_columns:
        if col in df.columns and 'BKP_Beschreibung' not in df.columns:
            df['BKP_Beschreibung'] = df[col]
            break

    # Menge normalisieren
    qty_columns = ['Menge', 'menge', 'Quantity', 'quantity', 'Anzahl', 'anzahl', 'Count']
    for col in qty_columns:
        if col in df.columns and 'Menge' not in df.columns:
            df['Menge'] = pd.to_numeric(df[col], errors='coerce').fillna(1.0)
            break

    return df


def render_data_source_section() -> Optional[pd.DataFrame]:
    """
    Rendert den Datenquellen-Bereich mit Tabs für verschiedene Import-Optionen.

    Returns:
        DataFrame mit BKP-Codes oder None
    """
    st.subheader("📂 Datenquelle")

    # Prüfe ob bereits Daten geladen sind
    has_existing_data = has_classification_results()

    if has_existing_data:
        existing_df = get_state(DATA_CLASSIFICATION_RESULTS)
        col1, col2 = st.columns([3, 1])
        with col1:
            st.success(f"✅ {len(existing_df)} klassifizierte Elemente aus Session geladen")
        with col2:
            if st.button("🗑️ Daten löschen", help="Aktuelle Daten löschen und neue laden"):
                set_state(DATA_CLASSIFICATION_RESULTS, None)
                set_state('cost_results_df', None)
                set_state('cost_summaries', None)
                st.rerun()

    # Tabs für verschiedene Datenquellen
    tab_session, tab_upload = st.tabs([
        "📊 Aus KI-Klassifizierung",
        "📤 CSV importieren"
    ])

    with tab_session:
        if has_existing_data:
            st.info("Daten aus der KI-Klassifizierung werden verwendet.")
            # Zeige Vorschau
            with st.expander("Datenvorschau", expanded=False):
                preview_cols = [c for c in ['BKP_Code', 'BKP_Beschreibung', 'Menge', 'Einheit'] if c in existing_df.columns]
                if preview_cols:
                    st.dataframe(existing_df[preview_cols].head(10), hide_index=True)
                else:
                    st.dataframe(existing_df.head(10), hide_index=True)
        else:
            st.warning("Keine Daten aus der KI-Klassifizierung vorhanden.")
            st.info("Führen Sie zuerst die KI-Klassifizierung durch oder importieren Sie eine CSV-Datei.")

    with tab_upload:
        st.markdown("""
        **CSV-Anforderungen:**
        - Trennzeichen: Semikolon (;) oder Komma (,)
        - Encoding: UTF-8
        - Erforderliche Spalte: `BKP_Code` (oder `eBKP_Code`, `eBKP-H Code`)
        - Optional: `BKP_Beschreibung`, `Menge`, `Einheit`
        """)

        uploaded_file = st.file_uploader(
            "CSV mit BKP-Codes hochladen",
            type=['csv'],
            help="CSV-Datei mit klassifizierten BKP-Codes",
            key='csv_uploader'
        )

        if uploaded_file:
            try:
                # Versuche verschiedene Trennzeichen
                content = uploaded_file.getvalue().decode('utf-8-sig')
                if ';' in content[:1000]:
                    sep = ';'
                else:
                    sep = ','

                uploaded_file.seek(0)
                df_upload = pd.read_csv(uploaded_file, sep=sep, encoding='utf-8-sig')

                # Normalisiere Spaltennamen
                df_upload = normalize_bkp_columns(df_upload)

                if 'BKP_Code' not in df_upload.columns:
                    st.error("❌ Keine BKP-Code Spalte gefunden!")
                    st.info(f"Gefundene Spalten: {list(df_upload.columns)}")
                    st.info("Bitte stellen Sie sicher, dass eine der folgenden Spalten vorhanden ist: BKP_Code, eBKP_Code, eBKP-H Code, Code")
                    return None

                # Zeige Vorschau
                st.success(f"✅ {len(df_upload)} Zeilen erkannt")

                with st.expander("Datenvorschau", expanded=True):
                    preview_cols = [c for c in ['BKP_Code', 'BKP_Beschreibung', 'Menge', 'Einheit'] if c in df_upload.columns]
                    if preview_cols:
                        st.dataframe(df_upload[preview_cols].head(10), hide_index=True)
                    else:
                        st.dataframe(df_upload.head(10), hide_index=True)

                    # Zeige Spalten-Info
                    st.caption(f"Spalten: {', '.join(df_upload.columns)}")

                # Lade-Button
                if st.button("📥 Daten für Kostenberechnung laden", type="primary"):
                    set_state(DATA_CLASSIFICATION_RESULTS, df_upload)
                    set_state('cost_results_df', None)
                    set_state('cost_summaries', None)
                    st.success("✅ Daten erfolgreich geladen!")
                    st.rerun()

            except Exception as e:
                st.error(f"❌ Fehler beim Laden der CSV: {e}")
                return None

    # Rückgabe der aktuellen Daten
    if has_classification_results():
        return get_state(DATA_CLASSIFICATION_RESULTS).copy()
    return None


st.title("💰 Kostenberechnung")
st.caption("Berechnung der Kosten basierend auf eBKP-H Klassifizierung und Kennwerten")

# Lade Standard-Kennwerte
default_kennwerte_df = load_kennwerte_from_file()

if default_kennwerte_df.empty:
    st.error("Standard-Kennwerte konnten nicht geladen werden.")
    st.stop()

render_divider("section")

# === Kennwerte-Katalog (Standard oder Eigene) ===
kennwerte_df = render_kennwerte_section(default_kennwerte_df)

# Zeige aktiven Status
use_custom = get_state(CFG_USE_CUSTOM_KENNWERTE, False)
if use_custom:
    st.success(f"🟢 **Eigene Kennwerte aktiv** - {len(kennwerte_df)} Einträge")
else:
    st.info(f"📚 Standard-Kennwerte - {len(kennwerte_df)} Einträge")

render_divider("section")

# === Datenquelle ===
df = render_data_source_section()

if df is None:
    st.info("👆 Bitte laden Sie Daten über eine der obigen Optionen.")
    st.stop()

# Zeige geladene Daten-Info
st.success(f"✅ {len(df)} Elemente bereit für Kostenberechnung")

render_divider("section")

# === Konfiguration ===
cost_level = render_config_section()

render_divider("section")

# === Mengen ===
df = render_quantity_input_section(df)

render_divider("section")

# === Berechnung ===
st.subheader("🧮 Berechnung")

# Info über verwendete Kennwerte
if use_custom:
    st.caption("🟢 Berechnung mit **eigenen Kennwerten**")
else:
    st.caption("📋 Berechnung mit **Standard-Kennwerten**")

if st.button("💵 Kosten berechnen", type="primary", use_container_width=True):
    with st.spinner("Berechne Kosten mit hierarchischem Lookup..."):
        project_areas = get_state('project_areas')

        results_df, summaries = calculate_all_costs(
            df,
            kennwerte_df,
            cost_level=cost_level,
            quantity_column='Menge',
            project_areas=project_areas
        )

        set_state('cost_results_df', results_df)
        set_state('cost_summaries', summaries)

    st.success("✅ Berechnung abgeschlossen!")
    st.rerun()

# === Ergebnisse anzeigen ===
results_df = get_state('cost_results_df')
summaries = get_state('cost_summaries')

if results_df is not None and summaries is not None:
    render_divider("section")
    render_results_section(results_df, summaries)
    render_divider("section")
    render_export_section(results_df, summaries)

# Footer
render_page_footer()
