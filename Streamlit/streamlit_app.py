'''
eBKP-H Suite - Startseite
Willkommensseite mit Logo und Start-Button
'''

import streamlit as st
import os

# Seitenkonfiguration
st.set_page_config(
    page_title="eBKP-H Suite",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS für zentriertes Layout und versteckte Sidebar
st.markdown("""
<style>
    /* Sidebar komplett ausblenden */
    [data-testid="stSidebar"] {
        display: none;
    }
    [data-testid="stSidebarCollapsedControl"] {
        display: none;
    }

    /* Hauptcontainer zentrieren */
    .main .block-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 80vh;
        padding-top: 5rem;
    }

    /* Logo zentrieren */
    [data-testid="stImage"] {
        display: flex;
        justify-content: center;
    }

    /* Start-Button Styling */
    .stButton > button {
        font-size: 1.2rem;
        padding: 0.75rem 3rem;
        border-radius: 0.5rem;
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Pfad zum Logo
logo_path = os.path.join(os.path.dirname(__file__), "Logo.png")

# Logo anzeigen
if os.path.exists(logo_path):
    st.image(logo_path, width=400)
else:
    st.warning("Logo.png nicht gefunden")

# Abstand
st.markdown("<br>", unsafe_allow_html=True)

# Start-Button
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("Start", type="primary", use_container_width=True):
        st.switch_page("pages/Dashboard.py")
