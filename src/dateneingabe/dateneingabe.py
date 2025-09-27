import streamlit as st
import pandas as pd

st.title("Raumprogramm-Eingabe")

# Listen-Speicher initialisieren
if 'raum_liste' not in st.session_state:
    st.session_state['raum_liste'] = []

with st.form("raumprogramm_formular"):
    raumname = st.text_input("Raumname")
    nutzung = st.selectbox("Nutzungsart (gemäss SIA2024)", ["Wohnraum", "Büro", "Sitzungszimmer", "Schulzimmer", "Lehrerzimmer", "Bibliothek", "Labor (verschiedene Fachrichtungen)", "Restaurant", "Küche", "Verkaufsfläche", "Lager", "Technikraum", "Umkleide/Garderobe", "Sanitär (WC, Dusche)", "Turnhalle/Sporthalle", "Multifunktionsraum", "Flur", "Empfang"])
    flaeche = st.number_input("Soll-Fläche [m²]", min_value=1, max_value=1000)
    besondere = st.text_input("Besondere Anforderungen", placeholder="z.B. barrierefrei, medientechnik")
    abgeschickt = st.form_submit_button("Raum hinzufügen")

    if abgeschickt:
        st.session_state['raum_liste'].append({
            "Raumname": raumname,
            "Nutzungsart": nutzung,
            "Fläche_soll_m2": flaeche,
            "Besondere_Anforderungen": besondere
        })

# Anzeige und Export der Tabelle + Neustart-Knopf
if st.session_state['raum_liste']:
    df = pd.DataFrame(st.session_state['raum_liste'])
    st.dataframe(df)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Als CSV herunterladen", data=csv, file_name="raumprogramm.csv", mime="text/csv")

    # Neustart-Knopf
    if st.button("Raumprogramm zurücksetzen"):
        st.session_state['raum_liste'] = []
        st.rerun()

else:
    st.info("Noch keine Räume im Programm.")
