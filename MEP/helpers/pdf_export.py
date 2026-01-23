'''
PDF Export für MEP Präsentation
Generiert ein PDF mit allen Folien und klickbaren Links
'''

from io import BytesIO
from pathlib import Path
import os

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm, mm
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, Image, KeepTogether, ListFlowable, ListItem
    )
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Farben (passend zur Präsentation)
PURPLE_PRIMARY = colors.HexColor('#667eea')
PURPLE_SECONDARY = colors.HexColor('#764ba2')
GRAY_LIGHT = colors.HexColor('#f5f5f5')
GRAY_TEXT = colors.HexColor('#333333')
GRAY_SUBTITLE = colors.HexColor('#666666')


def get_styles():
    """Erstellt die Paragraph-Styles für das PDF"""
    styles = getSampleStyleSheet()

    # Titel-Style (Folientitel)
    styles.add(ParagraphStyle(
        name='SlideTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=PURPLE_PRIMARY,
        spaceAfter=6,
        spaceBefore=0,
        leading=28
    ))

    # Untertitel-Style
    styles.add(ParagraphStyle(
        name='SlideSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=GRAY_SUBTITLE,
        spaceAfter=12,
        spaceBefore=0
    ))

    # Abschnitts-Überschrift
    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=PURPLE_PRIMARY,
        spaceBefore=12,
        spaceAfter=6,
        leading=18
    ))

    # Normaler Text
    styles.add(ParagraphStyle(
        name='SlideText',
        parent=styles['Normal'],
        fontSize=11,
        textColor=GRAY_TEXT,
        spaceAfter=6,
        leading=14
    ))

    # Bullet-Punkt
    styles.add(ParagraphStyle(
        name='BulletText',
        parent=styles['Normal'],
        fontSize=11,
        textColor=GRAY_TEXT,
        leftIndent=15,
        spaceAfter=4,
        leading=14
    ))

    # Zentrierter Text (für Titelfolie)
    styles.add(ParagraphStyle(
        name='CenteredText',
        parent=styles['Normal'],
        fontSize=11,
        textColor=GRAY_TEXT,
        alignment=TA_CENTER,
        spaceAfter=6
    ))

    # Grosser zentrierter Titel
    styles.add(ParagraphStyle(
        name='BigTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=PURPLE_PRIMARY,
        alignment=TA_CENTER,
        spaceAfter=8,
        spaceBefore=20
    ))

    # Link-Style
    styles.add(ParagraphStyle(
        name='Link',
        parent=styles['Normal'],
        fontSize=11,
        textColor=PURPLE_PRIMARY,
        alignment=TA_CENTER,
        spaceAfter=6
    ))

    # Kennzahl gross
    styles.add(ParagraphStyle(
        name='BigNumber',
        parent=styles['Normal'],
        fontSize=24,
        textColor=PURPLE_PRIMARY,
        alignment=TA_CENTER,
        spaceBefore=4,
        spaceAfter=2
    ))

    # Kennzahl Label
    styles.add(ParagraphStyle(
        name='NumberLabel',
        parent=styles['Normal'],
        fontSize=9,
        textColor=GRAY_SUBTITLE,
        alignment=TA_CENTER,
        spaceAfter=8
    ))

    return styles


def add_slide_header(elements, styles, title, subtitle="", slide_number=None, total_slides=12):
    """Fügt einen Folien-Header hinzu"""
    # Titel
    elements.append(Paragraph(title, styles['SlideTitle']))

    # Untertitel (falls vorhanden)
    if subtitle:
        elements.append(Paragraph(subtitle, styles['SlideSubtitle']))

    # Foliennummer (rechts)
    if slide_number:
        elements.append(Paragraph(
            f"<font color='#999999' size='9'>Folie {slide_number} / {total_slides}</font>",
            styles['SlideText']
        ))

    elements.append(Spacer(1, 8))


def add_section(elements, styles, title, emoji=""):
    """Fügt eine Abschnitts-Überschrift hinzu"""
    elements.append(Paragraph(f"{emoji} {title}" if emoji else title, styles['SectionHeader']))


