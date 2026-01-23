'''
Presentation Helpers
Helper-Funktionen für die MEP Präsentation
'''

import streamlit as st
import os
import base64

# Farben (konsistent mit Hauptapp)
COLORS = {
    'primary': '#667eea',
    'secondary': '#764ba2',
    'success': '#43e97b',
    'warning': '#fee140',
    'error': '#f5576c',
    'info': '#4facfe',
    'cyan': '#00f2fe',
    'pink': '#f093fb',
    'orange': '#fa709a',
    'dark': '#330867'
}

# Gradient-Definitionen
GRADIENTS = {
    'purple': f"linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%)",
    'cyan': f"linear-gradient(135deg, {COLORS['info']} 0%, {COLORS['cyan']} 100%)",
    'green': f"linear-gradient(135deg, {COLORS['success']} 0%, #38f9d7 100%)",
    'orange': f"linear-gradient(135deg, {COLORS['orange']} 0%, {COLORS['warning']} 100%)",
    'pink': f"linear-gradient(135deg, {COLORS['pink']} 0%, {COLORS['error']} 100%)",
    'dark': f"linear-gradient(135deg, #30cfd0 0%, {COLORS['dark']} 100%)"
}

# Folien-Liste für Navigation
SLIDES = [
    ("praesentation_app", "Titel"),
    ("01_Projektueberblick", "Projektübersicht"),
    ("02_Problemstellung", "Problemstellung"),
    ("03_eBKP_Erklaerung", "eBKP-H Erklärung"),
    ("04_Architektur", "Architektur"),
    ("05_Datenfluss", "Datenfluss"),
    ("06_Workflow", "Workflow"),
    ("07_KI_Klassifizierung", "KI-Klassifizierung"),
    ("09_Code_Highlights", "Code Highlights"),
    ("10_Live_Demo", "Live Demo"),
    ("11_Zusammenfassung", "Zusammenfassung"),
    ("12_Fragen", "Fragen")
]


