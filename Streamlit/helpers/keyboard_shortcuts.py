"""
Keyboard Shortcuts Hilfe
Übersicht über verfügbare Tastenkombinationen
"""

import streamlit as st


SHORTCUTS = {
    "Navigation": {
        "1-6": "Kostenermittlung: Stufe direkt wählen",
        "Space": "KI-Klassifizierung starten",
        "Ctrl/Cmd + S": "BKP-Codes speichern (Bearbeiten-Seite)",
        "Ctrl/Cmd + E": "Export starten (Auswertung)",
        "?": "Diese Hilfe anzeigen/verstecken",
    },
    "Allgemein": {
        "Esc": "Dialogfenster schließen",
        "Tab": "Zwischen Elementen wechseln",
        "Enter": "Bestätigen",
    }
}


def show_keyboard_shortcuts():
    """
    Zeigt Keyboard Shortcuts in einem Expander

    Example:
        # Am Ende jeder Page:
        show_keyboard_shortcuts()
    """
    with st.expander("⌨️ Keyboard Shortcuts", expanded=False):
        for category, shortcuts in SHORTCUTS.items():
            st.markdown(f"**{category}:**")
            for key, desc in shortcuts.items():
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.code(key)
                with col2:
                    st.caption(desc)
            st.markdown("---")
