import streamlit as st
import ifcopenshell
import ifcopenshell.util.element
import pandas as pd
import plotly.express as px
from collections import defaultdict
import io

# BKP-Kategorisierung (Schweizer Baukostenplan)
BKP_MAPPING = {
    # BKP 21 - Rohbau 1
    'IfcWall': {'code': '211', 'name': 'Baumeisterarbeiten / Wände', 'unit_cost': 450, 'unit': 'm²'},
    'IfcWallStandardCase': {'code': '211', 'name': 'Baumeisterarbeiten / Wände', 'unit_cost': 450, 'unit': 'm²'},
    'IfcSlab': {'code': '211', 'name': 'Baumeisterarbeiten / Decken', 'unit_cost': 380, 'unit': 'm²'},
    'IfcBeam': {'code': '214', 'name': 'Montagebau Holz / Träger', 'unit_cost': 350, 'unit': 'm'},
    'IfcColumn': {'code': '213', 'name': 'Montagebau Stahl / Stützen', 'unit_cost': 420, 'unit': 'm'},
    
    # BKP 22 - Rohbau 2
    'IfcDoor': {'code': '221', 'name': 'Fenster, Aussentüren', 'unit_cost': 1200, 'unit': 'Stk'},
    'IfcWindow': {'code': '221', 'name': 'Fenster, Aussentüren', 'unit_cost': 1500, 'unit': 'Stk'},
    'IfcRoof': {'code': '224', 'name': 'Bedachungsarbeiten', 'unit_cost': 520, 'unit': 'm²'},
    'IfcCurtainWall': {'code': '221', 'name': 'Fassadenkonstruktion', 'unit_cost': 950, 'unit': 'm²'},
    'IfcRailing': {'code': '228', 'name': 'Äussere Abschlüsse', 'unit_cost': 280, 'unit': 'm'},
    'IfcStair': {'code': '211', 'name': 'Baumeisterarbeiten / Treppen', 'unit_cost': 800, 'unit': 'm'},
    'IfcCovering': {'code': '281', 'name': 'Bodenbeläge', 'unit_cost': 120, 'unit': 'm²'},
    
    # BKP 23 - Elektroanlagen
    'IfcElectricDistributionBoard': {'code': '231', 'name': 'Apparate Starkstrom', 'unit_cost': 3500, 'unit': 'Stk'},
    'IfcSwitchingDevice': {'code': '231', 'name': 'Apparate Starkstrom', 'unit_cost': 150, 'unit': 'Stk'},
    'IfcOutlet': {'code': '232', 'name': 'Starkstrominstallationen', 'unit_cost': 180, 'unit': 'Stk'},
    'IfcLightFixture': {'code': '233', 'name': 'Leuchten und Lampen', 'unit_cost': 450, 'unit': 'Stk'},
    'IfcElectricAppliance': {'code': '234', 'name': 'Elektrogeräte', 'unit_cost': 800, 'unit': 'Stk'},
    'IfcCableCarrierFitting': {'code': '232', 'name': 'Starkstrominstallationen / Kabelkanäle', 'unit_cost': 85, 'unit': 'm'},
    'IfcCableSegment': {'code': '232', 'name': 'Starkstrominstallationen / Kabel', 'unit_cost': 25, 'unit': 'm'},
    'IfcCommunicationsAppliance': {'code': '235', 'name': 'Apparate Schwachstrom', 'unit_cost': 650, 'unit': 'Stk'},
    'IfcAlarm': {'code': '235', 'name': 'Apparate Schwachstrom / Brandmeldung', 'unit_cost': 280, 'unit': 'Stk'},
    'IfcController': {'code': '237', 'name': 'Gebäudeautomation', 'unit_cost': 1200, 'unit': 'Stk'},
    'IfcSensor': {'code': '237', 'name': 'Gebäudeautomation / Sensoren', 'unit_cost': 320, 'unit': 'Stk'},
    'IfcActuator': {'code': '237', 'name': 'Gebäudeautomation / Aktoren', 'unit_cost': 450, 'unit': 'Stk'},
    
    # BKP 24 - Heizungs-, Lüftungs-, Klimaanlagen (HLKS)
    'IfcBoiler': {'code': '242', 'name': 'Wärmeerzeugung / Kessel', 'unit_cost': 15000, 'unit': 'Stk'},
    'IfcChiller': {'code': '246', 'name': 'Kälteanlagen / Kältemaschine', 'unit_cost': 25000, 'unit': 'Stk'},
    'IfcPump': {'code': '243', 'name': 'Wärmeverteilung / Pumpen', 'unit_cost': 2800, 'unit': 'Stk'},
    'IfcFan': {'code': '244', 'name': 'Lüftungsanlagen / Ventilatoren', 'unit_cost': 3200, 'unit': 'Stk'},
    'IfcAirTerminal': {'code': '244', 'name': 'Lüftungsanlagen / Luftauslässe', 'unit_cost': 380, 'unit': 'Stk'},
    'IfcAirToAirHeatRecovery': {'code': '244', 'name': 'Lüftungsanlagen / Wärmerückgewinnung', 'unit_cost': 8500, 'unit': 'Stk'},
    'IfcDuctSegment': {'code': '244', 'name': 'Lüftungsanlagen / Luftkanäle', 'unit_cost': 120, 'unit': 'm'},
    'IfcDuctFitting': {'code': '244', 'name': 'Lüftungsanlagen / Formstücke', 'unit_cost': 85, 'unit': 'Stk'},
    'IfcPipeSegment': {'code': '243', 'name': 'Wärmeverteilung / Rohrleitungen', 'unit_cost': 95, 'unit': 'm'},
    'IfcPipeFitting': {'code': '243', 'name': 'Wärmeverteilung / Rohrverbinder', 'unit_cost': 45, 'unit': 'Stk'},
    'IfcValve': {'code': '243', 'name': 'Wärmeverteilung / Armaturen', 'unit_cost': 280, 'unit': 'Stk'},
    'IfcHeatExchanger': {'code': '242', 'name': 'Wärmeerzeugung / Wärmetauscher', 'unit_cost': 5500, 'unit': 'Stk'},
    'IfcCoil': {'code': '245', 'name': 'Klimaanlagen / Wärmeregister', 'unit_cost': 1800, 'unit': 'Stk'},
    'IfcHumidifier': {'code': '245', 'name': 'Klimaanlagen / Befeuchter', 'unit_cost': 3200, 'unit': 'Stk'},
    'IfcTank': {'code': '241', 'name': 'Zulieferung Energieträger / Tanks', 'unit_cost': 8000, 'unit': 'Stk'},
    'IfcSpaceHeater': {'code': '243', 'name': 'Wärmeverteilung / Heizkörper', 'unit_cost': 650, 'unit': 'Stk'},
    'IfcUnitaryEquipment': {'code': '245', 'name': 'Klimaanlagen / Klimageräte', 'unit_cost': 4500, 'unit': 'Stk'},
    'IfcFilter': {'code': '244', 'name': 'Lüftungsanlagen / Filter', 'unit_cost': 420, 'unit': 'Stk'},
    'IfcDamper': {'code': '244', 'name': 'Lüftungsanlagen / Klappen', 'unit_cost': 350, 'unit': 'Stk'},
    
    # BKP 25 - Sanitäranlagen
    'IfcSanitaryTerminal': {'code': '251', 'name': 'Allgemeine Sanitärapparate', 'unit_cost': 850, 'unit': 'Stk'},
    'IfcFireSuppressionTerminal': {'code': '252', 'name': 'Spezielle Sanitärapparate', 'unit_cost': 1200, 'unit': 'Stk'},
    'IfcWasteTerminal': {'code': '254', 'name': 'Sanitärleitungen / Abwasser', 'unit_cost': 180, 'unit': 'm'},
}

