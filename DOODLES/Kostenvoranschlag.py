import streamlit as st
from datetime import datetime
import base64

# Seitenkonfiguration
st.set_page_config(page_title="Kostenvoranschlag Generator", layout="wide")

# Session State initialisieren
if 'bkp_items' not in st.session_state:
    st.session_state.bkp_items = {}

# BKP-Struktur gemäss Schweizer Standard
BKP_STRUCTURE = {
    "1": {"name": "Vorbereitungsarbeiten", "subcategories": {
        "10": "Bestandesaufnahmen, Baugrunduntersuchungen",
        "101": "Bestandesaufnahmen"
    }},
    "2": {"name": "Gebäude", "subcategories": {
        "21": "Rohbau 1",
        "211": "Baumeisterarbeiten",
        "214": "Montagebau in Holz",
        "22": "Rohbau 2",
        "221": "Fenster, Aussentüren, Tore",
        "222": "Spenglerarbeiten",
        "224": "Bedachungsarbeiten",
        "226": "Fassadenputze",
        "228": "Äussere Abschlüsse, Sonnenschutz",
        "23": "Elektroanlagen",
        "230": "Elektroinstallation",
        "233": "Leuchten und Lampen",
        "24": "Heizungs-, Lüftungs-, Klimaanlagen",
        "240": "Heizungsanlage",
        "25": "Sanitäranlagen",
        "250": "Sanitärinstallation",
        "258": "Kücheneinrichtungen",
        "27": "Ausbau 1",
        "271": "Gipserarbeiten",
        "272": "Metallbauarbeiten",
        "273": "Schreinerarbeiten",
        "275": "Schliessanlagen",
        "28": "Ausbau 2",
        "281": "Bodenbeläge",
        "282": "Wandbeläge, Wandbekleidungen",
        "285": "Innere Oberflächenbehandlungen",
        "287": "Baureinigung",
        "289": "Baunebenkosten",
        "29": "Honorare",
        "291": "Architekt",
        "292": "Bauingenieur",
        "293": "Elektroingenieur",
        "294": "HLK-Ingenieur",
        "295": "Sanitäringenieur",
        "296": "Spezialisten"
    }},
    "5": {"name": "Baunebenkosten und Übergangskonten", "subcategories": {
        "51": "Bewilligungen, Gebühren",
        "511": "Bewilligungen, Baugespann (Gebühren)",
        "512": "Anschlussgebühren",
        "52": "Muster, Modelle, Vervielfältigungen, Dokumentation",
        "524": "Vervielfältigungen, Plankopien",
        "525": "Dokumentation",
        "53": "Versicherungen",
        "531": "Bauzeitversicherungen"
    }}
}

def format_currency(value):
    """Formatiert Zahlen im Schweizer Format"""
    return f"{value:,.2f}".replace(",", "'").replace(".", ",").replace(",", ".", 1)