def get_base_css():
    """Gibt das Basis-CSS für alle Präsentationsfolien zurück - PowerPoint Style
    Der gesamte .block-container wird als Slide gestylt!
    """
    return """
    <style>
        /* Sidebar komplett ausblenden */
        [data-testid="stSidebar"] { display: none; }
        [data-testid="stSidebarCollapsedControl"] { display: none; }

        /* Dunkler Hintergrund für die gesamte App */
        .stApp {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%) !important;
        }

        /* ============================================
           HAUPTCONTAINER = POWERPOINT SLIDE
           ============================================ */
        .main .block-container {
            background: white !important;
            border-radius: 12px !important;
            box-shadow: 0 25px 80px rgba(0,0,0,0.5) !important;
            padding: 2rem 2.5rem 2.5rem 2.5rem !important;
            margin: 1rem auto !important;
            max-width: 1150px !important;
            min-height: 78vh !important;
            position: relative !important;
        }

        /* Gradient Bar am unteren Rand der Slide */
        .main .block-container::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 6px;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #667eea 100%);
            border-radius: 0 0 12px 12px;
        }

        /* ============================================
           SLIDE HEADER
           ============================================ */
        .slide-header {
            text-align: left;
            margin-bottom: 1rem;
            padding-bottom: 0.8rem;
            border-bottom: 3px solid;
            border-image: linear-gradient(90deg, #667eea, #764ba2, transparent) 1;
        }
        .slide-title {
            font-size: 2rem;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.2rem;
            line-height: 1.2;
        }
        .slide-subtitle {
            font-size: 1rem;
            opacity: 0.6;
            font-weight: 400;
        }

        /* Foliennummer oben rechts in der Slide */
        .slide-number {
            position: absolute;
            top: 1.2rem;
            right: 1.5rem;
            font-size: 0.85rem;
            opacity: 0.4;
            font-weight: 600;
            color: #667eea;
        }

        /* ============================================
           NAVIGATION (ausserhalb der Slide)
           ============================================ */
        .nav-info {
            color: rgba(255,255,255,0.8) !important;
            font-size: 0.9rem;
            font-weight: 500;
            text-align: center;
        }

        /* Navigation Buttons */
        .stButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 2rem !important;
            padding: 0.4rem 1.2rem !important;
            font-weight: 600 !important;
            font-size: 0.85rem !important;
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }

        /* ============================================
           CONTENT ELEMENTE
           ============================================ */

        /* Gradient Cards */
        .gradient-card {
            padding: 1rem 1.2rem;
            border-radius: 0.6rem;
            color: white;
            margin: 0.4rem 0;
            min-height: 100px;
        }
        .gradient-card h3 {
            font-size: 1rem;
            margin-bottom: 0.5rem;
            font-weight: 600;
        }
        .gradient-card p {
            opacity: 0.95;
            line-height: 1.4;
            font-size: 0.85rem;
        }

        .card-purple { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .card-cyan { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
        .card-green { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
        .card-orange { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }
        .card-pink { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
        .card-dark { background: linear-gradient(135deg, #30cfd0 0%, #330867 100%); }

        /* Content Box */
        .content-box {
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%);
            padding: 1rem 1.2rem;
            border-radius: 0.5rem;
            border-left: 4px solid #667eea;
            margin: 0.6rem 0;
        }

        /* Badge */
        .badge {
            display: inline-block;
            padding: 0.2rem 0.6rem;
            border-radius: 1rem;
            font-size: 0.75rem;
            font-weight: 600;
            margin: 0.1rem;
        }
        .badge-primary { background: #667eea; color: white; }
        .badge-success { background: #43e97b; color: #1a1a1a; }
        .badge-info { background: #4facfe; color: white; }
        .badge-warning { background: #fee140; color: #1a1a1a; }

        /* Divider */
        .slide-divider {
            height: 2px;
            background: linear-gradient(90deg, transparent, rgba(102,126,234,0.3), rgba(118,75,162,0.3), transparent);
            margin: 1rem 0;
            border: none;
        }

        /* Big Number */
        .big-number {
            font-size: 2.8rem;
            font-weight: 800;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-align: center;
        }

        /* Code Block Enhancement */
        .code-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 0.3rem 0.8rem;
            border-radius: 0.4rem 0.4rem 0 0;
            font-size: 0.8rem;
            font-weight: 600;
        }

        /* Plotly Charts Hintergrund transparent */
        .js-plotly-plot .plotly .main-svg {
            background: transparent !important;
        }

        /* Streamlit Markdown h3 */
        .main .block-container h3 {
            font-size: 1.1rem !important;
            color: #667eea !important;
            margin-top: 0.8rem !important;
            margin-bottom: 0.5rem !important;
        }

        /* Kleinere Schrift für Slide-Inhalte */
        .main .block-container p,
        .main .block-container li {
            font-size: 0.9rem !important;
        }

        /* Streamlit Info/Warning Boxen kompakter */
        .stAlert {
            padding: 0.6rem 1rem !important;
            font-size: 0.85rem !important;
        }

        /* Tabs kompakter */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
        }
        .stTabs [data-baseweb="tab"] {
            font-size: 0.85rem !important;
            padding: 0.4rem 0.8rem !important;
        }
    </style>
    """


