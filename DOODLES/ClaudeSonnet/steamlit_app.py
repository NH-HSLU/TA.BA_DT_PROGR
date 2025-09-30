import streamlit as st
import ifcopenshell
import ifcopenshell.util.element as Element
import ifcopenshell.util.placement as Placement
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import defaultdict
import numpy as np

# Seitenkonfiguration
st.set_page_config(
    page_title="IFC Kostenauswertung mit BKP",
    page_icon="💰",
    layout="wide"
)

st.title("💰 IFC Kostenauswertung nach BKP-Baukostenplan")
st.markdown("Objektgliederung nach Gebäude, Etage und Zimmer mit Kostenanalyse")

# Erweitertes BKP-Mapping inkl. Gebäudetechnik und Elektro
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

# BKP Hauptgruppen für Übersicht
BKP_GROUPS = {
    '21': {'name': 'Rohbau 1', 'color': '#1f77b4'},
    '22': {'name': 'Rohbau 2', 'color': '#ff7f0e'},
    '23': {'name': 'Elektroanlagen', 'color': '#2ca02c'},
    '24': {'name': 'Heizungs-, Lüftungs-, Klimaanlagen', 'color': '#d62728'},
    '25': {'name': 'Sanitäranlagen', 'color': '#9467bd'},
    '28': {'name': 'Ausbau', 'color': '#8c564b'}
}

def get_bkp_group(bkp_code):
    """Ermittelt die BKP-Hauptgruppe aus dem Code"""
    if len(bkp_code) >= 2:
        return bkp_code[:2]
    return bkp_code

def get_spatial_structure(ifc_file):
    """Extrahiert die räumliche Struktur: Gebäude > Etage > Raum"""
    structure = defaultdict(lambda: defaultdict(list))
    
    buildings = ifc_file.by_type('IfcBuilding')
    
    for building in buildings:
        building_name = building.Name or "Gebäude ohne Namen"
        
        for rel in building.IsDecomposedBy:
            for storey in rel.RelatedObjects:
                if storey.is_a('IfcBuildingStorey'):
                    storey_name = storey.Name or f"Etage {storey.Elevation or 0}"
                    
                    for rel2 in storey.IsDecomposedBy:
                        for space in rel2.RelatedObjects:
                            if space.is_a('IfcSpace'):
                                space_name = space.LongName or space.Name or "Raum unbenannt"
                                structure[building_name][storey_name].append({
                                    'space': space,
                                    'name': space_name,
                                    'elevation': storey.Elevation or 0
                                })
    
    return structure

def calculate_element_cost(element, element_type):
    """Berechnet die Kosten eines Elements basierend auf BKP-Chefwerten"""
    if element_type not in BKP_MAPPING:
        return 0, 0, 'Unbekannt', '000', 'Nicht klassifiziert'
    
    bkp_info = BKP_MAPPING[element_type]
    unit_cost = bkp_info['unit_cost']
    unit = bkp_info['unit']
    
    # Mengenermittlung
    quantity = 1
    
    try:
        psets = Element.get_psets(element)
        
        # Für Flächen (m²)
        if unit == 'm²':
            for pset_name, pset_data in psets.items():
                if 'NetSideArea' in pset_data:
                    quantity = pset_data['NetSideArea']
                    break
                elif 'GrossSideArea' in pset_data:
                    quantity = pset_data['GrossSideArea']
                    break
                elif 'NetArea' in pset_data:
                    quantity = pset_data['NetArea']
                    break
        
        # Für Längen (m)
        elif unit == 'm':
            for pset_name, pset_data in psets.items():
                if 'Length' in pset_data:
                    quantity = pset_data['Length']
                    break
                elif 'NominalLength' in pset_data:
                    quantity = pset_data['NominalLength']
                    break
            
            # Fallback für lineare Elemente
            if quantity == 1 and hasattr(element, 'Representation'):
                quantity = 3.0  # Standardlänge
        
        # Für Stückzahl bleibt quantity = 1
            
    except Exception as e:
        quantity = 1
    
    total_cost = quantity * unit_cost
    bkp_group = get_bkp_group(bkp_info['code'])
    group_name = BKP_GROUPS.get(bkp_group, {}).get('name', 'Sonstige')
    
    return total_cost, quantity, unit, bkp_info['code'], group_name