def get_bkp_category(ifc_type):
    """Ordnet IFC-Typen BKP-Kategorien zu"""
    bkp_info = BKP_MAPPING.get(ifc_type, {
        'code': '999', 
        'name': 'Nicht kategorisiert', 
        'unit_cost': 0, 
        'unit': 'Stk'
    })
    return bkp_info

def analyze_ifc_file(ifc_file):
    """Analysiert IFC-Datei und erstellt Ausmass-Daten"""
    import ifcopenshell.util.element
    
    data = []
    
    # Alle Bauteile extrahieren
    elements = ifc_file.by_type('IfcProduct')
    
    for element in elements:
        # Räumliche Strukturelemente überspringen
        if element.is_a('IfcSpatialStructureElement') or element.is_a('IfcSpace'):
            continue
        
        # Gebäude, Etage und Raum ermitteln
        building_name = "Unzugeordnet"
        storey_name = "Unzugeordnet"
        space_name = "Unzugeordnet"
        
        # Räumliche Zuordnung mit get_container ermitteln
        try:
            container = ifcopenshell.util.element.get_container(element)
            
            if container:
                if container.is_a('IfcBuildingStorey'):
                    storey_name = container.Name or f"Etage {container.id()}"
                    if hasattr(container, 'Decomposes') and container.Decomposes:
                        for rel in container.Decomposes:
                            building = rel.RelatingObject
                            if building.is_a('IfcBuilding'):
                                building_name = building.Name or f"Gebäude {building.id()}"
                                break
                
                elif container.is_a('IfcSpace'):
                    space_name = container.Name or f"Raum {container.id()}"
                    if hasattr(container, 'Decomposes') and container.Decomposes:
                        for rel in container.Decomposes:
                            storey = rel.RelatingObject
                            if storey.is_a('IfcBuildingStorey'):
                                storey_name = storey.Name or f"Etage {storey.id()}"
                                if hasattr(storey, 'Decomposes') and storey.Decomposes:
                                    for rel_build in storey.Decomposes:
                                        building = rel_build.RelatingObject
                                        if building.is_a('IfcBuilding'):
                                            building_name = building.Name or f"Gebäude {building.id()}"
                                            break
                                break
                
                elif container.is_a('IfcBuilding'):
                    building_name = container.Name or f"Gebäude {container.id()}"
                
                elif container.is_a('IfcSite'):
                    building_name = "Gelände/Site"
        
        except Exception as e:
            pass
        
        # Eigenschaften extrahieren
        element_type = element.is_a()
        bkp_info = get_bkp_category(element_type)
        
        # Quantitäten ermitteln
        quantities = ifcopenshell.util.element.get_psets(element)
        volume = 0.0
        area = 0.0
        length = 0.0
        count = 1  # Stückzahl
        
        for pset_name, props in quantities.items():
            if isinstance(props, dict):
                if 'Volume' in props:
                    try:
                        volume = float(props['Volume'])
                    except (ValueError, TypeError):
                        pass
                if 'Area' in props or 'NetArea' in props or 'GrossArea' in props:
                    try:
                        area = float(props.get('Area', props.get('NetArea', props.get('GrossArea', 0.0))))
                    except (ValueError, TypeError):
                        pass
                if 'Length' in props:
                    try:
                        length = float(props['Length'])
                    except (ValueError, TypeError):
                        pass
        
        # Kostenberechnung basierend auf Einheit
        cost = 0.0
        primary_quantity = 0.0
        
        if bkp_info['unit'] == 'm²' and area > 0:
            primary_quantity = area
            cost = area * bkp_info['unit_cost']
        elif bkp_info['unit'] == 'm' and length > 0:
            primary_quantity = length
            cost = length * bkp_info['unit_cost']
        elif bkp_info['unit'] == 'm³' and volume > 0:
            primary_quantity = volume
            cost = volume * bkp_info['unit_cost']
        elif bkp_info['unit'] == 'Stk':
            primary_quantity = count
            cost = count * bkp_info['unit_cost']
        
        data.append({
            'Gebäude': building_name,
            'Etage': storey_name,
            'Raum': space_name,
            'Element': element.Name or f"{element_type}_{element.id()}",
            'IFC-Typ': element_type,
            'BKP-Code': bkp_info['code'],
            'BKP-Kategorie': bkp_info['name'],
            'Einheit': bkp_info['unit'],
            'Menge': round(primary_quantity, 2),
            'Einheitspreis (CHF)': bkp_info['unit_cost'],
            'Kosten (CHF)': round(cost, 2),
            'Volumen (m³)': round(volume, 2) if volume else 0.0,
            'Fläche (m²)': round(area, 2) if area else 0.0,
            'Länge (m)': round(length, 2) if length else 0.0,
            'GUID': element.GlobalId
        })
    
    return pd.DataFrame(data)


