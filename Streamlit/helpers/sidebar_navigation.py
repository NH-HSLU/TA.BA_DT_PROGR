"""
Gemeinsame Sidebar-Navigation für alle Pages
"""

import streamlit as st
from datetime import datetime
import os


def render_sidebar():
    """Rendert die einheitliche Sidebar-Navigation für alle Pages"""

    with st.sidebar:
        # Logo/Titel - Prominent mit Gradient
        st.markdown("""
        <div style="
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        ">
            <h2 style="margin: 0; font-size: 1.5rem;">🏗️ eBKP-H Suite</h2>
            <p style="margin: 0; font-size: 0.8rem; opacity: 0.9;">BIM-Klassifizierung</p>
        </div>
        """, unsafe_allow_html=True)

        # Status-Übersicht
        st.markdown("### 📊 Status")

        # API-Status
        if 'api_key' in st.session_state and st.session_state.api_key:
            if st.session_state.get('api_key_validated', False):
                st.success("✓ API-Key aktiv", icon="🔑")
            else:
                st.warning("⚠️ API-Key nicht validiert", icon="🔑")
        else:
            env_key = os.getenv('ANTHROPIC_API_KEY')
            if env_key:
                st.success("✓ API-Key (.env)", icon="🔑")
            else:
                st.info("ℹ️ Kein API-Key", icon="🔑")

        # Kostenermittlung-Status
        if 'cost_estimation_config' in st.session_state and st.session_state.cost_estimation_config.get('selected'):
            config = st.session_state.cost_estimation_config
            st.success(f"✓ {config['name'][:20]}...", icon="🏗️")
            st.caption(f"Toleranz: ±{config['tolerance']}% | Level: {config['ebkp_depth']}")
        else:
            st.info("ℹ️ Keine Stufe gewählt", icon="🏗️")

        # Daten-Status
        if 'classification_results' in st.session_state and st.session_state.classification_results is not None:
            df = st.session_state.classification_results
            st.success(f"✓ {len(df)} Elemente", icon="📄")
        else:
            st.info("ℹ️ Keine Daten geladen", icon="📄")


def render_page_header(title: str, subtitle: str = "", icon: str = ""):
    """Rendert einen einheitlichen Page-Header"""

    if icon:
        st.markdown(f'<p style="font-size: 2.5rem; font-weight: bold; text-align: center;">{icon} {title}</p>',
                    unsafe_allow_html=True)
    else:
        st.markdown(f'<p style="font-size: 2.5rem; font-weight: bold; text-align: center;">{title}</p>',
                    unsafe_allow_html=True)

    if subtitle:
        st.markdown(f'<p style="font-size: 1.1rem; opacity: 0.7; margin-bottom: 1rem; text-align: center;">{subtitle}</p>',
                    unsafe_allow_html=True)

def render_divider(style: str = "gradient"):
    """
    Rendert einen stilisierten Divider

    Args:
        style: 'gradient' (default), 'simple', 'dotted', 'thick', 'section'
    """

    if style == "gradient":
        st.markdown("""
        <div style="
            height: 2px;
            background: linear-gradient(90deg,
                rgba(102, 126, 234, 0) 0%,
                rgba(102, 126, 234, 0.8) 50%,
                rgba(102, 126, 234, 0) 100%);
            margin: 1.5rem 0;
        "></div>
        """, unsafe_allow_html=True)

    elif style == "dotted":
        st.markdown("""
        <div style="
            border-top: 3px dotted #667eea;
            margin: 1.5rem 0;
            opacity: 0.4;
        "></div>
        """, unsafe_allow_html=True)

    elif style == "thick":
        st.markdown("""
        <div style="
            height: 4px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 2px;
            margin: 2rem 0;
        "></div>
        """, unsafe_allow_html=True)

    elif style == "section":
        st.markdown("""
        <div style="
            height: 1px;
            background: linear-gradient(90deg,
                transparent 0%,
                #667eea 20%,
                #667eea 80%,
                transparent 100%);
            margin: 2rem 0;
        "></div>
        """, unsafe_allow_html=True)

    else:  # simple
        st.markdown("""
        <div style="
            border-top: 1px solid rgba(102, 126, 234, 0.2);
            margin: 1.5rem 0;
        "></div>
        """, unsafe_allow_html=True)


def render_page_footer(show_version: bool = True, show_date: bool = True):
    """
    Rendert einen schönen Page-Footer mit Gradient-Design

    Args:
        show_version: Zeigt die Versionsnummer
        show_date: Zeigt das aktuelle Datum
    """

    version_text = "v1.0" if show_version else ""
    date_text = datetime.now().strftime('%d.%m.%Y') if show_date else ""

    # Gradient Divider vor Footer
    st.markdown("""
    <div style="
        height: 2px;
        background: linear-gradient(90deg,
            rgba(102, 126, 234, 0) 0%,
            rgba(102, 126, 234, 0.6) 50%,
            rgba(102, 126, 234, 0) 100%);
        margin: 3rem 0 1.5rem 0;
    "></div>
    """, unsafe_allow_html=True)

    # Footer Content
    footer_parts = []
    if show_version:
        footer_parts.append(f"🏗️ eBKP-H Suite {version_text}")
    if show_date:
        footer_parts.append(f"📅 {date_text}")
    footer_parts.append("🎓 TA.BA_DT_PROGR")

    footer_text = " | ".join(footer_parts)

    st.markdown(f"""
    <div style="
        text-align: center;
        padding: 1rem;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border-radius: 0.5rem;
        font-size: 0.85rem;
        color: var(--text-color);
        opacity: 0.7;
        margin-bottom: 1rem;
    ">
        {footer_text}
    </div>
    """, unsafe_allow_html=True)


def render_sidebar_footer():
    """Rendert einen kompakten Footer in der Sidebar"""

    st.markdown("---")

    st.markdown("""
    <div style="
        text-align: center;
        padding: 0.5rem;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border-radius: 0.3rem;
        font-size: 0.75rem;
        color: rgba(0, 0, 0, 0.5);
        margin-top: 1rem;
    ">
        🏗️ eBKP-H Suite v1.0<br>
        🎓 TA.BA_DT_PROGR
    </div>
    """, unsafe_allow_html=True)