def create_html_report(data):
    """Erstellt HTML-Bericht basierend auf den eingegebenen Daten"""
    
    # BKP-Items sortieren und formatieren
    bkp_rows = ""
    total = 0
    
    for bkp_num in sorted(data['bkp_items'].keys()):
        item = data['bkp_items'][bkp_num]
        bkp_rows += f"""
        <tr>
            <td>{bkp_num}</td>
            <td>{item['text']}</td>
            <td>{item['comment']}</td>
            <td style="text-align: right;">{format_currency(item['amount'])}</td>
        </tr>
        """
        total += item['amount']
    
    mwst_rate = data.get('mwst_rate', 8.1)
    mwst_amount = total * (mwst_rate / 100)
    total_with_mwst = total + mwst_amount
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{
                size: A4;
                margin: 2cm;
            }}
            body {{
                font-family: Arial, Helvetica, sans-serif;
                font-size: 10pt;
                line-height: 1.4;
            }}
            .header {{
                margin-bottom: 20px;
            }}
            .company-name {{
                font-size: 16pt;
                font-weight: bold;
                margin-bottom: 10px;
            }}
            .title {{
                font-size: 14pt;
                font-weight: bold;
                margin: 20px 0 10px 0;
            }}
            .info-section {{
                display: flex;
                justify-content: space-between;
                margin: 20px 0;
            }}
            .info-box {{
                width: 48%;
            }}
            .info-box h3 {{
                font-size: 11pt;
                font-weight: bold;
                margin-bottom: 5px;
            }}
            .info-box p {{
                margin: 3px 0;
                font-size: 9pt;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}
            th {{
                background-color: #f0f0f0;
                padding: 8px;
                text-align: left;
                font-weight: bold;
                border: 1px solid #ddd;
            }}
            td {{
                padding: 6px 8px;
                border: 1px solid #ddd;
            }}
            .total-row {{
                font-weight: bold;
                background-color: #f9f9f9;
            }}
            .final-total {{
                font-weight: bold;
                background-color: #e0e0e0;
                font-size: 11pt;
            }}
            @media print {{
                body {{
                    margin: 0;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="company-name">{data['firma_name']}</div>
            <div>{data['firma_adresse']}</div>
            <div>Tel: {data['firma_tel']}</div>
            <div>Email: {data['firma_email']}</div>
        </div>
        
        <div class="title">Kostenvoranschlag</div>
        <div>Projekt: {data['projekt_name']}</div>
        <div>Stand: {datetime.now().strftime('%d. %B %Y')}</div>
        
        <div class="info-section" style="margin-top: 30px;">
            <div class="info-box">
                <h3>Bauherrschaft:</h3>
                <p>{data['bauherr_name']}</p>
                <p>{data['bauherr_adresse']}</p>
                <p>Tel: {data['bauherr_tel']}</p>
                <p>Email: {data['bauherr_email']}</p>
            </div>
            <div class="info-box">
                <h3>Planer:</h3>
                <p>{data['planer_name']}</p>
                <p>{data['planer_adresse']}</p>
                <p>Tel: {data['planer_tel']}</p>
                <p>Email: {data['planer_email']}</p>
            </div>
        </div>
        
        <div class="info-section">
            <div class="info-box">
                <h3>Bauleitung:</h3>
                <p>{data['bauleitung_name']}</p>
                <p>{data['bauleitung_adresse']}</p>
                <p>Tel: {data['bauleitung_tel']}</p>
                <p>Email: {data['bauleitung_email']}</p>
            </div>
            <div class="info-box">
                <h3>KV-Genauigkeit:</h3>
                <p>{data['kv_genauigkeit']}</p>
            </div>
        </div>
        
        <div style="page-break-before: always;"></div>
        
        <div class="title">Kostenvoranschlag/Baubeschrieb</div>
        
        <table>
            <thead>
                <tr>
                    <th style="width: 15%;">BKP</th>
                    <th style="width: 40%;">Text</th>
                    <th style="width: 25%;">Kommentar</th>
                    <th style="width: 20%; text-align: right;">Betrag</th>
                </tr>
            </thead>
            <tbody>
                {bkp_rows}
                <tr class="total-row">
                    <td colspan="3">Total</td>
                    <td style="text-align: right;">{format_currency(total)}</td>
                </tr>
                <tr>
                    <td colspan="3">MwSt {mwst_rate}%</td>
                    <td style="text-align: right;">{format_currency(mwst_amount)}</td>
                </tr>
                <tr class="final-total">
                    <td colspan="3">Total inklusive {mwst_rate}% MwSt</td>
                    <td style="text-align: right;">{format_currency(total_with_mwst)}</td>
                </tr>
            </tbody>
        </table>
    </body>
    </html>
    """
    return html

# Hauptanwendung
st.title("Kostenvoranschlag Generator (BKP)")

# Tabs für verschiedene Bereiche
tab1, tab2, tab3 = st.tabs(["Projektinformationen", "BKP-Positionen", "Export"])

with tab1:
    st.header("Projektinformationen")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Firma/Ersteller")
        firma_name = st.text_input("Firmenname", value="REALPLAN AG")
        firma_adresse = st.text_input("Firmenadresse", value="Schaffhauserstrasse 473, 8052 Zürich")
        firma_tel = st.text_input("Telefon Firma", value="+41-44-306 70 00")
        firma_email = st.text_input("Email Firma", value="info@realplan-ag.ch")
        
        st.subheader("Projekt")
        projekt_name = st.text_input("Projektname", value="")
        kv_genauigkeit = st.text_input("KV-Genauigkeit", value="+/- 10%")
        mwst_rate = st.number_input("MwSt-Satz (%)", value=8.1, step=0.1)
    
    with col2:
        st.subheader("Bauherrschaft")
        bauherr_name = st.text_input("Name Bauherr", value="")
        bauherr_adresse = st.text_input("Adresse Bauherr", value="")
        bauherr_tel = st.text_input("Telefon Bauherr", value="")
        bauherr_email = st.text_input("Email Bauherr", value="")
        
        st.subheader("Planer")
        planer_name = st.text_input("Name Planer", value="")
        planer_adresse = st.text_input("Adresse Planer", value="")
        planer_tel = st.text_input("Telefon Planer", value="")
        planer_email = st.text_input("Email Planer", value="")
        
        st.subheader("Bauleitung")
        bauleitung_name = st.text_input("Name Bauleitung", value="")
        bauleitung_adresse = st.text_input("Adresse Bauleitung", value="")
        bauleitung_tel = st.text_input("Telefon Bauleitung", value="")
        bauleitung_email = st.text_input("Email Bauleitung", value="")

with tab2:
    st.header("BKP-Positionen")
    
    # BKP-Position hinzufügen
    st.subheader("Neue Position hinzufügen")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        bkp_number = st.text_input("BKP-Nummer", key="new_bkp")
        bkp_text = st.text_input("Beschreibung", key="new_text")
    
    with col2:
        calculation_method = st.radio(
            "Berechnungsmethode",
            ["Fester Betrag", "Prozentsatz", "Automatische Berechnung (Code)"],
            key="calc_method"
        )
        
        if calculation_method == "Fester Betrag":
            amount = st.number_input("Betrag (CHF)", min_value=0.0, step=100.0, key="fixed_amount")
        elif calculation_method == "Prozentsatz":
            base_amount = st.number_input("Basisbetrag (CHF)", min_value=0.0, step=100.0, key="base_amount")
            percentage = st.number_input("Prozentsatz (%)", min_value=0.0, max_value=100.0, step=0.5, key="percentage")
            amount = base_amount * (percentage / 100)
            st.info(f"Berechneter Betrag: CHF {format_currency(amount)}")
        else:
            st.text_area("Python-Code zur Berechnung", 
                        placeholder="# Beispiel:\n# amount = grundfläche * preis_pro_m2\namount = 0",
                        key="python_code")
            amount = st.number_input("Berechneter Betrag (CHF)", min_value=0.0, step=100.0, key="calculated_amount")
    
    with col3:
        comment = st.text_area("Kommentar", key="new_comment")
        
        if st.button("Position hinzufügen"):
            if bkp_number and bkp_text:
                st.session_state.bkp_items[bkp_number] = {
                    'text': bkp_text,
                    'amount': amount,
                    'comment': comment,
                    'calculation_method': calculation_method
                }
                st.success(f"Position {bkp_number} hinzugefügt!")
                st.rerun()
    
    # Vorhandene Positionen anzeigen
    st.subheader("Vorhandene BKP-Positionen")
    
    if st.session_state.bkp_items:
        # Gruppierung nach Hauptkategorien
        grouped_items = {}
        for bkp_num, item in st.session_state.bkp_items.items():
            main_cat = bkp_num[0]
            if main_cat not in grouped_items:
                grouped_items[main_cat] = []
            grouped_items[main_cat].append((bkp_num, item))
        
        total = 0
        for main_cat in sorted(grouped_items.keys()):
            st.markdown(f"### {main_cat} - {BKP_STRUCTURE.get(main_cat, {}).get('name', 'Weitere Positionen')}")
            
            for bkp_num, item in sorted(grouped_items[main_cat]):
                col1, col2, col3, col4 = st.columns([1, 3, 2, 1])
                with col1:
                    st.write(f"**{bkp_num}**")
                with col2:
                    st.write(item['text'])
                with col3:
                    st.write(f"CHF {format_currency(item['amount'])}")
                with col4:
                    if st.button("🗑️", key=f"del_{bkp_num}"):
                        del st.session_state.bkp_items[bkp_num]
                        st.rerun()
                
                if item['comment']:
                    st.caption(f"💬 {item['comment']}")
                
                total += item['amount']
        
        st.markdown("---")
        st.markdown(f"### Zwischentotal: CHF {format_currency(total)}")
        mwst = total * (mwst_rate / 100)
        st.markdown(f"### MwSt ({mwst_rate}%): CHF {format_currency(mwst)}")
        st.markdown(f"### **Total inkl. MwSt: CHF {format_currency(total + mwst)}**")
    else:
        st.info("Noch keine BKP-Positionen erfasst.")

with tab3:
    st.header("Export")
    
    st.write("Exportieren Sie den Kostenvoranschlag als HTML-Datei (kann im Browser als PDF gedruckt werden).")
    
    if st.button("HTML generieren", type="primary"):
        if not st.session_state.bkp_items:
            st.error("Bitte fügen Sie mindestens eine BKP-Position hinzu.")
        else:
            try:
                data = {
                    'firma_name': firma_name,
                    'firma_adresse': firma_adresse,
                    'firma_tel': firma_tel,
                    'firma_email': firma_email,
                    'projekt_name': projekt_name,
                    'kv_genauigkeit': kv_genauigkeit,
                    'mwst_rate': mwst_rate,
                    'bauherr_name': bauherr_name,
                    'bauherr_adresse': bauherr_adresse,
                    'bauherr_tel': bauherr_tel,
                    'bauherr_email': bauherr_email,
                    'planer_name': planer_name,
                    'planer_adresse': planer_adresse,
                    'planer_tel': planer_tel,
                    'planer_email': planer_email,
                    'bauleitung_name': bauleitung_name,
                    'bauleitung_adresse': bauleitung_adresse,
                    'bauleitung_tel': bauleitung_tel,
                    'bauleitung_email': bauleitung_email,
                    'bkp_items': st.session_state.bkp_items
                }
                
                html_content = create_html_report(data)
                
                st.download_button(
                    label="📥 HTML herunterladen",
                    data=html_content,
                    file_name=f"Kostenvoranschlag_{projekt_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.html",
                    mime="text/html"
                )
                
                st.success("HTML erfolgreich generiert! Öffnen Sie die Datei im Browser und drucken Sie sie als PDF.")
                
                # Vorschau anzeigen
                with st.expander("Vorschau anzeigen"):
                    st.components.v1.html(html_content, height=800, scrolling=True)
                    
            except Exception as e:
                st.error(f"Fehler bei der HTML-Generierung: {str(e)}")
    
    st.markdown("---")
    st.markdown("### Anleitung: HTML zu PDF konvertieren")
    st.info("""
    **So konvertieren Sie die HTML-Datei zu PDF:**
    
    1. Klicken Sie auf "HTML herunterladen"
    2. Öffnen Sie die heruntergeladene HTML-Datei in einem Browser (Chrome, Firefox, Edge)
    3. Drücken Sie Strg+P (Windows) oder Cmd+P (Mac)
    4. Wählen Sie "Als PDF speichern" als Drucker
    5. Klicken Sie auf "Speichern"
    
    **Optional: Für direkten PDF-Export installieren Sie:**
    ```
    pip install fpdf2
    ```
    """)
    
    # Vorschau der Daten
    with st.expander("Datenvorschau anzeigen"):
        if st.session_state.bkp_items:
            st.json({
                'Projekt': projekt_name,
                'Bauherr': bauherr_name,
                'Anzahl Positionen': len(st.session_state.bkp_items),
                'Total Positionen': sum(item['amount'] for item in st.session_state.bkp_items.values())
            })
        else:
            st.warning("Noch keine Daten vorhanden")