def get_all_elements_with_location(ifc_file):
    """Holt alle Elemente mit ihrem räumlichen Kontext"""
    results = []
    
    # Alle relevanten Elemente durchgehen
    for element_type in BKP_MAPPING.keys():
        elements = ifc_file.by_type(element_type)
        
        for element in elements:
            building_name = "Nicht zugeordnet"
            storey_name = "Nicht zugeordnet"
            space_name = "Nicht zugeordnet"
            
            # Räumliche Zuordnung finden
            if hasattr(element, 'ContainedInStructure') and element.ContainedInStructure:
                container = element.ContainedInStructure[0].RelatingStructure
                
                if container.is_a('IfcSpace'):
                    space_name = container.LongName or container.Name or "Raum unbenannt"
                    
                    if hasattr(container, 'Decomposes') and container.Decomposes:
                        storey = container.Decomposes[0].RelatingObject
                        if storey.is_a('IfcBuildingStorey'):
                            storey_name = storey.Name or f"Etage {storey.Elevation or 0}"
                            
                            if hasattr(storey, 'Decomposes') and storey.Decomposes:
                                building = storey.Decomposes[0].RelatingObject
                                if building.is_a('IfcBuilding'):
                                    building_name = building.Name or "Gebäude ohne Namen"
                
                elif container.is_a('IfcBuildingStorey'):
                    storey_name = container.Name or f"Etage {container.Elevation or 0}"
                    
                    if hasattr(container, 'Decomposes') and container.Decomposes:
                        building = container.Decomposes[0].RelatingObject
                        if building.is_a('IfcBuilding'):
                            building_name = building.Name or "Gebäude ohne Namen"
            
            cost, quantity, unit, bkp_code, group_name = calculate_element_cost(element, element_type)
            bkp_info = BKP_MAPPING[element_type]
            
            results.append({
                'Gebäude': building_name,
                'Etage': storey_name,
                'Raum': space_name,
                'Element': element.Name or "Unbenannt",
                'Typ': element_type,
                'BKP-Hauptgruppe': group_name,
                'BKP-Code': bkp_code,
                'BKP-Bezeichnung': bkp_info['name'],
                'Menge': round(quantity, 2),
                'Einheit': unit,
                'Einheitspreis (CHF)': bkp_info['unit_cost'],
                'Gesamtkosten (CHF)': round(cost, 2)
            })
    
    return pd.DataFrame(results)

# Datei-Upload
uploaded_file = st.file_uploader("IFC-Datei hochladen", type=['ifc'])

