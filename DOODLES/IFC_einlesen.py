import ifcopenshell
import streamlit as st

def main():
    st.title("IFC Modelle laden (Architektur & Elektro)")

    st.write("Bitte lade das Architekturmodell (aus Archicad) hoch:")
    arch_file = st.file_uploader("Architekturmodell (IFC)", type="ifc", key="arch")

    st.write("Bitte lade das Elektromodell (aus Revit) hoch:")
    elektro_file = st.file_uploader("Elektromodell (IFC)", type="ifc", key="elektro")

    if arch_file and elektro_file:
        # Temporäre Dateien für ifcopenshell
        with open("temp_arch.ifc", "wb") as f:
            f.write(arch_file.read())
        with open("temp_elektr.ifc", "wb") as f:
            f.write(elektro_file.read())

        arch_ifc = ifcopenshell.open("temp_arch.ifc")
        elektro_ifc = ifcopenshell.open("temp_elektr.ifc")

        st.success("Beide Modelle wurden erfolgreich geladen!")
        st.write(f"Architekturmodell: {arch_file.name}")
        st.write(f"Elektromodell: {elektro_file.name}")

if __name__ == "__main__":
    main()