def add_bullet_list(elements, styles, items):
    """Fügt eine Aufzählungsliste hinzu"""
    for item in items:
        elements.append(Paragraph(f"• {item}", styles['BulletText']))


def add_gradient_box(elements, styles, title, content, width=None):
    """Fügt eine farbige Box hinzu (simuliert Gradient-Card)"""
    box_data = [[
        Paragraph(f"<b>{title}</b><br/><br/>{content}", styles['SlideText'])
    ]]

    box_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), PURPLE_PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('ROUNDEDCORNERS', [6, 6, 6, 6]),
    ])

    table = Table(box_data, colWidths=[width or 240])
    table.setStyle(box_style)
    elements.append(table)
    elements.append(Spacer(1, 8))


def generate_presentation_pdf(logo_path=None):
    """
    Generiert ein PDF der gesamten Präsentation.

    Args:
        logo_path: Pfad zum Logo (optional)

    Returns:
        BytesIO buffer mit dem PDF
    """
    if not REPORTLAB_AVAILABLE:
        raise ImportError("ReportLab ist nicht installiert. Bitte installieren mit: pip install reportlab")

    buffer = BytesIO()

    # Querformat für Präsentation
    page_width, page_height = landscape(A4)

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )

    styles = get_styles()
    elements = []

    # ==========================================
    # FOLIE 1: Titelfolie
    # ==========================================
    elements.append(Spacer(1, 40))

    # Logo (falls vorhanden)
    if logo_path and os.path.exists(logo_path):
        try:
            logo = Image(logo_path, width=180, height=60)
            logo.hAlign = 'CENTER'
            elements.append(logo)
            elements.append(Spacer(1, 20))
        except:
            pass

    elements.append(Paragraph("eBKP-H⁺ BIM Kostenklassifizierung", styles['BigTitle']))
    elements.append(Paragraph(
        "Automatische eBKP-H Klassifizierung von BIM-Daten mit KI inkl. Kostenberechnung",
        styles['CenteredText']
    ))
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("<b>Nicole Hitz &amp; Orlando Bassi</b>", styles['CenteredText']))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("TA.BA_DT_PROGR_MM - Digital Twin Programmieren", styles['CenteredText']))
    elements.append(Paragraph("Hochschule Luzern - Technik &amp; Architektur", styles['CenteredText']))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("Modulendprüfung - 27. Januar 2026", styles['CenteredText']))
    elements.append(PageBreak())

    # ==========================================
    # FOLIE 2: Projektübersicht
    # ==========================================
    add_slide_header(elements, styles, "Projektübersicht",
                     "Was ist eBKP-H⁺ und was kann es?", 2)

    add_section(elements, styles, "Ziel des Projekts", "🎯")
    elements.append(Paragraph(
        "Entwicklung einer Streamlit-Webanwendung zur automatischen Klassifizierung "
        "von BIM-Elementen nach dem eBKP-H Standard mittels Claude AI.",
        styles['SlideText']
    ))

    add_section(elements, styles, "Kernfunktionen", "⚡")
    add_bullet_list(elements, styles, [
        "CSV-Upload von BIM-Daten (aus Revit/pyRevit)",
        "KI-gestützte eBKP-H Klassifizierung mit Konfidenzwerten",
        "Manuelle Korrekturmöglichkeit für unsichere Klassifizierungen",
        "Kostenberechnung basierend auf Kennwerten",
        "Export als CSV und PDF"
    ])

    add_section(elements, styles, "Technologie-Stack", "🛠️")
    add_bullet_list(elements, styles, [
        "Frontend: Streamlit (Python)",
        "KI: Claude 3.5 Haiku (Anthropic API)",
        "Datenverarbeitung: Pandas",
        "PDF-Export: ReportLab"
    ])
    elements.append(PageBreak())

    # ==========================================
    # FOLIE 3: Problemstellung
    # ==========================================
    add_slide_header(elements, styles, "Problemstellung",
                     "Warum braucht es eBKP-H⁺?", 3)

    add_section(elements, styles, "Herausforderungen in der Praxis", "❌")
    add_bullet_list(elements, styles, [
        "Manuelle eBKP-Zuordnung ist zeitaufwändig und fehleranfällig",
        "Inkonsistente Klassifizierung zwischen verschiedenen Bearbeitern",
        "Über 10'000 mögliche eBKP-H Codes erschweren die Auswahl",
        "Keine automatisierte Lösung für BIM-Daten verfügbar"
    ])

    add_section(elements, styles, "Unsere Lösung", "✅")
    add_bullet_list(elements, styles, [
        "Automatische Klassifizierung durch KI spart Zeit",
        "Konsistente Ergebnisse durch standardisierten Prozess",
        "Konfidenzwerte zeigen Unsicherheiten transparent auf",
        "Validierung gegen offiziellen eBKP-H Katalog"
    ])
    elements.append(PageBreak())

    # ==========================================
    # FOLIE 4: eBKP-H Erklärung
    # ==========================================
    add_slide_header(elements, styles, "eBKP-H Erklärung",
                     "Der Schweizer Baukostenplan", 4)

    add_section(elements, styles, "Was ist eBKP-H?", "📋")
    elements.append(Paragraph(
        "Der elementbasierte Baukostenplan Hochbau (eBKP-H) ist der Schweizer Standard "
        "für die Gliederung von Baukosten nach Elementen.",
        styles['SlideText']
    ))

    add_section(elements, styles, "Hierarchie-Struktur", "🏗️")
    add_bullet_list(elements, styles, [
        "Hauptgruppe (A-Z): z.B. C = Bauwerk - Rohbau",
        "Elementgruppe (C1-C9): z.B. C2 = Fundation",
        "Elemente (C21-C29): z.B. C21 = Streifenfundamente",
        "Unterelemente: z.B. C21.01 = Betonarbeiten",
        "Details: z.B. C21.01.01 = Beton giessen"
    ])

    add_section(elements, styles, "Wichtige Hauptgruppen", "📊")
    add_bullet_list(elements, styles, [
        "A: Grundstück",
        "B: Vorbereitungsarbeiten",
        "C: Bauwerk - Rohbau",
        "D: Bauwerk - Technik",
        "E: Bauwerk - Ausbau",
        "V/W: Planungs- und Nebenkosten"
    ])
    elements.append(PageBreak())

    # ==========================================
    # FOLIE 5: Architektur
    # ==========================================
    add_slide_header(elements, styles, "Systemarchitektur",
                     "Aufbau der Anwendung", 5)

    add_section(elements, styles, "Drei-Schichten-Architektur", "🏛️")

    # Architektur als Tabelle
    arch_data = [
        ['Schicht', 'Komponenten', 'Technologie'],
        ['Frontend', 'Multi-Page Streamlit App', 'Streamlit, HTML/CSS'],
        ['Logik', 'Klassifizierung, Validierung, Export', 'Python, Pandas'],
        ['Backend', 'Claude API, Session State', 'Anthropic SDK']
    ]

    arch_table = Table(arch_data, colWidths=[120, 200, 150])
    arch_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PURPLE_PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BACKGROUND', (0, 1), (-1, -1), GRAY_LIGHT),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.white),
    ]))
    elements.append(arch_table)
    elements.append(Spacer(1, 12))

    add_section(elements, styles, "Streamlit-Seiten", "📄")
    add_bullet_list(elements, styles, [
        "Startseite mit Workflow-Übersicht",
        "KI-Klassifizierung (Upload, Verarbeitung, Ergebnisse)",
        "BKP-Bearbeitung (manuelle Korrektur)",
        "eBKP-Auswertung (Visualisierung)",
        "Kostenberechnung",
        "Einstellungen (API-Key)"
    ])
    elements.append(PageBreak())

    # ==========================================
    # FOLIE 6: Datenfluss
    # ==========================================
    add_slide_header(elements, styles, "Datenfluss",
                     "Vom Upload zum Ergebnis", 6)

    add_section(elements, styles, "Verarbeitungs-Pipeline", "🔄")

    flow_data = [
        ['1. CSV Upload', '→', '2. Deduplizierung', '→', '3. KI-Klassifizierung'],
        ['', '', '', '', ''],
        ['6. Export', '←', '5. Visualisierung', '←', '4. Validierung']
    ]

    flow_table = Table(flow_data, colWidths=[100, 30, 100, 30, 100])
    flow_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (-1, -1), PURPLE_PRIMARY),
    ]))
    elements.append(flow_table)
    elements.append(Spacer(1, 12))

    add_section(elements, styles, "Session State", "💾")
    elements.append(Paragraph(
        "Alle Daten werden im Streamlit Session State gespeichert und sind so "
        "über alle Seiten hinweg verfügbar. Dies ermöglicht einen nahtlosen "
        "Workflow ohne Datenverlust zwischen den Schritten.",
        styles['SlideText']
    ))
    elements.append(PageBreak())

    # ==========================================
    # FOLIE 7: Workflow
    # ==========================================
    add_slide_header(elements, styles, "Benutzer-Workflow",
                     "Schritt für Schritt", 7)

    workflow_steps = [
        ("1. Daten vorbereiten", "CSV aus Revit/pyRevit exportieren mit Elementtyp und Kategorie"),
        ("2. Upload", "CSV-Datei in die Anwendung hochladen"),
        ("3. Klassifizierung", "KI-gestützte eBKP-H Zuordnung starten"),
        ("4. Überprüfung", "Ergebnisse prüfen, bei Bedarf korrigieren"),
        ("5. Auswertung", "Visualisierung nach Hauptgruppen"),
        ("6. Export", "Ergebnisse als CSV oder PDF exportieren")
    ]

    for step, desc in workflow_steps:
        elements.append(Paragraph(f"<b>{step}</b>: {desc}", styles['SlideText']))

    elements.append(PageBreak())

    # ==========================================
    # FOLIE 8: KI-Klassifizierung
    # ==========================================
    add_slide_header(elements, styles, "KI-Klassifizierung",
                     "Claude AI im Einsatz", 8)

    add_section(elements, styles, "Modell: Claude 3.5 Haiku", "🤖")
    add_bullet_list(elements, styles, [
        "Schnellstes Modell der Claude-Familie",
        "Optimiert für strukturierte Ausgaben",
        "Kosteneffizient für Batch-Verarbeitung"
    ])

    add_section(elements, styles, "Prompt Engineering", "📝")
    elements.append(Paragraph(
        "Der Prompt enthält den vollständigen eBKP-H Katalog als Referenz. "
        "Das Modell gibt strukturierte JSON-Antworten mit Code, Beschreibung "
        "und Konfidenzwert (0-1) zurück.",
        styles['SlideText']
    ))

    add_section(elements, styles, "Kostenoptimierung", "💰")
    add_bullet_list(elements, styles, [
        "Batch-Verarbeitung: Mehrere Elemente pro API-Call",
        "Prompt Caching: Wiederverwendung des Katalogs",
        "Deduplizierung: Gleiche Elemente nur einmal klassifizieren",
        "Einsparung: Bis zu 95% gegenüber Einzelabfragen"
    ])
    elements.append(PageBreak())

    # ==========================================
    # FOLIE 9: Code Highlights
    # ==========================================
    add_slide_header(elements, styles, "Code Highlights",
                     "Interessante Implementierungsdetails", 9)

    add_section(elements, styles, "BKP Classifier", "🔧")
    elements.append(Paragraph(
        "Die Klasse <font face='Courier'>BKPClassifier</font> kapselt die gesamte "
        "Kommunikation mit der Claude API und bietet Methoden für Einzel- und "
        "Batch-Klassifizierung.",
        styles['SlideText']
    ))

    add_section(elements, styles, "Session State Management", "💾")
    elements.append(Paragraph(
        "Zentralisierte Verwaltung aller Zustandsvariablen über "
        "<font face='Courier'>session_state.py</font> mit typisierteren Konstanten "
        "und Helper-Funktionen.",
        styles['SlideText']
    ))

    add_section(elements, styles, "Validierung", "✅")
    elements.append(Paragraph(
        "Jeder klassifizierte Code wird gegen den offiziellen eBKP-H Katalog "
        "validiert. Ungültige Codes werden markiert und können manuell "
        "korrigiert werden.",
        styles['SlideText']
    ))
    elements.append(PageBreak())

    # ==========================================
    # FOLIE 10: Live Demo
    # ==========================================
    add_slide_header(elements, styles, "Live Demo",
                     "Die Anwendung in Aktion", 10)

    elements.append(Spacer(1, 20))
    elements.append(Paragraph(
        "Diese Folie zeigt in der Präsentation eine Live-Demonstration der Anwendung.",
        styles['CenteredText']
    ))
    elements.append(Spacer(1, 20))

    add_section(elements, styles, "Demo-Ablauf", "🎬")
    add_bullet_list(elements, styles, [
        "1. CSV-Upload mit Beispieldaten",
        "2. Start der KI-Klassifizierung",
        "3. Anzeige der Ergebnisse mit Konfidenzwerten",
        "4. Manuelle Korrektur eines Elements",
        "5. Visualisierung nach Hauptgruppen",
        "6. PDF-Export"
    ])
    elements.append(PageBreak())

    # ==========================================
    # FOLIE 11: Zusammenfassung
    # ==========================================
    add_slide_header(elements, styles, "Zusammenfassung",
                     "Was wir erreicht haben", 11)

    add_section(elements, styles, "Erreichte Ziele", "✅")
    add_bullet_list(elements, styles, [
        "Automatische eBKP-Klassifizierung mit Claude AI",
        "Vollständiger Workflow von Upload bis Export",
        "Kostenoptimierte API-Nutzung (Batch, Caching)",
        "Validierung gegen offiziellen eBKP-H Katalog",
        "Benutzerfreundliches UI mit Streamlit"
    ])

    add_section(elements, styles, "Projekt-Kennzahlen", "📊")

    # Kennzahlen als Tabelle
    stats_data = [
        ['10\'210', '13', '~95%', '5'],
        ['eBKP-H Codes', 'Streamlit Seiten', 'Kosteneinsparung', 'Hierarchie-Ebenen']
    ]

    stats_table = Table(stats_data, colWidths=[100, 100, 100, 100])
    stats_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, 0), 18),
        ('FONTSIZE', (0, 1), (-1, 1), 8),
        ('TEXTCOLOR', (0, 0), (-1, 0), PURPLE_PRIMARY),
        ('TEXTCOLOR', (0, 1), (-1, 1), GRAY_SUBTITLE),
    ]))
    elements.append(stats_table)
    elements.append(PageBreak())

    # ==========================================
    # FOLIE 12: Fragen / Ende
    # ==========================================
    elements.append(Spacer(1, 60))
    elements.append(Paragraph("?", ParagraphStyle(
        'BigQuestion',
        parent=styles['Normal'],
        fontSize=120,
        textColor=PURPLE_PRIMARY,
        alignment=TA_CENTER,
        leading=130
    )))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(
        "Vielen Dank für Ihre Aufmerksamkeit!",
        styles['BigTitle']
    ))
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("<b>Nicole Hitz &amp; Orlando Bassi</b>", styles['CenteredText']))
    elements.append(Paragraph("TA.BA_DT_PROGR_MM - Digital Twin Programmieren", styles['CenteredText']))
    elements.append(Paragraph("Hochschule Luzern - Technik &amp; Architektur", styles['CenteredText']))
    elements.append(Spacer(1, 20))

    # GitHub Link (klickbar!)
    elements.append(Paragraph(
        '<a href="https://github.com/NH-HSLU/TA.BA_DT_PROGR" color="#667eea">'
        '📂 GitHub Repository: github.com/NH-HSLU/TA.BA_DT_PROGR</a>',
        styles['Link']
    ))

    # PDF generieren
    doc.build(elements)
    buffer.seek(0)

    return buffer


def is_available():
    """Prüft ob ReportLab verfügbar ist"""
    return REPORTLAB_AVAILABLE