def extract_spatial_structure(ifc_file):
    """Extrahiert Gebäude-, Etagen- und Raumstruktur"""
    structure = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    
    # Alle räumlichen Elemente durchgehen
    buildings = ifc_file.by_type('IfcBuilding')
    
    for building in buildings:
        building_name = building.Name or f"Gebäude {building.id()}"
        
        # Etagen im Gebäude
        for rel in building.IsDecomposedBy or []:
            for storey in rel.RelatedObjects:
                if storey.is_a('IfcBuildingStorey'):
                    storey_name = storey.Name or f"Etage {storey.id()}"
                    
                    # Räume in der Etage
                    for rel_storey in storey.IsDecomposedBy or []:
                        for space in rel_storey.RelatedObjects:
                            if space.is_a('IfcSpace'):
                                space_name = space.Name or f"Raum {space.id()}"
                                
                                # Elemente im Raum
                                for rel_space in space.IsDecomposedBy or []:
                                    for element in rel_space.RelatedObjects:
                                        structure[building_name][storey_name][space_name].append(element)
    
    return structure


# Streamlit App
st.set_page_config(
    page_title="IFC Ausmass-Analyse mit BKP",
    page_icon="🏗️",
    layout="wide"
)

st.title("🏗️ IFC Ausmass-Analyse mit BKP-Kategorisierung")
st.markdown("**Kompatibel mit IFC2x3, IFC4 und IFC4x3**")