if uploaded_file is not None:
    try:
        # IFC-Datei laden
        ifc_file = ifcopenshell.file.from_string(uploaded_file.read().decode('utf-8', errors='ignore'))
        
        st.success(f"✅ IFC-Datei erfolgreich geladen: {uploaded_file.name}")
        
        # Räumliche Struktur extrahieren
        with st.spinner('Analysiere Struktur und Kosten...'):
            structure = get_spatial_structure(ifc_file)
            df = get_all_elements_with_location(ifc_file)
        
        if len(df) == 0:
            st.warning("⚠️ Keine relevanten Elemente mit BKP-Klassifizierung gefunden")
        else:
            # Gesamtstatistiken
            st.markdown("## 📊 Kostenübersicht")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_cost = df['Gesamtkosten (CHF)'].sum()
                st.metric("Gesamtkosten", f"CHF {total_cost:,.0f}")
            
            with col2:
                total_elements = len(df)
                st.metric("Anzahl Elemente", f"{total_elements:,}")
            
            with col3:
                avg_cost = df['Gesamtkosten (CHF)'].mean()
                st.metric("Ø Kosten/Element", f"CHF {avg_cost:,.0f}")
            
            with col4:
                num_buildings = df['Gebäude'].nunique()
                st.metric("Anzahl Gebäude", num_buildings)
            
            # BKP-Hauptgruppen Übersicht
            st.markdown("## 🏗️ Kostenverteilung nach BKP-Hauptgruppen")
            
            group_costs = df.groupby('BKP-Hauptgruppe')['Gesamtkosten (CHF)'].sum().reset_index()
            group_costs = group_costs.sort_values('Gesamtkosten (CHF)', ascending=False)
            
            col_g1, col_g2 = st.columns([2, 1])
            
            with col_g1:
                fig_groups = px.bar(
                    group_costs,
                    x='BKP-Hauptgruppe',
                    y='Gesamtkosten (CHF)',
                    title='Kosten nach BKP-Hauptgruppen',
                    color='BKP-Hauptgruppe',
                    color_discrete_sequence=px.colors.qualitative.Set2
                )
                fig_groups.update_layout(showlegend=False, xaxis_tickangle=-45)
                st.plotly_chart(fig_groups, use_container_width=True)
            
            with col_g2:
                st.markdown("### Hauptgruppen")
                group_details = group_costs.copy()
                group_details['Anteil (%)'] = (group_details['Gesamtkosten (CHF)'] / total_cost * 100).round(1)
                st.dataframe(group_details, use_container_width=True, hide_index=True)
            
            # Interaktive Kuchen-Diagramme
            st.markdown("## 🥧 Interaktive Kostenverteilung")
            
            tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                "📍 Nach Gebäude", 
                "🏢 Nach Etage", 
                "🚪 Nach Raum", 
                "📋 Nach BKP-Code",
                "⚡ Elektroanlagen",
                "🌡️ HLKS-Anlagen"
            ])
            
            with tab1:
                building_costs = df.groupby('Gebäude')['Gesamtkosten (CHF)'].sum().reset_index()
                building_costs = building_costs.sort_values('Gesamtkosten (CHF)', ascending=False)
                
                fig1 = px.pie(
                    building_costs, 
                    values='Gesamtkosten (CHF)', 
                    names='Gebäude',
                    title='Kostenverteilung nach Gebäude',
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig1.update_traces(
                    textposition='inside', 
                    textinfo='percent+label',
                    hovertemplate='<b>%{label}</b><br>Kosten: CHF %{value:,.0f}<br>Anteil: %{percent}<extra></extra>'
                )
                st.plotly_chart(fig1, use_container_width=True)
                
                building_details = df.groupby('Gebäude').agg({
                    'Gesamtkosten (CHF)': 'sum',
                    'Element': 'count'
                }).reset_index()
                building_details.columns = ['Gebäude', 'Gesamtkosten (CHF)', 'Anzahl Elemente']
                building_details['Anteil (%)'] = (building_details['Gesamtkosten (CHF)'] / total_cost * 100).round(2)
                st.dataframe(building_details, use_container_width=True, hide_index=True)
            
            with tab2:
                storey_costs = df.groupby(['Gebäude', 'Etage'])['Gesamtkosten (CHF)'].sum().reset_index()
                storey_costs['Label'] = storey_costs['Gebäude'] + ' - ' + storey_costs['Etage']
                storey_costs = storey_costs.sort_values('Gesamtkosten (CHF)', ascending=False)
                
                fig2 = px.pie(
                    storey_costs, 
                    values='Gesamtkosten (CHF)', 
                    names='Label',
                    title='Kostenverteilung nach Etage',
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig2.update_traces(
                    textposition='inside', 
                    textinfo='percent+label',
                    hovertemplate='<b>%{label}</b><br>Kosten: CHF %{value:,.0f}<br>Anteil: %{percent}<extra></extra>'
                )
                st.plotly_chart(fig2, use_container_width=True)
                
                st.markdown("### Top 10 Etagen nach Kosten")
                top_storeys = storey_costs.head(10)[['Label', 'Gesamtkosten (CHF)']]
                top_storeys.columns = ['Etage', 'Gesamtkosten (CHF)']
                st.dataframe(top_storeys, use_container_width=True, hide_index=True)
            
            with tab3:
                room_costs = df.groupby(['Gebäude', 'Etage', 'Raum'])['Gesamtkosten (CHF)'].sum().reset_index()
                room_costs['Label'] = room_costs['Gebäude'] + ' / ' + room_costs['Etage'] + ' / ' + room_costs['Raum']
                room_costs = room_costs.sort_values('Gesamtkosten (CHF)', ascending=False)
                
                top_rooms = room_costs.head(20)
                
                fig3 = px.pie(
                    top_rooms, 
                    values='Gesamtkosten (CHF)', 
                    names='Label',
                    title='Kostenverteilung Top 20 Räume',
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Bold
                )
                fig3.update_traces(
                    textposition='inside', 
                    textinfo='percent',
                    hovertemplate='<b>%{label}</b><br>Kosten: CHF %{value:,.0f}<br>Anteil: %{percent}<extra></extra>'
                )
                st.plotly_chart(fig3, use_container_width=True)
                
                st.markdown("### Top 15 Räume nach Kosten")
                top_room_details = room_costs.head(15)[['Label', 'Gesamtkosten (CHF)']]
                top_room_details.columns = ['Raum', 'Gesamtkosten (CHF)']
                st.dataframe(top_room_details, use_container_width=True, hide_index=True)
            
            with tab4:
                bkp_costs = df.groupby(['BKP-Code', 'BKP-Bezeichnung'])['Gesamtkosten (CHF)'].sum().reset_index()
                bkp_costs['Label'] = bkp_costs['BKP-Code'] + ' - ' + bkp_costs['BKP-Bezeichnung']
                bkp_costs = bkp_costs.sort_values('Gesamtkosten (CHF)', ascending=False)
                
                fig4 = px.pie(
                    bkp_costs, 
                    values='Gesamtkosten (CHF)', 
                    names='Label',
                    title='Kostenverteilung nach BKP-Baukostenplan',
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Vivid
                )
                fig4.update_traces(
                    textposition='inside', 
                    textinfo='percent+label',
                    hovertemplate='<b>%{label}</b><br>Kosten: CHF %{value:,.0f}<br>Anteil: %{percent}<extra></extra>'
                )
                st.plotly_chart(fig4, use_container_width=True)
                
                st.markdown("### BKP-Kostengruppen mit Chefwerten")
                bkp_details = df.groupby(['BKP-Code', 'BKP-Bezeichnung']).agg({
                    'Gesamtkosten (CHF)': 'sum',
                    'Element': 'count',
                    'Menge': 'sum',
                    'Einheit': 'first'
                }).reset_index()
                bkp_details.columns = ['BKP-Code', 'BKP-Bezeichnung', 'Gesamtkosten (CHF)', 
                                       'Anzahl', 'Gesamtmenge', 'Einheit']
                bkp_details['Chefwert (CHF)'] = (bkp_details['Gesamtkosten (CHF)'] / bkp_details['Gesamtmenge']).round(2)
                bkp_details['Anteil (%)'] = (bkp_details['Gesamtkosten (CHF)'] / total_cost * 100).round(2)
                st.dataframe(bkp_details, use_container_width=True, hide_index=True)
            
            with tab5:
                st.markdown("### ⚡ Elektroanlagen (BKP 23)")
                
                # Filter für Elektroanlagen
                electro_df = df[df['BKP-Code'].str.startswith('23')]
                
                if len(electro_df) > 0:
                    electro_total = electro_df['Gesamtkosten (CHF)'].sum()
                    
                    col_e1, col_e2, col_e3 = st.columns(3)
                    with col_e1:
                        st.metric("Elektro Gesamtkosten", f"CHF {electro_total:,.0f}")
                    with col_e2:
                        st.metric("Anzahl Komponenten", len(electro_df))
                    with col_e3:
                        electro_percent = (electro_total / total_cost * 100)
                        st.metric("Anteil an Gesamtkosten", f"{electro_percent:.1f}%")
                    
                    # Unterkategorien
                    electro_sub = electro_df.groupby('BKP-Bezeichnung')['Gesamtkosten (CHF)'].sum().reset_index()
                    electro_sub = electro_sub.sort_values('Gesamtkosten (CHF)', ascending=False)
                    
                    fig_electro = px.pie(
                        electro_sub,
                        values='Gesamtkosten (CHF)',
                        names='BKP-Bezeichnung',
                        title='Elektro-Kostenverteilung nach Unterkategorien',
                        hole=0.3,
                        color_discrete_sequence=px.colors.sequential.Greens
                    )
                    fig_electro.update_traces(
                        textposition='inside',
                        textinfo='percent+label',
                        hovertemplate='<b>%{label}</b><br>CHF %{value:,.0f}<extra></extra>'
                    )
                    st.plotly_chart(fig_electro, use_container_width=True)
                    
                    # Detail-Tabelle
                    st.markdown("#### Elektro-Komponenten Details")
                    electro_details = electro_df.groupby(['BKP-Code', 'BKP-Bezeichnung', 'Typ']).agg({
                        'Gesamtkosten (CHF)': 'sum',
                        'Element': 'count',
                        'Menge': 'sum'
                    }).reset_index()
                    electro_details.columns = ['BKP', 'Bezeichnung', 'IFC-Typ', 'Kosten (CHF)', 'Anzahl', 'Menge']
                    st.dataframe(electro_details, use_container_width=True, hide_index=True)
                else:
                    st.info("Keine Elektroanlagen in der IFC-Datei gefunden")
            
            with tab6:
                st.markdown("### 🌡️ HLKS-Anlagen (BKP 24)")
                
                # Filter für HLKS
                hlks_df = df[df['BKP-Code'].str.startswith('24')]
                
                if len(hlks_df) > 0:
                    hlks_total = hlks_df['Gesamtkosten (CHF)'].sum()
                    
                    col_h1, col_h2, col_h3 = st.columns(3)
                    with col_h1:
                        st.metric("HLKS Gesamtkosten", f"CHF {hlks_total:,.0f}")
                    with col_h2:
                        st.metric("Anzahl Komponenten", len(hlks_df))
                    with col_h3:
                        hlks_percent = (hlks_total / total_cost * 100)
                        st.metric("Anteil an Gesamtkosten", f"{hlks_percent:.1f}%")
                    
                    # Unterkategorien
                    hlks_sub = hlks_df.groupby('BKP-Bezeichnung')['Gesamtkosten (CHF)'].sum().reset_index()
                    hlks_sub = hlks_sub.sort_values('Gesamtkosten (CHF)', ascending=False)
                    
                    fig_hlks = px.pie(
                        hlks_sub,
                        values='Gesamtkosten (CHF)',
                        names='BKP-Bezeichnung',
                        title='HLKS-Kostenverteilung nach Unterkategorien',
                        hole=0.3,
                        color_discrete_sequence=px.colors.sequential.Reds
                    )
                    fig_hlks.update_traces(
                        textposition='inside',
                        textinfo='percent+label',
                        hovertemplate='<b>%{label}</b><br>CHF %{value:,.0f}<extra></extra>'
                    )
                    st.plotly_chart(fig_hlks, use_container_width=True)
                    
                    # Detail-Tabelle
                    st.markdown("#### HLKS-Komponenten Details")
                    hlks_details = hlks_df.groupby(['BKP-Code', 'BKP-Bezeichnung', 'Typ']).agg({
                        'Gesamtkosten (CHF)': 'sum',
                        'Element': 'count',
                        'Menge': 'sum'
                    }).reset_index()
                    hlks_details.columns = ['BKP', 'Bezeichnung', 'IFC-Typ', 'Kosten (CHF)', 'Anzahl', 'Menge']
                    st.dataframe(hlks_details, use_container_width=True, hide_index=True)
                else:
                    st.info("Keine HLKS-Anlagen in der IFC-Datei gefunden")
            
            # Hierarchische Tabellenansicht
            st.markdown("## 📋 Hierarchische Kostenübersicht")
            
            # Filter
            filter_col1, filter_col2, filter_col3 = st.columns(3)
            
            with filter_col1:
                selected_buildings = st.multiselect(
                    'Gebäude filtern',
                    options=df['Gebäude'].unique(),
                    default=df['Gebäude'].unique()
                )
            
            with filter_col2:
                selected_bkp_groups = st.multiselect(
                    'BKP-Hauptgruppe filtern',
                    options=df['BKP-Hauptgruppe'].unique(),
                    default=df['BKP-Hauptgruppe'].unique()
                )
            
            with filter_col3:
                min_cost = st.number_input('Min. Kosten (CHF)', min_value=0, value=0)
            
            # Gefilterte Daten
            filtered_df = df[
                (df['Gebäude'].isin(selected_buildings)) &
                (df['BKP-Hauptgruppe'].isin(selected_bkp_groups)) &
                (df['Gesamtkosten (CHF)'] >= min_cost)
            ]
            
            st.dataframe(
                filtered_df,
                use_container_width=True,
                height=400
            )
            
            # Download
            csv = filtered_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 Kostenauswertung als CSV herunterladen",
                data=csv,
                file_name="ifc_kostenauswertung_bkp_komplett.csv",
                mime="text/csv"
            )
            
    except Exception as e:
        st.error(f"❌ Fehler beim Verarbeiten der IFC-Datei: {str(e)}")
        st.exception(e)
else:
    st.info("👆 Bitte laden Sie eine IFC-Datei hoch, um die Kostenauswertung zu starten")

# Sidebar mit Informationen
with st.sidebar:
    st.markdown("### ℹ️ Über diese Anwendung")
    st.markdown("""
    Diese Anwendung erstellt eine **hierarchische Kostenauswertung** nach:
    
    **Räumliche Gliederung:**
    - 🏢 Gebäude
    - 📐 Etage
    - 🚪 Raum
    
    **BKP-Klassifizierung:**
    - **BKP 21**: Rohbau 1
    - **BKP 22**: Rohbau 2
    - **BKP 23**: Elektroanlagen
    - **BKP 24**: HLKS-Anlagen
    - **BKP 25**: Sanitäranlagen
    """)
    
    st.markdown("### ⚡ Elektroanlagen (BKP 23)")
    st.markdown("""
    - 231: Apparate Starkstrom
    - 232: Starkstrominstallationen
    - 233: Leuchten und Lampen
    - 234: Elektrogeräte
    - 235: Schwachstromanlagen
    - 237: Gebäudeautomation
    """)
    
    st.markdown("### 🌡️ HLKS (BKP 24)")
    st.markdown("""
    - 241: Energieträger, Lagerung
    - 242: Wärmeerzeugung
    - 243: Wärmeverteilung
    - 244: Lüftungsanlagen
    - 245: Klimaanlagen
    - 246: Kälteanlagen
    """)
    
    st.markdown("### 💰 Chefwerte")
    st.markdown("""
    Einheitspreise für Kostenschätzung:
    - CHF/m² (Flächen)
    - CHF/m (Längen)
    - CHF/Stk (Stückzahl)
    """)
    
    st.markdown("### 🔧 Technologie")
    st.markdown("""
    - IfcOpenShell
    - Streamlit
    - Plotly (Interaktive Charts)
    - Pandas
    """)