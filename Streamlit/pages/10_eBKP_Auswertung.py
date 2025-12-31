'''
eBKP-H Kostenauswertung
Visualisierung von BKP-klassifizierten Daten mit hierarchischer Gliederung
'''

import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os
from io import BytesIO
from datetime import datetime

# Füge Parent-Verzeichnis zum Path hinzu für Imports
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from helpers.sia_lho_102_config import format_tolerance
except ImportError:
    def format_tolerance(tolerance: int) -> str:
        return f'± {tolerance}%' if tolerance > 0 else 'exakt'

from helpers.sidebar_navigation import render_sidebar, render_page_header, render_divider, render_page_footer

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from Helpers.ebkp_reference import load_ebkp_catalog, get_hauptgruppen

# Custom CSS für schönere Tabs
st.markdown("""
<style>
    /* Tab Container */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
        padding: 0.5rem 0;
    }

    /* Einzelne Tabs */
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 0.75rem 1.5rem;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
        border-radius: 0.5rem;
        border: 1px solid rgba(102, 126, 234, 0.2);
        font-weight: 500;
        transition: all 0.2s ease;
    }

    /* Tab Hover */
    .stTabs [data-baseweb="tab"]:hover {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border-color: rgba(102, 126, 234, 0.4);
        transform: translateY(-2px);
    }

    /* Aktiver Tab */
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border-color: transparent !important;
        color: white !important;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }

    /* Tab Panel (Content-Bereich) */
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Seitenkonfiguration
st.set_page_config(
    page_title="eBKP-H Auswertung",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Lade eBKP-H Katalog und Hauptgruppen
ebkp_catalog = load_ebkp_catalog()
EBKP_HAUPTGRUPPEN = get_hauptgruppen(ebkp_catalog)


# Hilfsfunktionen
def extract_bkp_hauptgruppe(bkp_code: str) -> str:
    """Extrahiert Hauptgruppe aus BKP-Code"""
    if pd.isna(bkp_code) or not bkp_code:
        return 'Unbekannt'
    bkp_str = str(bkp_code).strip()
    if bkp_str and bkp_str[0].upper() in EBKP_HAUPTGRUPPEN:
        return bkp_str[0].upper()
    return 'Unbekannt'


def extract_bkp_untergruppe(bkp_code: str) -> str:
    """Extrahiert Untergruppe aus BKP-Code"""
    if pd.isna(bkp_code) or not bkp_code:
        return 'Unbekannt'
    bkp_str = str(bkp_code).strip()
    if '.' in bkp_str:
        return bkp_str.split('.')[0]
    elif len(bkp_str) >= 2:
        return bkp_str[:2]
    return bkp_str


def format_currency(value: float) -> str:
    """Formatiert als CHF"""
    return f"CHF {value:,.2f}".replace(',', "'")


def format_currency_with_tolerance(value: float, tolerance: int = 0) -> str:
    """Formatiert Währung mit Toleranzbereich"""
    formatted = format_currency(value)
    if tolerance > 0:
        tolerance_amount = value * (tolerance / 100)
        min_value = value - tolerance_amount
        max_value = value + tolerance_amount
        return f"{formatted}\n({format_currency(min_value)} - {format_currency(max_value)})"
    return formatted


def aggregate_quantities_by_unit(df: pd.DataFrame) -> str:
    """
    Aggregiert Mengen nach Einheit und formatiert als String.

    Args:
        df: DataFrame mit 'Menge' und 'Einheit' Spalten

    Returns:
        Formatierter String z.B. "45 Stk, 120 m², 5 m"
    """
    if 'Menge' not in df.columns or 'Einheit' not in df.columns:
        return f"{len(df)} Elemente"

    # Gruppiere nach Einheit und summiere Mengen
    quantity_summary = df.groupby('Einheit')['Menge'].sum()

    # Formatiere als Liste
    parts = []
    for einheit, menge in quantity_summary.items():
        if pd.notna(einheit) and pd.notna(menge):
            parts.append(f"{menge:.0f} {einheit}")

    if parts:
        return ", ".join(parts)
    else:
        return f"{len(df)} Elemente"


def render_bkp_hierarchy_markdown(df: pd.DataFrame, hauptgruppe: str) -> str:
    """Generiert Markdown für BKP-Hierarchie mit Summierung"""
    hauptgruppe_df = df[df['BKP_Hauptgruppe'] == hauptgruppe].copy()

    if hauptgruppe_df.empty:
        return f"*Keine Daten für Hauptgruppe {hauptgruppe}*"

    markdown = []

    # Hauptgruppen-Total
    hauptgruppe_name = EBKP_HAUPTGRUPPEN.get(hauptgruppe, hauptgruppe)
    if 'Kosten' in hauptgruppe_df.columns:
        hg_total = hauptgruppe_df['Kosten'].sum()
        markdown.append(f"# {hauptgruppe} - {hauptgruppe_name} ({format_currency(hg_total)})\n")
    elif 'Fläche (m²)' in hauptgruppe_df.columns or 'Fläche' in hauptgruppe_df.columns:
        flaeche_col = 'Fläche (m²)' if 'Fläche (m²)' in hauptgruppe_df.columns else 'Fläche'
        hg_total = hauptgruppe_df[flaeche_col].sum()
        markdown.append(f"# {hauptgruppe} - {hauptgruppe_name} ({hg_total:,.2f} m²)\n")
    else:
        markdown.append(f"# {hauptgruppe} - {hauptgruppe_name} ({len(hauptgruppe_df)} Elemente)\n")

    # Gruppiere nach Untergruppe
    untergruppen = hauptgruppe_df.groupby('BKP_Untergruppe')

    for untergruppe, ug_df in untergruppen:
        # Untergruppen-Total
        if 'Kosten' in ug_df.columns:
            ug_total = ug_df['Kosten'].sum()
            markdown.append(f"\n## {untergruppe} ({format_currency(ug_total)})")
        elif 'Fläche (m²)' in ug_df.columns or 'Fläche' in ug_df.columns:
            flaeche_col = 'Fläche (m²)' if 'Fläche (m²)' in ug_df.columns else 'Fläche'
            ug_total = ug_df[flaeche_col].sum()
            markdown.append(f"\n## {untergruppe} ({ug_total:,.2f} m²)")
        else:
            markdown.append(f"\n## {untergruppe} ({len(ug_df)} Elemente)")

        # Codes mit Beschreibung
        if 'BKP_Beschreibung' in ug_df.columns:
            beschreibungen = ug_df.groupby(['BKP_Code', 'BKP_Beschreibung'])
            for (code, beschr), beschr_df in beschreibungen:
                # Mengen-Aggregation
                quantity_str = aggregate_quantities_by_unit(beschr_df)

                if 'Kosten' in beschr_df.columns:
                    code_total = beschr_df['Kosten'].sum()
                    markdown.append(f"- **{code}**: {beschr} - {format_currency(code_total)} | {quantity_str}")
                elif 'Fläche (m²)' in beschr_df.columns or 'Fläche' in beschr_df.columns:
                    flaeche_col = 'Fläche (m²)' if 'Fläche (m²)' in beschr_df.columns else 'Fläche'
                    code_total = beschr_df[flaeche_col].sum()
                    markdown.append(f"- **{code}**: {beschr} - {code_total:,.2f} m² | {quantity_str}")
                else:
                    markdown.append(f"- **{code}**: {beschr} - {quantity_str}")
        else:
            codes = ug_df['BKP_Code'].value_counts()
            for code, count in codes.items():
                markdown.append(f"- **{code}**: {count} Elemente")

    return "\n".join(markdown)


def display_bkp_hierarchy(df: pd.DataFrame, hauptgruppe: str):
    """Zeigt BKP-Hierarchie für eine Hauptgruppe als Markdown"""
    markdown_output = render_bkp_hierarchy_markdown(df, hauptgruppe)
    st.markdown(markdown_output)

    # Optional: Details-Tabelle als Expander
    hauptgruppe_df = df[df['BKP_Hauptgruppe'] == hauptgruppe].copy()
    if not hauptgruppe_df.empty:
        with st.expander("📋 Detaildaten anzeigen", expanded=False):
            st.dataframe(hauptgruppe_df, width='stretch', height=300)


def generate_hierarchy_pdf(df: pd.DataFrame, ebkp_catalog: dict, hauptgruppen: dict) -> BytesIO:
    """Generiert PDF mit vollständig ausgeklappter eBKP-Hierarchie"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except ImportError:
        st.error("reportlab ist nicht installiert. Bitte führen Sie 'pip install reportlab' aus.")
        return None

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    story = []
    styles = getSampleStyleSheet()

    # Custom Styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=20,
        textColor=colors.HexColor('#667eea')
    )

    heading1_style = ParagraphStyle(
        'CustomHeading1',
        parent=styles['Heading1'],
        fontSize=14,
        spaceAfter=10,
        textColor=colors.HexColor('#667eea')
    )

    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=8,
        leftIndent=0.5*cm
    )

    heading3_style = ParagraphStyle(
        'CustomHeading3',
        parent=styles['Heading3'],
        fontSize=10,
        spaceAfter=6,
        leftIndent=1*cm
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=9,
        leftIndent=1.5*cm,
        spaceAfter=4
    )

    # Titel und Datum
    story.append(Paragraph("eBKP-H Kostenauswertung", title_style))
    story.append(Paragraph(f"Erstellt am: {datetime.now().strftime('%d.%m.%Y %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))

    # Zusammenfassung
    has_costs = 'Kosten' in df.columns
    has_area = 'Fläche (m²)' in df.columns or 'Fläche' in df.columns

    summary_data = [
        ['Gesamt Elemente:', str(len(df))],
        ['Hauptgruppen:', str(df['BKP_Hauptgruppe'].nunique())],
        ['Untergruppen:', str(df['BKP_Untergruppe'].nunique())]
    ]

    if has_costs:
        total_kosten = df['Kosten'].sum()
        summary_data.append(['Gesamtkosten:', format_currency(total_kosten)])
    elif has_area:
        flaeche_col = 'Fläche (m²)' if 'Fläche (m²)' in df.columns else 'Fläche'
        total_flaeche = df[flaeche_col].sum()
        summary_data.append(['Gesamtfläche:', f"{total_flaeche:,.2f} m²".replace(',', "'")])

    summary_table = Table(summary_data, colWidths=[5*cm, 10*cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))

    story.append(summary_table)
    story.append(Spacer(1, 0.8*cm))
    story.append(PageBreak())

    # Hierarchie generieren
    hauptgruppen_sorted = sorted([hg for hg in df['BKP_Hauptgruppe'].unique() if hg != 'Unbekannt'])

    for hauptgruppe in hauptgruppen_sorted:
        hauptgruppe_name = hauptgruppen.get(hauptgruppe, 'Unbekannt')
        hauptgruppe_df = df[df['BKP_Hauptgruppe'] == hauptgruppe].copy()

        # Level 1: Hauptgruppe
        if has_costs:
            hg_total = hauptgruppe_df['Kosten'].sum()
            hg_summary = f"{format_currency(hg_total)} ({len(hauptgruppe_df)} Elemente)"
        elif has_area:
            flaeche_col = 'Fläche (m²)' if 'Fläche (m²)' in df.columns else 'Fläche'
            hg_total = hauptgruppe_df[flaeche_col].sum()
            hg_summary = f"{hg_total:,.1f} m² ({len(hauptgruppe_df)} Elemente)".replace(',', "'")
        else:
            hg_summary = f"{len(hauptgruppe_df)} Elemente"

        story.append(Paragraph(f"<b>{hauptgruppe}</b> - {hauptgruppe_name}", heading1_style))
        story.append(Paragraph(hg_summary, styles['Normal']))
        story.append(Spacer(1, 0.3*cm))

        # Gruppiere nach Level 2
        hauptgruppe_df['BKP_Level2'] = hauptgruppe_df['BKP_Code'].apply(
            lambda x: str(x)[:3] if pd.notna(x) and len(str(x)) >= 3 else str(x)
        )

        level2_groups = hauptgruppe_df.groupby('BKP_Level2')

        for level2_code, level2_df in sorted(level2_groups):
            # Level 2: Untergruppe
            if has_costs:
                level2_total = level2_df['Kosten'].sum()
                level2_summary = f"{format_currency(level2_total)} | {len(level2_df)} Elemente"
            elif has_area:
                level2_total = level2_df[flaeche_col].sum()
                level2_summary = f"{level2_total:,.1f} m² | {len(level2_df)} Elemente".replace(',', "'")
            else:
                level2_summary = f"{len(level2_df)} Elemente"

            level2_desc = ebkp_catalog.get(level2_code, {}).get('name', level2_code)

            story.append(Paragraph(f"<b>{level2_code}</b> - {level2_desc}", heading2_style))
            story.append(Paragraph(level2_summary, ParagraphStyle('level2sum', parent=styles['Normal'], leftIndent=0.5*cm, fontSize=9)))
            story.append(Spacer(1, 0.2*cm))

            # Gruppiere nach Level 3
            level2_df['BKP_Level3'] = level2_df['BKP_Code'].apply(
                lambda x: str(x).split('.')[0] + '.' + str(x).split('.')[1][:2] if '.' in str(x) and len(str(x).split('.')) > 1 else str(x)
            )

            level3_groups = level2_df.groupby('BKP_Level3')

            for level3_code, level3_df in sorted(level3_groups):
                # Level 3: Detail-Gruppe
                if has_costs:
                    level3_total = level3_df['Kosten'].sum()
                    level3_summary = f"{format_currency(level3_total)} | {len(level3_df)} Elemente"
                elif has_area:
                    level3_total = level3_df[flaeche_col].sum()
                    level3_summary = f"{level3_total:,.1f} m² | {len(level3_df)} Elemente".replace(',', "'")
                else:
                    level3_summary = f"{len(level3_df)} Elemente"

                level3_desc = ebkp_catalog.get(level3_code, {}).get('name', level3_code)

                story.append(Paragraph(f"<b>{level3_code}</b> - {level3_desc}", heading3_style))
                story.append(Paragraph(level3_summary, ParagraphStyle('level3sum', parent=styles['Normal'], leftIndent=1*cm, fontSize=8)))
                story.append(Spacer(1, 0.1*cm))

                # Level 4: Einzelne Codes
                if 'BKP_Beschreibung' in level3_df.columns:
                    code_groups = level3_df.groupby(['BKP_Code', 'BKP_Beschreibung'])

                    for (code, beschr), code_df in sorted(code_groups):
                        if has_costs:
                            code_total = code_df['Kosten'].sum()
                            code_summary = f"{format_currency(code_total)}"
                        elif has_area:
                            code_total = code_df[flaeche_col].sum()
                            code_summary = f"{code_total:,.1f} m²".replace(',', "'")
                        else:
                            code_summary = f"{len(code_df)} Stk."

                        story.append(Paragraph(f"• <b>{code}</b>: {beschr} - {code_summary}", body_style))
                else:
                    code_counts = level3_df['BKP_Code'].value_counts()
                    for code, count in sorted(code_counts.items()):
                        story.append(Paragraph(f"• <b>{code}</b>: {count} Elemente", body_style))

                story.append(Spacer(1, 0.2*cm))

            story.append(Spacer(1, 0.3*cm))

        story.append(PageBreak())

    # PDF generieren
    doc.build(story)
    buffer.seek(0)
    return buffer


# Render gemeinsame Sidebar
render_sidebar()

# Page Header
render_page_header("📊 eBKP-H Auswertung", "Hierarchische Kostenvisualisierung")

# Stylesheet
st.markdown("""
<style>
    .metric-card {
        padding: 1rem;
        border-radius: 0.5rem;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border-left: 4px solid #667eea;
    }
</style>
""", unsafe_allow_html=True)

# Kostenermittlungs-Status
if 'cost_estimation_config' in st.session_state and st.session_state.cost_estimation_config.get('selected'):
    config = st.session_state.cost_estimation_config

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📐 Ermittlungsart", config['name'].split()[0])
    with col2:
        st.metric("⚖️ Toleranz", format_tolerance(config['tolerance']))
    with col3:
        st.metric("🏗️ Phase", config['project_phase'])
    with col4:
        st.metric("📊 eBKP-Tiefe", config['ebkp_depth'].replace(' eBKP', ''))

render_divider("section")

# Daten-Upload oder Auto-Load
auto_load = 'classification_results' in st.session_state and st.session_state.classification_results is not None

if auto_load:
    st.success("✅ Daten aus KI-Klassifizierung geladen", icon="🤖")

col1, col2 = st.columns([3, 1])

with col1:
    if auto_load:
        data_source = st.radio(
            "Datenquelle",
            ["🤖 KI-Klassifizierung", "📁 Datei hochladen"],
            horizontal=True
        )
        use_auto = (data_source == "🤖 KI-Klassifizierung")
    else:
        use_auto = False
        st.info("Laden Sie eine CSV-Datei hoch")

with col2:
    if not auto_load or data_source == "📁 Datei hochladen":
        uploaded_file = st.file_uploader("CSV-Datei", type=['csv'], label_visibility="collapsed")
    else:
        uploaded_file = None

render_divider("section")

# Daten laden
df = None

if use_auto:
    df = st.session_state.classification_results.copy()
    st.caption(f"📊 {len(df)} Elemente geladen")

elif uploaded_file:
    try:
        try:
            df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8-sig')
        except:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, encoding='utf-8-sig')

        if 'BKP_Code' not in df.columns:
            st.error("❌ Spalte 'BKP_Code' fehlt!")
            st.stop()

        df_original = len(df)
        df = df[df['BKP_Code'].notna()].copy()

        if len(df) == 0:
            st.error("❌ Keine gültigen BKP-Codes!")
            st.stop()

        if len(df) < df_original:
            st.warning(f"⚠️ {df_original - len(df)} Zeilen ohne BKP-Code entfernt")

        st.success(f"✅ {len(df)} Elemente geladen")

    except Exception as e:
        st.error(f"❌ Fehler beim Laden: {str(e)}")
        st.stop()

# Verarbeitung wenn Daten vorhanden
if df is not None:
    # BKP-Spalten hinzufügen
    df['BKP_Hauptgruppe'] = df['BKP_Code'].apply(extract_bkp_hauptgruppe)
    df['BKP_Untergruppe'] = df['BKP_Code'].apply(extract_bkp_untergruppe)

    # Übersicht
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Gesamt Elemente", len(df))
    with col2:
        st.metric("Hauptgruppen", df['BKP_Hauptgruppe'].nunique())
    with col3:
        st.metric("Untergruppen", df['BKP_Untergruppe'].nunique())
    with col4:
        if 'Kosten' in df.columns:
            total_kosten = df['Kosten'].sum()
            st.metric("Gesamtkosten", format_currency(total_kosten))
        elif 'Fläche (m²)' in df.columns or 'Fläche' in df.columns:
            flaeche_col = 'Fläche (m²)' if 'Fläche (m²)' in df.columns else 'Fläche'
            total_flaeche = df[flaeche_col].sum()
            st.metric("Gesamtfläche", f"{total_flaeche:,.2f} m²".replace(',', "'"))

    render_divider("section")

    # Visualisierung
    tab1, tab2, tab3 = st.tabs(["📊 Hierarchie", "📈 Diagramme", "📄 Export"])

    with tab1:
        # === TOP SECTION: Übersicht aller Hauptgruppen ===
        st.subheader("📋 Übersicht Hauptgruppen")

        # Gruppiere Daten nach Hauptgruppe
        hauptgruppen_summary = df.groupby('BKP_Hauptgruppe').agg({
            'BKP_Code': 'count'
        }).rename(columns={'BKP_Code': 'Anzahl'})

        # Füge Kosten/Fläche hinzu, falls vorhanden
        has_costs = 'Kosten' in df.columns
        has_area = 'Fläche (m²)' in df.columns or 'Fläche' in df.columns

        if has_costs:
            hauptgruppen_summary['Kosten'] = df.groupby('BKP_Hauptgruppe')['Kosten'].sum()
        elif has_area:
            flaeche_col = 'Fläche (m²)' if 'Fläche (m²)' in df.columns else 'Fläche'
            hauptgruppen_summary['Fläche'] = df.groupby('BKP_Hauptgruppe')[flaeche_col].sum()

        hauptgruppen_summary = hauptgruppen_summary.reset_index()
        hauptgruppen_summary = hauptgruppen_summary[hauptgruppen_summary['BKP_Hauptgruppe'] != 'Unbekannt']
        hauptgruppen_summary = hauptgruppen_summary.sort_values('BKP_Hauptgruppe')

        # Zeige Karten in 4-Spalten-Layout
        num_groups = len(hauptgruppen_summary)
        cols_per_row = 4

        for i in range(0, num_groups, cols_per_row):
            cols = st.columns(cols_per_row)

            for j in range(cols_per_row):
                if i + j < num_groups:
                    row_data = hauptgruppen_summary.iloc[i + j]
                    hauptgruppe = row_data['BKP_Hauptgruppe']
                    hauptgruppe_name = EBKP_HAUPTGRUPPEN.get(hauptgruppe, 'Unbekannt')
                    anzahl = row_data['Anzahl']

                    with cols[j]:
                        # Berechne Wert für Metrik
                        if has_costs:
                            value = format_currency(row_data['Kosten'])
                            delta_label = f"{anzahl} Elemente"
                        elif has_area:
                            value = f"{row_data['Fläche']:,.1f} m²".replace(',', "'")
                            delta_label = f"{anzahl} Elemente"
                        else:
                            value = f"{anzahl}"
                            delta_label = "Elemente"

                        st.metric(
                            label=f"{hauptgruppe} - {hauptgruppe_name}",
                            value=value,
                            delta=delta_label
                        )

        render_divider("section")

        # === MIDDLE SECTION: Aggregierte Element-Übersicht ===
        st.subheader("📊 Aggregierte Element-Übersicht")

        # Prüfe, ob Menge und Einheit vorhanden sind
        if 'Menge' in df.columns and 'Einheit' in df.columns and 'BKP_Code' in df.columns and 'BKP_Beschreibung' in df.columns:
            # Aggregiere nach BKP-Code und Einheit
            aggregated = df.groupby(['BKP_Code', 'BKP_Beschreibung', 'Einheit']).agg({
                'Menge': 'sum'
            }).reset_index()

            # Sortiere nach BKP-Code
            aggregated = aggregated.sort_values('BKP_Code')

            # Formatiere Menge mit Einheit
            aggregated['Stückzahl/Menge'] = aggregated.apply(
                lambda row: f"{row['Menge']:.0f} {row['Einheit']}" if pd.notna(row['Einheit']) and row['Einheit'] != '' else f"{row['Menge']:.0f}",
                axis=1
            )

            # Zeige Tabelle
            st.dataframe(
                aggregated[['BKP_Code', 'BKP_Beschreibung', 'Stückzahl/Menge']],
                column_config={
                    'BKP_Code': st.column_config.TextColumn('BKP-Code', width='small'),
                    'BKP_Beschreibung': st.column_config.TextColumn('Beschreibung', width='large'),
                    'Stückzahl/Menge': st.column_config.TextColumn('Stückzahl/Menge', width='medium')
                },
                hide_index=True,
                width="stretch"
            )
        else:
            st.info("💡 Für eine aggregierte Mengen-Übersicht werden die Spalten 'Menge' und 'Einheit' benötigt.")

        render_divider("section")

        # === BOTTOM SECTION: Detaillierte Hierarchie ===
        st.subheader("🔍 Detaillierte Hierarchie")

        # Sortiere Hauptgruppen
        hauptgruppen_sorted = sorted([hg for hg in df['BKP_Hauptgruppe'].unique() if hg != 'Unbekannt'])

        for hauptgruppe in hauptgruppen_sorted:
            hauptgruppe_name = EBKP_HAUPTGRUPPEN.get(hauptgruppe, 'Unbekannt')
            hauptgruppe_df = df[df['BKP_Hauptgruppe'] == hauptgruppe].copy()

            # Berechne Hauptgruppen-Total
            # Mengen-Aggregation
            hg_quantity_str = aggregate_quantities_by_unit(hauptgruppe_df)

            if has_costs:
                hg_total = hauptgruppe_df['Kosten'].sum()
                hg_summary = f"{format_currency(hg_total)} | {hg_quantity_str}"
            elif has_area:
                flaeche_col = 'Fläche (m²)' if 'Fläche (m²)' in df.columns else 'Fläche'
                hg_total = hauptgruppe_df[flaeche_col].sum()
                hg_summary = f"{hg_total:,.1f} m² | {hg_quantity_str}".replace(',', "'")
            else:
                hg_summary = hg_quantity_str

            # LEVEL 1: Hauptgruppen-Expander
            with st.expander(f"**{hauptgruppe}** - {hauptgruppe_name} | {hg_summary}", expanded=False):

                # Gruppiere nach 3-stelligem Code (z.B. B03)
                hauptgruppe_df['BKP_Level2'] = hauptgruppe_df['BKP_Code'].apply(
                    lambda x: str(x)[:3] if pd.notna(x) and len(str(x)) >= 3 else str(x)
                )

                level2_groups = hauptgruppe_df.groupby('BKP_Level2')

                for level2_code, level2_df in sorted(level2_groups):
                    # LEVEL 2: Untergruppen-Überschrift (z.B. B03)
                    # Mengen-Aggregation
                    level2_quantity_str = aggregate_quantities_by_unit(level2_df)

                    if has_costs:
                        level2_total = level2_df['Kosten'].sum()
                        level2_summary = f"{format_currency(level2_total)} | {level2_quantity_str}"
                    elif has_area:
                        level2_total = level2_df[flaeche_col].sum()
                        level2_summary = f"{level2_total:,.1f} m² | {level2_quantity_str}".replace(',', "'")
                    else:
                        level2_summary = level2_quantity_str

                    # Hole Beschreibung für Level 2 aus Katalog
                    level2_desc = ebkp_catalog.get(level2_code, {}).get('name', level2_code)

                    st.markdown(f"### {level2_code} - {level2_desc}")
                    st.caption(level2_summary)

                    # Gruppiere nach 5-stelligem Code (z.B. B03.02)
                    level2_df['BKP_Level3'] = level2_df['BKP_Code'].apply(
                        lambda x: str(x).split('.')[0] + '.' + str(x).split('.')[1][:2] if '.' in str(x) and len(str(x).split('.')) > 1 else str(x)
                    )

                    level3_groups = level2_df.groupby('BKP_Level3')

                    for level3_code, level3_df in sorted(level3_groups):
                        # LEVEL 3: Detail-Gruppen-Expander (z.B. B03.02)
                        # Mengen-Aggregation
                        level3_quantity_str = aggregate_quantities_by_unit(level3_df)

                        if has_costs:
                            level3_total = level3_df['Kosten'].sum()
                            level3_summary = f"{format_currency(level3_total)} | {level3_quantity_str}"
                        elif has_area:
                            level3_total = level3_df[flaeche_col].sum()
                            level3_summary = f"{level3_total:,.1f} m² | {level3_quantity_str}".replace(',', "'")
                        else:
                            level3_summary = level3_quantity_str

                        # Hole Beschreibung für Level 3 aus Katalog
                        level3_desc = ebkp_catalog.get(level3_code, {}).get('name', level3_code)

                        with st.expander(f"**{level3_code}** - {level3_desc} | {level3_summary}", expanded=False):
                            # LEVEL 4: Einzelne Codes (z.B. B03.02.005)
                            if 'BKP_Beschreibung' in level3_df.columns:
                                code_groups = level3_df.groupby(['BKP_Code', 'BKP_Beschreibung'])

                                for (code, beschr), code_df in sorted(code_groups):
                                    # Mengen-Aggregation
                                    code_quantity_str = aggregate_quantities_by_unit(code_df)

                                    if has_costs:
                                        code_total = code_df['Kosten'].sum()
                                        code_summary = f"{format_currency(code_total)} | {code_quantity_str}"
                                    elif has_area:
                                        code_total = code_df[flaeche_col].sum()
                                        code_summary = f"{code_total:,.1f} m² | {code_quantity_str}".replace(',', "'")
                                    else:
                                        code_summary = code_quantity_str

                                    st.markdown(f"- **{code}**: {beschr} - {code_summary}")
                            else:
                                # Fallback ohne Beschreibung
                                code_counts = level3_df['BKP_Code'].value_counts()
                                for code, count in sorted(code_counts.items()):
                                    st.markdown(f"- **{code}**: {count} Elemente")

                            # Zeige optionale Datentabelle
                            with st.expander("📋 Detaildaten", expanded=False):
                                st.dataframe(level3_df, width='stretch', height=200)

    with tab2:
        # Diagramme
        st.subheader("Verteilung nach Hauptgruppen")

        hauptgruppen_summary = df.groupby('BKP_Hauptgruppe').size().reset_index(name='Anzahl')
        hauptgruppen_summary = hauptgruppen_summary[hauptgruppen_summary['BKP_Hauptgruppe'] != 'Unbekannt']

        if not hauptgruppen_summary.empty:
            col1, col2 = st.columns(2)

            with col1:
                fig_pie = px.pie(
                    hauptgruppen_summary,
                    values='Anzahl',
                    names='BKP_Hauptgruppe',
                    title="Verteilung nach Hauptgruppen"
                )
                st.plotly_chart(fig_pie, width='stretch')

            with col2:
                fig_bar = px.bar(
                    hauptgruppen_summary,
                    x='BKP_Hauptgruppe',
                    y='Anzahl',
                    title="Anzahl Elemente pro Hauptgruppe"
                )
                st.plotly_chart(fig_bar, width='stretch')

        # Kosten-Diagramme (falls vorhanden)
        if 'Kosten' in df.columns:
            st.subheader("Kostenverteilung")

            kosten_summary = df.groupby('BKP_Hauptgruppe')['Kosten'].sum().reset_index()
            kosten_summary = kosten_summary[kosten_summary['BKP_Hauptgruppe'] != 'Unbekannt']

            if not kosten_summary.empty:
                fig_kosten = px.bar(
                    kosten_summary,
                    x='BKP_Hauptgruppe',
                    y='Kosten',
                    title="Kosten nach Hauptgruppen"
                )
                st.plotly_chart(fig_kosten, width='stretch')

    with tab3:
        # Export
        st.subheader("Daten exportieren")

        col1, col2, col3 = st.columns(3)

        with col1:
            # CSV Export
            csv = df.to_csv(index=False, sep=';', encoding='utf-8-sig')
            st.download_button(
                label="📥 CSV herunterladen",
                data=csv,
                file_name=f"eBKP_Auswertung_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                width='stretch'
            )

        with col2:
            # Excel Export
            try:
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Auswertung')

                    # Zusammenfassung
                    summary_df = df.groupby('BKP_Hauptgruppe').agg({
                        'BKP_Code': 'count'
                    }).rename(columns={'BKP_Code': 'Anzahl'})

                    if 'Kosten' in df.columns:
                        summary_df['Kosten'] = df.groupby('BKP_Hauptgruppe')['Kosten'].sum()

                    summary_df.to_excel(writer, sheet_name='Zusammenfassung')

                excel_data = output.getvalue()

                st.download_button(
                    label="📥 Excel herunterladen",
                    data=excel_data,
                    file_name=f"eBKP_Auswertung_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    width='stretch'
                )
            except ImportError:
                st.info("Excel-Export erfordert openpyxl")

        with col3:
            # PDF Export mit vollständiger Hierarchie
            if st.button("📄 PDF generieren", type="secondary", width="stretch"):
                with st.spinner("PDF wird erstellt..."):
                    pdf_buffer = generate_hierarchy_pdf(df, ebkp_catalog, EBKP_HAUPTGRUPPEN)

                    if pdf_buffer:
                        st.download_button(
                            label="📥 PDF herunterladen",
                            data=pdf_buffer,
                            file_name=f"eBKP_Hierarchie_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf",
                            width="stretch"
                        )
                        st.success("✅ PDF erfolgreich generiert!")
                    else:
                        st.error("❌ PDF konnte nicht generiert werden")

        render_divider("section")

        # Vollständige Datentabelle
        st.subheader("Vollständige Daten")
        st.dataframe(df, width='stretch', height=400)

else:
    # Keine Daten geladen
    st.info("👈 Laden Sie eine CSV-Datei hoch oder nutzen Sie die KI-Klassifizierung")

    with st.expander("ℹ️ Anforderungen an CSV-Datei"):
        st.markdown("""
        **Erforderliche Spalten:**
        - `BKP_Code`: BKP-Klassifizierungscode (z.B. C13, D31)

        **Optionale Spalten:**
        - `BKP_Beschreibung`: Beschreibung des BKP-Codes
        - `Kosten`: Kosten in CHF
        - `Fläche (m²)` oder `Fläche`: Fläche in Quadratmetern
        - Weitere Spalten werden automatisch angezeigt
        """)


# Footer
render_page_footer()