# Sidebar
with st.sidebar:
    st.header("📁 IFC-Datei hochladen")
    uploaded_file = st.file_uploader(
        "Wählen Sie eine IFC-Datei",
        type=['ifc'],
        help="Unterstützt IFC2x3, IFC4 und IFC4x3"
    )
    
    st.markdown("---")
    st.markdown("### ℹ️ Info")
    st.markdown("""
    Diese Applikation analysiert IFC-Modelle und erstellt ein Ausmass der Elemente 
    nach **BKP-Kategorien** (Schweizer Baukostenplan).
    
    **Features:**
    - Hierarchische Struktur: Gebäude → Etage → Raum
    - BKP-Kategorisierung
    - Interaktive Kreisdiagramme
    - Exportierbare Listen
    """)

# Hauptbereich
if uploaded_file is not None:
    try:
        # IFC-Datei laden
        with st.spinner("IFC-Datei wird geladen..."):
            # Datei temporär speichern
            bytes_data = uploaded_file.read()
            temp_file_path = f"temp_{uploaded_file.name}"
            with open(temp_file_path, 'wb') as f:
                f.write(bytes_data)
            
            ifc_file = ifcopenshell.open(temp_file_path)
            schema_version = ifc_file.schema
            
            st.success(f"✅ IFC-Datei erfolgreich geladen! Schema: **{schema_version}**")
        
        # Daten analysieren
        with st.spinner("Daten werden analysiert..."):
            df = analyze_ifc_file(ifc_file)
        
        if df.empty:
            st.warning("⚠️ Keine Elemente in der IFC-Datei gefunden.")
        else:
            st.success(f"✅ {len(df)} Elemente analysiert")
            
            # Filter
            col1, col2, col3 = st.columns(3)
            
            with col1:
                buildings = ['Alle'] + sorted(df['Gebäude'].unique().tolist())
                selected_building = st.selectbox("Gebäude", buildings)
            
            with col2:
                if selected_building != 'Alle':
                    storeys = ['Alle'] + sorted(df[df['Gebäude'] == selected_building]['Etage'].unique().tolist())
                else:
                    storeys = ['Alle'] + sorted(df['Etage'].unique().tolist())
                selected_storey = st.selectbox("Etage", storeys)
            
            with col3:
                if selected_building != 'Alle' and selected_storey != 'Alle':
                    rooms = ['Alle'] + sorted(df[(df['Gebäude'] == selected_building) & 
                                                  (df['Etage'] == selected_storey)]['Raum'].unique().tolist())
                elif selected_building != 'Alle':
                    rooms = ['Alle'] + sorted(df[df['Gebäude'] == selected_building]['Raum'].unique().tolist())
                elif selected_storey != 'Alle':
                    rooms = ['Alle'] + sorted(df[df['Etage'] == selected_storey]['Raum'].unique().tolist())
                else:
                    rooms = ['Alle'] + sorted(df['Raum'].unique().tolist())
                selected_room = st.selectbox("Raum", rooms)
            
            # Daten filtern
            filtered_df = df.copy()
            if selected_building != 'Alle':
                filtered_df = filtered_df[filtered_df['Gebäude'] == selected_building]
            if selected_storey != 'Alle':
                filtered_df = filtered_df[filtered_df['Etage'] == selected_storey]
            if selected_room != 'Alle':
                filtered_df = filtered_df[filtered_df['Raum'] == selected_room]
            
            # Tabs für verschiedene Ansichten
            tab1, tab2, tab3 = st.tabs(["📊 Kreisdiagramme", "📋 Detailliste", "📈 Statistiken"])
            
            with tab1:
                st.header("Interaktive Kreisdiagramme")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # BKP-Kategorien Verteilung
                    bkp_counts = filtered_df['BKP-Kategorie'].value_counts().reset_index()
                    bkp_counts.columns = ['BKP-Kategorie', 'Anzahl']
                    
                    fig1 = px.pie(
                        bkp_counts, 
                        values='Anzahl', 
                        names='BKP-Kategorie',
                        title='Verteilung nach BKP-Kategorien',
                        hole=0.3
                    )
                    st.plotly_chart(fig1, use_container_width=True)
                
                with col2:
                    # IFC-Typen Verteilung
                    ifc_counts = filtered_df['IFC-Typ'].value_counts().reset_index()
                    ifc_counts.columns = ['IFC-Typ', 'Anzahl']
                    
                    fig2 = px.pie(
                        ifc_counts, 
                        values='Anzahl', 
                        names='IFC-Typ',
                        title='Verteilung nach IFC-Typen',
                        hole=0.3
                    )
                    st.plotly_chart(fig2, use_container_width=True)
                
                col3, col4 = st.columns(2)
                
                with col3:
                    # Gebäude Verteilung
                    building_counts = filtered_df['Gebäude'].value_counts().reset_index()
                    building_counts.columns = ['Gebäude', 'Anzahl']
                    
                    fig3 = px.pie(
                        building_counts, 
                        values='Anzahl', 
                        names='Gebäude',
                        title='Verteilung nach Gebäuden',
                        hole=0.3
                    )
                    st.plotly_chart(fig3, use_container_width=True)
                
                with col4:
                    # Etagen Verteilung
                    storey_counts = filtered_df['Etage'].value_counts().reset_index()
                    storey_counts.columns = ['Etage', 'Anzahl']
                    
                    fig4 = px.pie(
                        storey_counts, 
                        values='Anzahl', 
                        names='Etage',
                        title='Verteilung nach Etagen',
                        hole=0.3
                    )
                    st.plotly_chart(fig4, use_container_width=True)
            
            with tab2:
                st.header("Detaillierte Elementliste")
                
                # Suchfunktion
                search = st.text_input("🔍 Suche in Elementnamen", "")
                if search:
                    display_df = filtered_df[filtered_df['Element'].str.contains(search, case=False, na=False)]
                else:
                    display_df = filtered_df
                
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Download-Button
                csv = display_df.to_csv(index=False, encoding='utf-8-sig', sep=';')
                st.download_button(
                    label="📥 Als CSV exportieren",
                    data=csv,
                    file_name=f"ifc_ausmass_{uploaded_file.name}.csv",
                    mime="text/csv"
                )
            
            with tab3:
                st.header("Statistiken und Zusammenfassung")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Gesamt Elemente", len(filtered_df))
                
                with col2:
                    st.metric("BKP-Kategorien", filtered_df['BKP-Kategorie'].nunique())
                
                with col3:
                    st.metric("IFC-Typen", filtered_df['IFC-Typ'].nunique())
                
                with col4:
                    total_volume = filtered_df['Volumen (m³)'].sum()
                    st.metric("Gesamt Volumen", f"{total_volume:.2f} m³")
                
                st.markdown("---")
                
                # Zusammenfassung nach BKP
                st.subheader("Zusammenfassung nach BKP-Kategorien")
                bkp_summary = filtered_df.groupby('BKP-Kategorie').agg({
                    'Element': 'count',
                    'Volumen (m³)': 'sum',
                    'Fläche (m²)': 'sum',
                    'Länge (m)': 'sum'
                }).reset_index()
                bkp_summary.columns = ['BKP-Kategorie', 'Anzahl', 'Volumen (m³)', 'Fläche (m²)', 'Länge (m)']
                
                st.dataframe(bkp_summary, use_container_width=True, hide_index=True)
                
                # Balkendiagramm
                fig5 = px.bar(
                    bkp_summary.sort_values('Anzahl', ascending=False),
                    x='BKP-Kategorie',
                    y='Anzahl',
                    title='Elementanzahl nach BKP-Kategorien',
                    labels={'Anzahl': 'Anzahl Elemente'},
                    text='Anzahl'
                )
                fig5.update_traces(textposition='outside')
                st.plotly_chart(fig5, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Fehler beim Verarbeiten der IFC-Datei: {str(e)}")
        st.exception(e)

else:
    st.info("👈 Bitte laden Sie eine IFC-Datei hoch, um zu beginnen.")
    
    # Beispielinformationen
    st.markdown("### 🎯 Unterstützte Funktionen")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **IFC-Kompatibilität:**
        - IFC2x3 TC1
        - IFC4 Add2 TC1
        - IFC4x3 Add2
        """)
    
    with col2:
        st.markdown("""
        **BKP-Hauptgruppen:**
        - C: Bauwerkkonstruktionen
        - D: Technische Anlagen
        - E: Aussenwandkonstruktionen
        - F: Bedachungen
        - G: Ausbau
        """)