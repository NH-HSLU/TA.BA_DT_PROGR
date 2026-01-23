'''
eBKP-H⁺ - Startseite
Willkommensseite mit Logo und Start-Button
'''

import streamlit as st
import os
import base64

# Seitenkonfiguration
st.set_page_config(
    page_title="eBKP-H⁺",
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

    /* Logo Container */
    .logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
    }
    .logo-container img {
        max-width: 400px;
        height: auto;
    }

    /* Theme-abhängige Logos: Standard = hell */
    .logo-dark { display: none; }
    .logo-light { display: block; }

    /* Start-Button Styling */
    .stButton > button {
        font-size: 1.2rem;
        padding: 0.75rem 3rem;
        border-radius: 0.5rem;
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Funktion zum Base64-Encoding
def get_base64_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# Pfade zu den Logos
logo_dir = os.path.dirname(__file__)
logo_hell = os.path.join(logo_dir, "Logo_hell.png")
logo_dunkel = os.path.join(logo_dir, "Logo_dunkel.png")

# Logos als Base64
if os.path.exists(logo_hell) and os.path.exists(logo_dunkel):
    b64_hell = get_base64_image(logo_hell)
    b64_dunkel = get_base64_image(logo_dunkel)

    # HTML mit beiden Logos + JavaScript für Theme-Erkennung
    st.markdown(f"""
    <div class="logo-container">
        <img src="data:image/png;base64,{b64_hell}" class="logo-light" alt="Logo">
        <img src="data:image/png;base64,{b64_dunkel}" class="logo-dark" alt="Logo">
    </div>
    <script>
        function updateLogo() {{
            const isDark = window.parent.document.querySelector('[data-testid="stAppViewContainer"]')
                ?.style.backgroundColor.includes('14, 17, 23') ||
                window.matchMedia('(prefers-color-scheme: dark)').matches;

            document.querySelectorAll('.logo-light').forEach(el => el.style.display = isDark ? 'none' : 'block');
            document.querySelectorAll('.logo-dark').forEach(el => el.style.display = isDark ? 'block' : 'none');
        }}
        updateLogo();
        new MutationObserver(updateLogo).observe(window.parent.document.body, {{attributes: true, subtree: true}});
    </script>
    """, unsafe_allow_html=True)
else:
    st.warning("Logo_hell.png und Logo_dunkel.png nicht gefunden")

# Abstand
st.markdown("<br>", unsafe_allow_html=True)

# Start-Button
if st.button("Start", type="primary", width="stretch"):
   st.switch_page("pages/00_Dashboard.py")
