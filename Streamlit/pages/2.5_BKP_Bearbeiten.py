'''
BKP-Bearbeitungsseite
Ermöglicht manuelle Korrekturen der KI-klassifizierten BKP-Codes
'''

import streamlit as st
import pandas as pd
import re
from datetime import datetime

# Seitenkonfiguration
st.set_page_config(
    page_title="BKP Bearbeiten",
    page_icon="✏️",
    layout="wide"
)

# Bekannte BKP-Codes für Validierung (Auszug)
VALID_BKP_CODES = {
    'C': 'Elektroinstallationen',
    'C1': 'Starkstrom',
    'C11': 'Starkstromhauptverteilung',
    'C12': 'Installationsverteilungen',
    'C13': 'Steckdosen',
    'C14': 'Leuchten',
    'C15': 'Sicherheitsbeleuchtung',
    'C2': 'Schwachstrom',
    'C21': 'Telefon/Daten',
    'C22': 'Alarm/Sicherheit',
    'D': 'Heizung/Lüftung/Klima/Sanitär',
    'D1': 'Heizung',
    'D2': 'Lüftung/Klima',
    'D3': 'Sanitär',
    'D31': 'Kalt-/Warmwasser',
    'D32': 'Abwasser',
    'E': 'Bauwerk - Rohbau',
    'E1': 'Fundament',
    'E2': 'Wände/Stützen',
    'E21': 'Tragende Wände',
    'E22': 'Trennwände',
    'E3': 'Decken',
    'F': 'Bauwerk - Technik',
    'F1': 'Fenster/Fenstertüren',
    'F2': 'Aussentüren',
    'F3': 'Innentüren',
    'G': 'Baunebenkosten'
}


def validate_bkp_code(code: str) -> dict:
    """
    Validiert einen BKP-Code

    Returns:
        dict mit 'valid', 'message', 'known_code'
    """
    if not code or pd.isna(code):
        return {'valid': False, 'message': 'Leer', 'known_code': False}

    code = str(code).strip().upper()

    # Prüfe Format: Muss mit C/D/E/F/G beginnen
    if not re.match(r'^[CDEFG]', code):
        return {'valid': False, 'message': 'Muss mit C/D/E/F/G beginnen', 'known_code': False}

    # Prüfe ob Code bekannt ist
    if code in VALID_BKP_CODES:
        return {'valid': True, 'message': VALID_BKP_CODES[code], 'known_code': True}

    # Code hat gültiges Format, ist aber nicht in der Liste
    return {'valid': True, 'message': 'Format OK, Code unbekannt', 'known_code': False}


# Haupttitel
st.title("✏️ BKP-Codes Bearbeiten")
st.markdown("Überprüfen und korrigieren Sie die KI-Klassifizierung vor der Auswertung")
st.markdown("---")

# Prüfe ob Daten vorhanden sind
if 'classification_results' not in st.session_state or st.session_state.classification_results is None:
    st.warning("⚠️ Keine klassifizierten Daten vorhanden!")
    st.info("""
    **So geht's:**
    1. Gehen Sie zur Seite **"KI Klassifizierung"**
    2. Laden Sie eine CSV-Datei hoch
    3. Starten Sie die Klassifizierung
    4. Kehren Sie hierher zurück zum Bearbeiten
    """)
    st.stop()

# Daten laden
df = st.session_state.classification_results.copy()

# Statistiken
st.subheader("📊 Übersicht")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Gesamt Elemente", len(df))

with col2:
    avg_conf = df['KI_Konfidenz'].mean()
    st.metric("Ø Konfidenz", f"{avg_conf:.1%}")

with col3:
    if 'Bearbeitet' not in df.columns:
        df['Bearbeitet'] = False
    edited_count = df['Bearbeitet'].sum()
    st.metric("Bearbeitet", edited_count)

with col4:
    unique_codes = df['BKP_Code'].nunique()
    st.metric("Verschiedene Codes", unique_codes)

st.markdown("---")

