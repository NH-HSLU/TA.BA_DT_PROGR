import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Elektro BKP Analyse", layout="wide")

st.title("🔌 Elektro-Komponenten Analyse nach BKP")

# File Upload
uploaded_file = st.file_uploader("CSV-Datei hochladen", type=['csv'])

if uploaded_file:
    # CSV einlesen
    df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8-sig')
    
    # Sidebar Filter
    st.sidebar.header("Filter")
    
    # BKP Filter
    bkp_codes = ['Alle'] + sorted(df['BKP_Code'].unique().tolist())
    selected_bkp = st.sidebar.selectbox("BKP Code", bkp_codes)
    
    # Kategorie Filter
    categories = ['Alle'] + sorted(df['Kategorie'].unique().tolist())
    selected_category = st.sidebar.selectbox("Kategorie", categories)
    
    # Filter anwenden
    filtered_df = df.copy()
    if selected_bkp != 'Alle':
        filtered_df = filtered_df[filtered_df['BKP_Code'] == selected_bkp]
    if selected_category != 'Alle':
        filtered_df = filtered_df[filtered_df['Kategorie'] == selected_category]
    
    # Metriken
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Gesamt Elemente", len(filtered_df))
    with col2:
        st.metric("Anzahl Räume", filtered_df['Raum_Nummer'].nunique())
    with col3:
        st.metric("Anzahl BKP Codes", filtered_df['BKP_Code'].nunique())
    with col4:
        st.metric("Anzahl Kategorien", filtered_df['Kategorie'].nunique())
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Verteilung nach BKP")
        bkp_counts = filtered_df['BKP_Code'].value_counts().reset_index()
        bkp_counts.columns = ['BKP_Code', 'Anzahl']
        fig1 = px.bar(bkp_counts, x='BKP_Code', y='Anzahl', 
                     color='Anzahl', color_continuous_scale='Blues')
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        st.subheader("🔧 Verteilung nach Kategorie")
        cat_counts = filtered_df['Kategorie'].value_counts().reset_index()
        cat_counts.columns = ['Kategorie', 'Anzahl']
        fig2 = px.pie(cat_counts, values='Anzahl', names='Kategorie')
        st.plotly_chart(fig2, use_container_width=True)
    
    # BKP Beschreibung Chart
    st.subheader("📋 Übersicht nach BKP Beschreibung")
    bkp_desc_counts = filtered_df.groupby(['BKP_Beschreibung', 'BKP_Code']).size().reset_index(name='Anzahl')
    fig3 = px.treemap(bkp_desc_counts, path=['BKP_Beschreibung', 'BKP_Code'], 
                     values='Anzahl', color='Anzahl', color_continuous_scale='Viridis')
    st.plotly_chart(fig3, use_container_width=True)
    
    # Top Räume
    st.subheader("🏠 Top 10 Räume mit meisten Komponenten")
    room_counts = filtered_df.groupby(['Raum_Nummer', 'Raum_Name']).size().reset_index(name='Anzahl')
    room_counts = room_counts.sort_values('Anzahl', ascending=False).head(10)
    fig4 = px.bar(room_counts, x='Raum_Nummer', y='Anzahl', 
                 hover_data=['Raum_Name'], color='Anzahl')
    st.plotly_chart(fig4, use_container_width=True)
    
    # Detaillierte Tabelle
    st.subheader("📑 Detaillierte Elementliste")
    st.dataframe(filtered_df, use_container_width=True)
    
    # Download gefilterte Daten
    csv_download = filtered_df.to_csv(index=False, sep=';', encoding='utf-8-sig')
    st.download_button(
        label="📥 Gefilterte Daten herunterladen",
        data=csv_download,
        file_name="elektro_filtered.csv",
        mime="text/csv"
    )

else:
    st.info("Bitte laden Sie eine CSV-Datei hoch, um zu beginnen.")
    
    # Anleitung
    with st.expander("📖 Anleitung"):
        st.markdown("""
        ### So verwenden Sie diese App:
        
        1. **CSV exportieren**: Führen Sie das pyRevit Script in Revit aus
        2. **CSV hochladen**: Laden Sie die exportierte CSV-Datei hier hoch
        3. **Filtern**: Verwenden Sie die Sidebar-Filter für spezifische Analysen
        4. **Analysieren**: Betrachten Sie die verschiedenen Charts und Tabellen
        5. **Exportieren**: Laden Sie gefilterte Daten herunter
        
        ### BKP Codes (Auszug):
        - **230**: Gebäudetechnik
        - **235**: Elektroanlagen
        - **235.1**: Stromversorgung
        - **235.2**: Beleuchtung
        - **235.3**: Kommunikation
        - **235.4**: Sicherheit
        """)
