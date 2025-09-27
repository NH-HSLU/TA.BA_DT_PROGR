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

def main():
    st.title("IFC Modell Klassifizierungs-Auswertung")

    st.write("Bitte lade ein IFC-Modell hoch:")
    ifc_file = st.file_uploader("IFC Modell", type="ifc")

    if ifc_file:
        # Temporäre Datei für ifcopenshell
        with open("temp_upload.ifc", "wb") as f:
            f.write(ifc_file.read())

        ifc = ifcopenshell.open("temp_upload.ifc")
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

        st.subheader("Bauteile pro Klassifizierungsgruppe")
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
        ax1.set_title("Verteilung der Bauteil-Klassifizierungen")
        ax1.axis('equal')
        st.pyplot(fig1)

if __name__ == "__main__":
    main()