# Sidebar Filter
with st.sidebar:
    st.header("🔍 Filter")

    # Konfidenz-Filter
    conf_filter = st.radio(
        "Anzeigen:",
        ["Alle Elemente", "Nur niedrige Konfidenz", "Nur Fehler"],
        help="Filtern Sie die Elemente nach Konfidenz"
    )

    if conf_filter == "Nur niedrige Konfidenz":
        conf_threshold = st.slider(
            "Konfidenz-Schwellenwert",
            min_value=0.0,
            max_value=1.0,
            value=0.8,
            step=0.05
        )

    # BKP-Gruppen-Filter
    st.markdown("---")
    st.subheader("BKP-Gruppen")

    show_groups = st.multiselect(
        "Zeige nur:",
        ['C - Elektro', 'D - HLKS', 'E - Rohbau', 'F - Technik', 'G - Nebenkosten', 'Fehler'],
        default=['C - Elektro', 'D - HLKS', 'E - Rohbau', 'F - Technik', 'G - Nebenkosten', 'Fehler']
    )

    st.markdown("---")

    # BKP-Referenz
    with st.expander("📖 BKP-Referenz"):
        st.markdown("""
        **C**: Elektroinstallationen
        - C13: Steckdosen
        - C14: Leuchten
        - C21: Telefon/Daten

        **D**: HLKS
        - D1: Heizung
        - D2: Lüftung/Klima
        - D3: Sanitär

        **E**: Bauwerk - Rohbau
        - E1: Fundament
        - E2: Wände/Stützen
        - E3: Decken

        **F**: Bauwerk - Technik
        - F1: Fenster
        - F2: Aussentüren
        - F3: Innentüren

        **G**: Baunebenkosten
        """)

# Daten filtern
filtered_df = df.copy()

# Filter anwenden
if conf_filter == "Nur niedrige Konfidenz":
    filtered_df = filtered_df[filtered_df['KI_Konfidenz'] < conf_threshold]
    st.info(f"📌 Zeige {len(filtered_df)} Elemente mit Konfidenz < {conf_threshold:.0%}")
elif conf_filter == "Nur Fehler":
    filtered_df = filtered_df[filtered_df['BKP_Code'].isin(['ERROR', 'PARSE_ERROR', 'UNKNOWN'])]
    st.warning(f"⚠️ {len(filtered_df)} Elemente mit Fehlern")

# Gruppen-Filter
if show_groups:
    group_map = {
        'C - Elektro': 'C',
        'D - HLKS': 'D',
        'E - Rohbau': 'E',
        'F - Technik': 'F',
        'G - Nebenkosten': 'G',
        'Fehler': ['ERROR', 'PARSE_ERROR', 'UNKNOWN']
    }

    groups_to_show = []
    for group in show_groups:
        if group == 'Fehler':
            groups_to_show.extend(group_map[group])
        else:
            groups_to_show.append(group_map[group])

    # Filter: BKP_Code startet mit einer der ausgewählten Gruppen
    filtered_df = filtered_df[
        filtered_df['BKP_Code'].apply(
            lambda x: any(str(x).startswith(g) for g in groups_to_show)
        )
    ]

if len(filtered_df) == 0:
    st.info("Keine Elemente entsprechen den Filterkriterien")
    st.stop()

# Bearbeitbare Tabelle
st.subheader("✏️ Elemente bearbeiten")
st.caption(f"Zeige {len(filtered_df)} von {len(df)} Elementen")

# Vorbereitung: Nur relevante Spalten für Editing
edit_columns = ['BKP_Code', 'BKP_Beschreibung', 'KI_Konfidenz']

# Prüfe welche Spalten vorhanden sind
available_cols = [col for col in edit_columns if col in filtered_df.columns]

# Füge Original-Daten-Spalten hinzu (nur zur Ansicht)
display_cols = []
for col in filtered_df.columns:
    if col not in ['BKP_Code', 'BKP_Beschreibung', 'KI_Konfidenz', 'Bearbeitet'] and not col.startswith('Unnamed'):
        display_cols.append(col)

# Spalten für Editor
editor_df = filtered_df[display_cols + available_cols + ['Bearbeitet']].copy()

