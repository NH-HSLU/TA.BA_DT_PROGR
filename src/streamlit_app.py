import streamlit as st

Auswertung = st.Page("datenauswertung/auswertung.py", title="Auswertung", icon=":material/analytics:")
Eingabe = st.Page("dateneingabe/dateneingabe.py", title="Eingabe", icon=":material/add_circle:")

pg =    st.navigation(
    {
    "HOME":[Eingabe, Auswertung            ]
    })
pg.run()
