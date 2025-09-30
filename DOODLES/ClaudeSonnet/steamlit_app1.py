import streamlit as st
import ifcopenshell
import ifcopenshell.util.element as Element
import pandas as pd
import plotly.express as px
from collections import defaultdict

# Seitenkonfiguration
st.set_page_config(
    page_title="IFC Attributierungs-Checker",
    page_icon="🏗️",
    layout="wide"
)

# Titel und Beschreibung
st.title("🏗️ IFC Attributierungs-Checker")
st.markdown("Diese Anwendung prüft die Vollständigkeit der Attributierung in IFC-Dateien")

# Datei-Upload
uploaded_file = st.file_uploader("IFC-Datei hochladen", type=['ifc'])

def check_required_attributes(element, element_type):
    """Prüft ob erforderliche Attribute vorhanden sind"""
    required_attrs = {
        'IfcWall': ['Name', 'GlobalId', 'OwnerHistory'],
        'IfcDoor': ['Name', 'GlobalId', 'OverallHeight', 'OverallWidth'],
        'IfcWindow': ['Name', 'GlobalId', 'OverallHeight', 'OverallWidth'],
        'IfcSpace': ['Name', 'GlobalId', 'LongName'],
        'IfcSlab': ['Name', 'GlobalId', 'OwnerHistory'],
        'IfcBeam': ['Name', 'GlobalId', 'OwnerHistory'],
        'IfcColumn': ['Name', 'GlobalId', 'OwnerHistory']
    }
    
    missing = []
    required = required_attrs.get(element_type, ['Name', 'GlobalId'])
    
    for attr in required:
        try:
            value = getattr(element, attr, None)
            if value is None or (isinstance(value, str) and value.strip() == ''):
                missing.append(attr)
        except:
            missing.append(attr)
    
    return missing

def check_property_sets(ifc_file, element):
    """Prüft ob Property Sets vorhanden sind"""
    psets = Element.get_psets(element)
    return len(psets) > 1  # Mehr als nur das Standard-Set

def analyze_ifc_file(ifc_file):
    """Analysiert die IFC-Datei auf Attributierungsvollständigkeit"""
    results = []
    element_types = ['IfcWall', 'IfcDoor', 'IfcWindow', 'IfcSpace', 
                     'IfcSlab', 'IfcBeam', 'IfcColumn', 'IfcStair']
    
    for element_type in element_types:
        elements = ifc_file.by_type(element_type)
        
        for element in elements:
            missing_attrs = check_required_attributes(element, element_type)
            has_psets = check_property_sets(ifc_file, element)
            
            completeness = 100
            if missing_attrs:
                completeness -= len(missing_attrs) * 20
            if not has_psets:
                completeness -= 20
            
            completeness = max(0, completeness)
            
            results.append({
                'Element-Typ': element_type,
                'GlobalId': element.GlobalId,
                'Name': getattr(element, 'Name', 'Unbenannt'),
                'Fehlende Attribute': ', '.join(missing_attrs) if missing_attrs else 'Keine',
                'Property Sets': 'Ja' if has_psets else 'Nein',
                'Vollständigkeit (%)': completeness,
                'Status': 'Vollständig' if completeness == 100 else 
                         'Teilweise' if completeness >= 50 else 'Unvollständig'
            })
    
    return pd.DataFrame(results)

if uploaded_file is not None:
    try:
        # IFC-Datei laden
        ifc_file = ifcopenshell.file.from_string(uploaded_file.read().decode('utf-8', errors='ignore'))
        
        st.success(f"✅ IFC-Datei erfolgreich geladen: {uploaded_file.name}")
        st.info(f"Schema: {ifc_file.schema}")
        
        # Analyse durchführen
        with st.spinner('Analysiere Attributierung...'):
            df = analyze_ifc_file(ifc_file)
        
        # Statistiken anzeigen
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Gesamtanzahl Elemente", len(df))
        
        with col2:
            complete = len(df[df['Status'] == 'Vollständig'])
            st.metric("Vollständig", complete)
        
        with col3:
            partial = len(df[df['Status'] == 'Teilweise'])
            st.metric("Teilweise", partial)
        
        with col4:
            incomplete = len(df[df['Status'] == 'Unvollständig'])
            st.metric("Unvollständig", incomplete)
        
        # Visualisierungen
        st.markdown("## 📊 Visualisierungen")
        
        viz_col1, viz_col2 = st.columns(2)
        
        with viz_col1:
            # Status-Verteilung
            status_counts = df['Status'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Anzahl']
            fig1 = px.pie(status_counts, values='Anzahl', names='Status', 
                          title='Verteilung nach Status',
                          color='Status',
                          color_discrete_map={'Vollständig': 'green', 
                                             'Teilweise': 'orange', 
                                             'Unvollständig': 'red'})
            st.plotly_chart(fig1, use_container_width=True)
        
        with viz_col2:
            # Vollständigkeit nach Element-Typ
            avg_completeness = df.groupby('Element-Typ')['Vollständigkeit (%)'].mean().reset_index()
            fig2 = px.bar(avg_completeness, x='Element-Typ', y='Vollständigkeit (%)',
                          title='Durchschnittliche Vollständigkeit pro Element-Typ',
                          color='Vollständigkeit (%)',
                          color_continuous_scale='RdYlGn')
            st.plotly_chart(fig2, use_container_width=True)
        
        # Detaillierte Tabelle
        st.markdown("## 📋 Detaillierte Ergebnisse")
        
        # Filter nach Status
        status_filter = st.multiselect(
            'Nach Status filtern',
            options=df['Status'].unique(),
            default=df['Status'].unique()
        )
        
        filtered_df = df[df['Status'].isin(status_filter)]
        
        st.dataframe(
            filtered_df,
            use_container_width=True,
            height=400
        )
        
        # Download-Button für Ergebnisse
        csv = filtered_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 Ergebnisse als CSV herunterladen",
            data=csv,
            file_name="ifc_attributierungs_check.csv",
            mime="text/csv"
        )
        
    except Exception as e:
        st.error(f"❌ Fehler beim Verarbeiten der IFC-Datei: {str(e)}")
else:
    st.info("👆 Bitte laden Sie eine IFC-Datei hoch, um zu beginnen")

# Informationen in der Sidebar
with st.sidebar:
    st.markdown("### ℹ️ Über diese App")
    st.markdown("""
    Diese Anwendung prüft:
    - Vorhandensein erforderlicher Attribute
    - Vollständigkeit von Property Sets
    - Benennungen der Elemente
    
    **Unterstützte Element-Typen:**
    - Wände (IfcWall)
    - Türen (IfcDoor)
    - Fenster (IfcWindow)
    - Räume (IfcSpace)
    - Decken (IfcSlab)
    - Träger (IfcBeam)
    - Stützen (IfcColumn)
    - Treppen (IfcStair)
    """)
    
    st.markdown("### 🔧 Technologie")
    st.markdown("""
    - IfcOpenShell
    - Streamlit
    - Plotly
    - Pandas
    """)