# Editierbarer DataFrame
edited_df = st.data_editor(
    editor_df,
    column_config={
        "BKP_Code": st.column_config.TextColumn(
            "BKP Code",
            help="Bearbeiten Sie den BKP-Code (z.B. C13, D31, E21)",
            max_chars=10,
            required=True,
            width="small"
        ),
        "BKP_Beschreibung": st.column_config.TextColumn(
            "Beschreibung",
            help="Beschreibung des BKP-Codes",
            width="medium"
        ),
        "KI_Konfidenz": st.column_config.NumberColumn(
            "KI Konfidenz",
            format="%.0%",
            disabled=True,  # Konfidenz nicht editierbar
            width="small"
        ),
        "Bearbeitet": st.column_config.CheckboxColumn(
            "✓",
            help="Markieren Sie bearbeitete Zeilen",
            default=False,
            width="small"
        )
    },
    disabled=display_cols,  # Original-Spalten nicht editierbar
    hide_index=True,
    use_container_width=True,
    num_rows="fixed"
)

# Validierung
st.markdown("---")
st.subheader("🔍 Validierung")

# Validiere alle BKP-Codes
validation_results = []
for idx, row in edited_df.iterrows():
    code = row['BKP_Code']
    validation = validate_bkp_code(code)
    validation_results.append({
        'Index': idx,
        'Code': code,
        'Valid': validation['valid'],
        'Message': validation['message'],
        'Known': validation['known_code']
    })

validation_df = pd.DataFrame(validation_results)

# Zeige Validierungs-Statistik
col1, col2, col3 = st.columns(3)

with col1:
    valid_count = validation_df['Valid'].sum()
    st.metric("✅ Gültige Codes", f"{valid_count}/{len(validation_df)}")

with col2:
    known_count = validation_df['Known'].sum()
    st.metric("📚 Bekannte Codes", f"{known_count}/{len(validation_df)}")

with col3:
    invalid_count = len(validation_df) - valid_count
    if invalid_count > 0:
        st.metric("⚠️ Ungültige Codes", invalid_count, delta_color="inverse")
    else:
        st.success("Alle Codes gültig ✓")

# Zeige ungültige Codes
invalid_codes = validation_df[~validation_df['Valid']]
if not invalid_codes.empty:
    st.warning(f"⚠️ {len(invalid_codes)} ungültige BKP-Codes gefunden")

    for _, row in invalid_codes.iterrows():
        st.error(f"Zeile {row['Index']}: `{row['Code']}` - {row['Message']}")

# Zeige unbekannte aber gültige Codes
unknown_valid = validation_df[validation_df['Valid'] & ~validation_df['Known']]
if not unknown_valid.empty:
    with st.expander(f"ℹ️ {len(unknown_valid)} gültige aber unbekannte Codes"):
        for _, row in unknown_valid.iterrows():
            st.info(f"Zeile {row['Index']}: `{row['Code']}` - {row['Message']}")

# Speichern
st.markdown("---")

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.markdown("### 💾 Änderungen speichern")

    changes_made = not edited_df.equals(editor_df)
    if changes_made:
        st.success("✓ Änderungen erkannt")
    else:
        st.info("Keine Änderungen vorgenommen")

with col2:
    if st.button("💾 Speichern", type="primary", use_container_width=True, disabled=not changes_made):
        # Aktualisiere die Original-Daten
        for idx in filtered_df.index:
            if idx in edited_df.index:
                df.loc[idx, 'BKP_Code'] = edited_df.loc[idx, 'BKP_Code']
                df.loc[idx, 'BKP_Beschreibung'] = edited_df.loc[idx, 'BKP_Beschreibung']
                df.loc[idx, 'Bearbeitet'] = edited_df.loc[idx, 'Bearbeitet']

        # Speichere zurück in Session State
        st.session_state.classification_results = df

        st.success("✅ Änderungen gespeichert!")
        st.balloons()

        # Kurze Pause für User Feedback
        import time
        time.sleep(1)
        st.rerun()

with col3:
    if st.button("↩️ Zurücksetzen", use_container_width=True):
        st.rerun()

# Navigation
st.markdown("---")
st.subheader("➡️ Nächster Schritt")

col1, col2 = st.columns(2)

with col1:
    st.info("""
    **Bearbeitung abgeschlossen?**

    Ihre Daten sind jetzt bereit für die Auswertung!

    → Gehen Sie zur **"eBKP-H Auswertung"**
    """)

with col2:
    # Verwende Streamlit page_link für Dark Mode Kompatibilität
    st.page_link("pages/1_eBKP_Auswertung.py", label="📊 Zur eBKP-H Auswertung", icon="📊")

# Footer-Statistik
st.markdown("---")
st.caption(f"Letzte Bearbeitung: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')} | {len(df)} Elemente geladen")