def start_slide(title: str, subtitle: str = "", slide_number: int = None, total_slides: int = 12):
    """Rendert den Slide-Header mit Titel, Untertitel und Foliennummer.
    Der gesamte block-container wird via CSS als Slide gestylt.
    """
    # Foliennummer oben rechts (absolut positioniert via CSS)
    slide_num_html = ""
    if slide_number and total_slides:
        slide_num_html = f'<div class="slide-number">{slide_number} / {total_slides}</div>'

    # Header
    st.markdown(f"""
    {slide_num_html}
    <div class="slide-header">
        <div class="slide-title">{title}</div>
        <div class="slide-subtitle">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)


def end_slide():
    """Nicht mehr benötigt - der block-container ist die Slide.
    Behalten für Rückwärtskompatibilität.
    """
    pass


def render_slide_header(title: str, subtitle: str = "", slide_number: int = None, total_slides: int = None):
    """Rendert den Slide-Header mit Titel und optionalem Untertitel (Legacy)"""
    slide_info = ""
    if slide_number and total_slides:
        slide_info = f'<div class="slide-number">Folie {slide_number} von {total_slides}</div>'

    st.markdown(f"""
    <div class="slide-header">
        <div class="slide-title">{title}</div>
        <div class="slide-subtitle">{subtitle}</div>
        {slide_info}
    </div>
    """, unsafe_allow_html=True)


def render_slide_navigation(current_slide: int, total_slides: int = 12):
    """Rendert die Navigation unter der Slide"""
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if current_slide > 1:
            if st.button("← Zurück", key="nav_prev", width="stretch"):
                prev_slide = SLIDES[current_slide - 2][0]
                if current_slide == 2:
                    st.switch_page("praesentation_app.py")
                else:
                    st.switch_page(f"pages/{prev_slide}.py")

    with col2:
        st.markdown(f"""
        <div class="nav-info" style="text-align: center;">
            ● Folie {current_slide} von {total_slides} ●
        </div>
        """, unsafe_allow_html=True)

    with col3:
        if current_slide < total_slides:
            if st.button("Weiter →", key="nav_next", width="stretch"):
                next_slide = SLIDES[current_slide][0]
                st.switch_page(f"pages/{next_slide}.py")


def render_divider():
    """Rendert einen Gradient-Divider"""
    st.markdown('<hr class="slide-divider">', unsafe_allow_html=True)


def render_gradient_card(title: str, content: str, color: str = "purple", icon: str = ""):
    """Rendert eine Gradient-Card"""
    icon_html = f'<span style="font-size: 2rem; display: block; margin-bottom: 0.5rem;">{icon}</span>' if icon else ""
    st.markdown(f"""
    <div class="gradient-card card-{color}">
        {icon_html}
        <h3>{title}</h3>
        <p>{content}</p>
    </div>
    """, unsafe_allow_html=True)


def render_badge(text: str, style: str = "primary"):
    """Rendert ein Badge"""
    return f'<span class="badge badge-{style}">{text}</span>'


def render_badges(badges: list):
    """Rendert mehrere Badges"""
    html = " ".join([render_badge(b[0], b[1]) for b in badges])
    st.markdown(html, unsafe_allow_html=True)


def render_content_box(content: str, title: str = ""):
    """Rendert eine Content-Box mit Highlight"""
    title_html = f'<strong>{title}</strong><br>' if title else ""
    st.markdown(f"""
    <div class="content-box">
        {title_html}{content}
    </div>
    """, unsafe_allow_html=True)


def render_big_number(number: str, label: str = ""):
    """Rendert eine grosse Zahl mit optionalem Label"""
    st.markdown(f"""
    <div class="big-number">{number}</div>
    <div style="text-align: center; opacity: 0.7; font-size: 1.1rem;">{label}</div>
    """, unsafe_allow_html=True)


def render_code_block(code: str, language: str = "python", title: str = ""):
    """Rendert einen Code-Block mit optionalem Titel"""
    if title:
        st.markdown(f'<div class="code-header">{title}</div>', unsafe_allow_html=True)
    st.code(code, language=language)


def get_logo_html(logo_hell_path: str, logo_dunkel_path: str, max_width: str = "400px"):
    """Gibt das HTML für Theme-aware Logo zurück"""
    def get_base64_image(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()

    if os.path.exists(logo_hell_path) and os.path.exists(logo_dunkel_path):
        b64_hell = get_base64_image(logo_hell_path)
        b64_dunkel = get_base64_image(logo_dunkel_path)

        return f"""
        <style>
            .logo-container {{
                display: flex;
                justify-content: center;
                align-items: center;
                width: 100%;
            }}
            .logo-container img {{
                max-width: {max_width};
                height: auto;
            }}
            .logo-dark {{ display: none; }}
            .logo-light {{ display: block; }}
        </style>
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
        """
    return "<p>Logo nicht gefunden</p>"


def init_slide_page(page_title: str):
    """Initialisiert eine Slide-Page mit Standard-Einstellungen"""
    st.set_page_config(
        page_title=f"MEP - {page_title}",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    st.markdown(get_base_css(), unsafe_allow_html=True)
