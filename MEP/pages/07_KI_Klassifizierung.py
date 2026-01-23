'''
Folie 8: KI-Klassifizierung
'''

import streamlit as st
import os
import sys

# Pfad-Setup
current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from helpers.presentation_helpers import (
    init_slide_page,
    start_slide,
    end_slide,
    render_slide_navigation,
    render_divider,
    render_code_block,
    render_gradient_card,
    render_content_box
)

# Page Init
init_slide_page("KI-Klassifizierung")

# === SLIDE START ===
start_slide(
    "KI-Klassifizierung",
    "Wie Claude AI die eBKP-H Codes zuordnet",
    slide_number=8,
    total_slides=12
)

# Claude AI Übersicht
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 🤖 Claude AI Integration")
    st.markdown("""
    Wir nutzen **Claude 3.5 Haiku** von Anthropic für die Klassifizierung:

    - **Schnell**: Optimiert für hohen Durchsatz
    - **Günstig**: Niedrigste Kosten pro Token
    - **Präzise**: Hohe Trefferquote bei Klassifizierung
    - **Kontextfähig**: Versteht Schweizer Baustandards
    """)

    st.markdown("### 📊 Konfidenzwerte")
    st.markdown("""
    Jede Klassifizierung enthält einen Konfidenzwert (0-1):

    - **≥ 0.9**: Hohe Sicherheit ✅
    - **0.7 - 0.9**: Mittlere Sicherheit ⚠️
    - **< 0.7**: Überprüfung empfohlen 🔍
    """)

with col2:
    st.markdown("### 💬 Beispiel API-Aufruf")
    render_code_block('''# Klassifizierung eines Elements
from anthropic import Anthropic

client = Anthropic()

response = client.messages.create(
    model="claude-3-5-haiku-20241022",
    max_tokens=100,
    messages=[{
        "role": "user",
        "content": """
        Klassifiziere dieses Bauelement
        nach eBKP-H:

        Typ: Aussenwand
        Material: Backstein 30cm
        """
    }]
)

# Antwort: {"code": "C2.1",
#           "confidence": 0.94}''', "python", "classifier.py")

render_divider()


# Prompt Engineering
st.markdown("### 🎯 Prompt-Optimierung")

render_content_box("""
<strong>System Prompt (gekürzt):</strong><br><br>
<code>Du bist ein Experte für Schweizer Baukostenklassifizierung nach eBKP-H.
Ordne das gegebene Bauelement dem passenden eBKP-H Code zu.
Antworte im JSON-Format: {"code": "X1.2.3", "confidence": 0.95}</code>
<br><br>
<strong>Optimierungen:</strong>
<ul>
    <li>Kurze, präzise Prompts (weniger Tokens)</li>
    <li>Strukturierte JSON-Ausgabe</li>
    <li>Prompt Caching für wiederholte System-Prompts</li>
</ul>
""", "Prompt Engineering")

# === SLIDE END ===
end_slide()

# Navigation
render_slide_navigation(current_slide=8)
