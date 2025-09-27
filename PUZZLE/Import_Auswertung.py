import ifcopenshell
import streamlit as st
import matplotlib.pyplot as plt
from collections import defaultdict

def get_classifications(element):
    # IFC4: IfcRelAssociatesClassification
    if hasattr(element, "HasAssociations"):
        for assoc in element.HasAssociations:
            if assoc.is_a("IfcRelAssociatesClassification"):
                if hasattr(assoc.RelatingClassification, "Name"):
                    return [assoc.RelatingClassification.Name]
    return []

def auswertung(ifc, titel):
    elements = [e for e in ifc.by_type("IfcElement") if hasattr(e, "Name")]

    classified = defaultdict(list)
    unclassified = []

    for elem in elements:
        classifications = get_classifications(elem)
        if classifications:
            for c in classifications:
                classified[c].append(elem)
        else:
            unclassified.append(elem)

    st.subheader(f"Bauteile pro Klassifizierungsgruppe ({titel})")
    for group, elems in classified.items():
        st.markdown(f"**Klassifizierung: {group}**")
        for e in elems:
            st.write(f"- {e.Name} (GlobalId: {e.GlobalId})")

    st.markdown(f"**Nicht klassifizierte Bauteile: {len(unclassified)}**")
    for e in unclassified:
        st.write(f"- {e.Name} (GlobalId: {e.GlobalId})")

    # Kuchendiagramm: Gesamtübersicht
    labels = list(classified.keys()) + ["Nicht klassifiziert"]
    sizes = [len(elems) for elems in classified.values()] + [len(unclassified)]

    fig1, ax1 = plt.subplots(figsize=(6, 6))
    ax1.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
    ax1.set_title(f"Verteilung der Bauteil-Klassifizierungen ({titel})")
    ax1.axis('equal')
    st.pyplot(fig1)

def main():
    st.title("IFC Modelle laden & auswerten (Architektur & Elektro)")

    st.write("Bitte lade das Architekturmodell (aus Archicad) hoch:")
    arch_file = st.file_uploader("Architekturmodell (IFC)", type="ifc", key="arch")

    st.write("Bitte lade das Elektromodell (aus Revit) hoch:")
    elektro_file = st.file_uploader("Elektromodell (IFC)", type="ifc", key="elektro")

    if arch_file:
        with open("temp_arch.ifc", "wb") as f:
            f.write(arch_file.read())
        arch_ifc = ifcopenshell.open("temp_arch.ifc")
        st.success(f"Architekturmodell '{arch_file.name}' wurde erfolgreich geladen!")
        auswertung(arch_ifc, "Architekturmodell")

    if elektro_file:
        with open("temp_elektr.ifc", "wb") as f:
            f.write(elektro_file.read())
        elektro_ifc = ifcopenshell.open("temp_elektr.ifc")
        st.success(f"Elektromodell '{elektro_file.name}' wurde erfolgreich geladen!")
        auswertung(elektro_ifc, "Elektromodell")

if __name__ == "__main__":
    main()