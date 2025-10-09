import streamlit as st
import pandas as pd
import os

# Seitenkonfiguration
st.set_page_config(
    page_title="Bauvorausmass - Belagskalkulation",
    page_icon="🏗️",
    layout="wide"
)

st.title("🏗️ Bauvorausmass - Belagskalkulation")
st.markdown("---")

# Sidebar für Upload und Gruppierung
with st.sidebar:
    st.header("📁 CSV Import")
    uploaded_file = st.file_uploader("Raumliste hochladen", type=['csv'])
    
    st.markdown("---")
    st.header("📊 Gruppierung")
    
    grouping_options = st.radio(
        "Daten zusammenfassen nach:",
        ["Keine Gruppierung", "Pro Geschoss", "Pro Nutzungsart", "Pro Wohnung"],
        help="Wählen Sie, wie die Raumdaten gruppiert werden sollen"
    )

# Hauptbereich
if uploaded_file is not None:
    # CSV einlesen
    try:
        df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8-sig')
        st.success(f"✅ CSV erfolgreich geladen: {len(df)} Räume gefunden")
    except Exception as e:
        st.error(f"Fehler beim Laden der CSV: {e}")
        st.stop()
    
    # Zusätzliche Spalten für Belagmaterialien hinzufügen
    if 'Nutzungsart' not in df.columns:
        df['Nutzungsart'] = ''
    if 'Wohnung' not in df.columns:
        df['Wohnung'] = ''
    if 'Bodenbelag' not in df.columns:
        df['Bodenbelag'] = 'Nicht definiert'
    if 'Deckenbelag' not in df.columns:
        df['Deckenbelag'] = 'Nicht definiert'
    if 'Bodenpreis (CHF/m²)' not in df.columns:
        df['Bodenpreis (CHF/m²)'] = 0.0
    if 'Deckenpreis (CHF/m²)' not in df.columns:
        df['Deckenpreis (CHF/m²)'] = 0.0
    
    # Session State für DataFrame
    if 'df_work' not in st.session_state:
        st.session_state.df_work = df.copy()
    
    # Belagmaterial-Optionen
    bodenbelag_optionen = [
        'Nicht definiert',
        'Parkett',
        'Laminat',
        'Fliesen',
        'Naturstein',
        'Teppich',
        'Vinyl',
        'Linoleum',
        'Beton geschliffen',
        'Epoxidharz'
    ]
    
    deckenbelag_optionen = [
        'Nicht definiert',
        'Gipskarton gestrichen',
        'Spanndecke',
        'Akustikdecke',
        'Holzdecke',
        'Sichtbeton',
        'Mineralfaserplatten'
    ]
    
    # Tabs für verschiedene Ansichten
    tab1, tab2, tab3 = st.tabs(["📝 Raumdetails bearbeiten", "📊 Übersicht & Kalkulation", "💾 Export"])
    
    # Tab 1: Einzelraumbearbeitung
    with tab1:
        st.subheader("Beläge und Preise pro Raum definieren")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Raumauswahl
            room_options = [f"{row['Raumnummer']} - {row['Raumname']} ({row['Ebene']})" 
                          for idx, row in st.session_state.df_work.iterrows()]
            selected_room_str = st.selectbox("Raum auswählen:", room_options)
            
            if selected_room_str:
                # Index des ausgewählten Raums finden
                selected_idx = room_options.index(selected_room_str)
                room_data = st.session_state.df_work.iloc[selected_idx]
                
                st.info(f"**Fläche:** {room_data['Fläche (m²)']} m²")
                st.info(f"**Ebene:** {room_data['Ebene']}")
        
        with col2:
            if selected_room_str:
                st.markdown("#### Raumdaten bearbeiten")
                
                col2a, col2b = st.columns(2)
                
                with col2a:
                    # Nutzungsart
                    nutzungsart = st.text_input(
                        "Nutzungsart:",
                        value=st.session_state.df_work.iloc[selected_idx]['Nutzungsart'],
                        key=f"nutzung_{selected_idx}"
                    )
                    
                    # Bodenbelag
                    bodenbelag = st.selectbox(
                        "Bodenbelag:",
                        bodenbelag_optionen,
                        index=bodenbelag_optionen.index(
                            st.session_state.df_work.iloc[selected_idx]['Bodenbelag']
                        ),
                        key=f"boden_{selected_idx}"
                    )
                    
                    # Bodenpreis
                    bodenpreis = st.number_input(
                        "Bodenpreis (CHF/m²):",
                        min_value=0.0,
                        value=float(st.session_state.df_work.iloc[selected_idx]['Bodenpreis (CHF/m²)']),
                        step=10.0,
                        key=f"bodenpreis_{selected_idx}"
                    )
                
                with col2b:
                    # Wohnung
                    wohnung = st.text_input(
                        "Wohnung:",
                        value=st.session_state.df_work.iloc[selected_idx]['Wohnung'],
                        key=f"wohnung_{selected_idx}"
                    )
                    
                    # Deckenbelag
                    deckenbelag = st.selectbox(
                        "Deckenbelag:",
                        deckenbelag_optionen,
                        index=deckenbelag_optionen.index(
                            st.session_state.df_work.iloc[selected_idx]['Deckenbelag']
                        ),
                        key=f"decke_{selected_idx}"
                    )
                    
                    # Deckenpreis
                    deckenpreis = st.number_input(
                        "Deckenpreis (CHF/m²):",
                        min_value=0.0,
                        value=float(st.session_state.df_work.iloc[selected_idx]['Deckenpreis (CHF/m²)']),
                        step=10.0,
                        key=f"deckenpreis_{selected_idx}"
                    )
                
                # Speichern Button
                if st.button("💾 Änderungen speichern", type="primary"):
                    st.session_state.df_work.at[selected_idx, 'Nutzungsart'] = nutzungsart
                    st.session_state.df_work.at[selected_idx, 'Wohnung'] = wohnung
                    st.session_state.df_work.at[selected_idx, 'Bodenbelag'] = bodenbelag
                    st.session_state.df_work.at[selected_idx, 'Deckenbelag'] = deckenbelag
                    st.session_state.df_work.at[selected_idx, 'Bodenpreis (CHF/m²)'] = bodenpreis
                    st.session_state.df_work.at[selected_idx, 'Deckenpreis (CHF/m²)'] = deckenpreis
                    st.success("✅ Änderungen gespeichert!")
                    st.rerun()
    
    # Tab 2: Übersicht und Kalkulation
    with tab2:
        # Berechnete Spalten hinzufügen
        df_calc = st.session_state.df_work.copy()
        df_calc['Bodenkosten (CHF)'] = df_calc['Fläche (m²)'] * df_calc['Bodenpreis (CHF/m²)']
        df_calc['Deckenkosten (CHF)'] = df_calc['Fläche (m²)'] * df_calc['Deckenpreis (CHF/m²)']
        df_calc['Gesamtkosten (CHF)'] = df_calc['Bodenkosten (CHF)'] + df_calc['Deckenkosten (CHF)']
        
        # Gruppierung anwenden
        if grouping_options == "Keine Gruppierung":
            st.subheader("Detailansicht aller Räume")
            st.dataframe(df_calc, use_container_width=True, hide_index=True)
            
            # Gesamtsummen
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Gesamtfläche", f"{df_calc['Fläche (m²)'].sum():.2f} m²")
            col2.metric("Bodenkosten", f"{df_calc['Bodenkosten (CHF)'].sum():,.2f} CHF")
            col3.metric("Deckenkosten", f"{df_calc['Deckenkosten (CHF)'].sum():,.2f} CHF")
            col4.metric("Gesamtkosten", f"{df_calc['Gesamtkosten (CHF)'].sum():,.2f} CHF")
        
        elif grouping_options == "Pro Geschoss":
            st.subheader("Zusammenfassung pro Geschoss")
            grouped = df_calc.groupby('Ebene').agg({
                'Fläche (m²)': 'sum',
                'Bodenkosten (CHF)': 'sum',
                'Deckenkosten (CHF)': 'sum',
                'Gesamtkosten (CHF)': 'sum',
                'Raumnummer': 'count'
            }).rename(columns={'Raumnummer': 'Anzahl Räume'})
            
            st.dataframe(grouped, use_container_width=True)
            
            # Detailansicht
            with st.expander("🔍 Detailansicht anzeigen"):
                st.dataframe(df_calc, use_container_width=True, hide_index=True)
        
        elif grouping_options == "Pro Nutzungsart":
            st.subheader("Zusammenfassung pro Nutzungsart")
            
            # Filter für leere Nutzungsarten
            df_filtered = df_calc[df_calc['Nutzungsart'] != '']
            
            if len(df_filtered) > 0:
                grouped = df_filtered.groupby('Nutzungsart').agg({
                    'Fläche (m²)': 'sum',
                    'Bodenkosten (CHF)': 'sum',
                    'Deckenkosten (CHF)': 'sum',
                    'Gesamtkosten (CHF)': 'sum',
                    'Raumnummer': 'count'
                }).rename(columns={'Raumnummer': 'Anzahl Räume'})
                
                st.dataframe(grouped, use_container_width=True)
            else:
                st.warning("⚠️ Keine Nutzungsarten definiert. Bitte definieren Sie Nutzungsarten in Tab 1.")
            
            # Detailansicht
            with st.expander("🔍 Detailansicht anzeigen"):
                st.dataframe(df_calc, use_container_width=True, hide_index=True)
        
        elif grouping_options == "Pro Wohnung":
            st.subheader("Zusammenfassung pro Wohnung")
            
            # Filter für leere Wohnungen
            df_filtered = df_calc[df_calc['Wohnung'] != '']
            
            if len(df_filtered) > 0:
                grouped = df_filtered.groupby('Wohnung').agg({
                    'Fläche (m²)': 'sum',
                    'Bodenkosten (CHF)': 'sum',
                    'Deckenkosten (CHF)': 'sum',
                    'Gesamtkosten (CHF)': 'sum',
                    'Raumnummer': 'count'
                }).rename(columns={'Raumnummer': 'Anzahl Räume'})
                
                st.dataframe(grouped, use_container_width=True)
            else:
                st.warning("⚠️ Keine Wohnungen definiert. Bitte definieren Sie Wohnungen in Tab 1.")
            
            # Detailansicht
            with st.expander("🔍 Detailansicht anzeigen"):
                st.dataframe(df_calc, use_container_width=True, hide_index=True)
    
    # Tab 3: Export
    with tab3:
        st.subheader("💾 Daten exportieren")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Vorausmass als CSV exportieren")
            
            # CSV Export vorbereiten
            csv_export = df_calc.to_csv(index=False, sep=';', encoding='utf-8-sig')
            
            st.download_button(
                label="📥 CSV herunterladen",
                data=csv_export,
                file_name="vorausmass_kalkulation.csv",
                mime="text/csv",
                type="primary"
            )
        
        with col2:
            st.markdown("#### Zusammenfassung als CSV exportieren")
            
            if grouping_options != "Keine Gruppierung":
                summary_csv = grouped.to_csv(sep=';', encoding='utf-8-sig')
                
                st.download_button(
                    label="📥 Zusammenfassung herunterladen",
                    data=summary_csv,
                    file_name=f"zusammenfassung_{grouping_options.lower().replace(' ', '_')}.csv",
                    mime="text/csv"
                )

else:
    # Anleitung wenn keine Datei hochgeladen
    st.info("👈 Bitte laden Sie eine CSV-Datei in der Sidebar hoch")
    
    st.markdown("""
    ### 📖 Anleitung
    
    1. **CSV hochladen**: Laden Sie die aus Revit exportierte Raumliste hoch
    2. **Raumdetails bearbeiten**: Definieren Sie für jeden Raum:
       - Nutzungsart (z.B. Wohnzimmer, Küche, Bad)
       - Wohnung (z.B. WHG 1.1, WHG 2.3)
       - Bodenbelag und Preis pro m²
       - Deckenbelag und Preis pro m²
    3. **Übersicht ansehen**: Wechseln Sie zur Übersicht und wählen Sie die gewünschte Gruppierung
    4. **Exportieren**: Laden Sie die Kalkulation als CSV herunter
    
    ### 💡 Tipps
    - Die Änderungen werden automatisch gespeichert
    - Nutzen Sie die Gruppierung für schnelle Übersichten
    - Exportieren Sie die Daten für weitere Berechnungen in Excel
    """)

# Footer
st.markdown("---")
st.caption("🏗️ Bauvorausmass-Tool für Bauleiter | Erstellt mit Streamlit")
