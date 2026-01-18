from __future__ import annotations

from dataclasses import dataclass, asdict
import json
from typing import Dict, Any
import sys
import os

import streamlit as st

# Füge Parent-Verzeichnis zum Path hinzu für Imports
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from helpers.sidebar_navigation import render_sidebar, render_page_header, render_divider, render_page_footer
from helpers.notifications import toast, NotificationType
from helpers.session_state import (
    init_session_state,
    get_state,
    set_state,
    DATA_PROJEKT_DATEN
)


# ==========================
# Datenmodell (Domain Layer)
# ==========================

@dataclass
class ObjektInfo:
    """Repräsentiert die wichtigsten Stammdaten eines Bauobjekts."""

    projektname: str
    adresse: str
    plz_ort: str

    def to_dict(self) -> Dict[str, Any]:
        """Wandelt die Objektinformationen in ein Dictionary um."""
        return asdict(self)


@dataclass
class BauherrInfo:
    """Repräsentiert den Bauherr (Auftraggeber) eines Projekts."""

    name: str
    adresse: str
    plz_ort: str

    def to_dict(self) -> Dict[str, Any]:
        """Wandelt die Bauherr-Informationen in ein Dictionary um."""
        return asdict(self)


@dataclass
class BaumanagementInfo:
    """Repräsentiert die verantwortliche Baumanagement-Stelle."""

    firma: str
    kontaktperson: str
    adresse: str
    plz_ort: str

    def to_dict(self) -> Dict[str, Any]:
        """Wandelt die Baumanagement-Informationen in ein Dictionary um."""
        return asdict(self)


@dataclass
class ProjektDaten:
    """
    Aggregiert alle relevanten Projektdaten, damit sie später
    z.B. für einen PDF-Export an einer Stelle verfügbar sind.
    """

    objekt: ObjektInfo
    bauherr: BauherrInfo
    baumanagement: BaumanagementInfo

    def to_dict(self) -> Dict[str, Any]:
        """
        Gibt die Projektdaten als verschachteltes Dictionary zurück.
        Diese Struktur ist gut geeignet für JSON-Export oder PDF-Templates.
        """
        return {
            "objekt": self.objekt.to_dict(),
            "bauherr": self.bauherr.to_dict(),
            "baumanagement": self.baumanagement.to_dict(),
        }


# ==========================
# Hilfsfunktionen
# ==========================

def serialize_to_json(data: ProjektDaten) -> str:
    """
    Serialisiert ein ProjektDaten-Objekt in einen formatierten JSON-String.

    Dieser JSON-String kann z.B. in Dateien gespeichert oder
    an einen PDF-Generator übergeben werden.
    """
    return json.dumps(data.to_dict(), ensure_ascii=False, indent=2)


# ==========================
# UI / Streamlit App
# ==========================

def render_form() -> None:
    """
    Rendert das Eingabeformular für die Projektdaten.
    Die Eingaben werden erst beim Klick auf den Submit-Button verarbeitet.
    """
    st.header("Projektdaten eingeben")

    # Lade vorhandene Projektdaten aus Session State
    existing_data: ProjektDaten | None = get_state(DATA_PROJEKT_DATEN)

    # Zeige Hinweis, wenn Daten bereits vorhanden sind
    if existing_data is not None:
        st.info("ℹ️ Projektdaten wurden bereits erfasst. Sie können die Daten unten bearbeiten und erneut speichern.")

    # Default-Werte aus vorhandenen Daten oder leer
    default_projektname = existing_data.objekt.projektname if existing_data else ""
    default_objekt_adresse = existing_data.objekt.adresse if existing_data else ""
    default_objekt_plz = existing_data.objekt.plz_ort if existing_data else ""

    default_bauherr_name = existing_data.bauherr.name if existing_data else ""
    default_bauherr_adresse = existing_data.bauherr.adresse if existing_data else ""
    default_bauherr_plz = existing_data.bauherr.plz_ort if existing_data else ""

    default_bm_firma = existing_data.baumanagement.firma if existing_data else ""
    default_bm_kontakt = existing_data.baumanagement.kontaktperson if existing_data else ""
    default_bm_adresse = existing_data.baumanagement.adresse if existing_data else ""
    default_bm_plz = existing_data.baumanagement.plz_ort if existing_data else ""

    # Verwendung eines Formulars sorgt dafür, dass die App nur
    # beim Klick auf den Submit-Button neu berechnet wird.
    with st.form("projekt_formular"):
        st.subheader("Objekt")
        objekt_projektname = st.text_input(
            "Projektname",
            value=default_projektname,
            placeholder="MFH Schönenberg, Sanierung 2026",
        )
        objekt_adresse = st.text_input(
            "Objektadresse",
            value=default_objekt_adresse,
            placeholder="Strasse, Nummer",
        )
        objekt_PLZ = st.text_input(
            "Postleitzahl und Ort",
            value=default_objekt_plz,
            placeholder="PLZ Ort",
        )

        st.subheader("Bauherr")
        bauherr_name = st.text_input(
            "Name des Bauherrn",
            value=default_bauherr_name,
            placeholder="Firma / Privatperson",
        )
        bauherr_adresse = st.text_input(
            "Adresse des Bauherrn",
            value=default_bauherr_adresse,
            placeholder="Strasse, Nummer",
        )
        bauherr_PLZ = st.text_input(
            "Postleitzahl und Ort",
            value=default_bauherr_plz,
            placeholder="PLZ Ort",
            key="bauherr_plz_input",
        )

        st.subheader("Baumanagement")
        bm_firma = st.text_input(
            "Baumanagement-Firma",
            value=default_bm_firma,
            placeholder="Baumanagement AG",
        )
        bm_kontakt = st.text_input(
            "Kontaktperson",
            value=default_bm_kontakt,
            placeholder="Max Muster",
        )
        bm_adresse = st.text_input(
            "Adresse Baumanagement",
            value=default_bm_adresse,
            placeholder="Strasse, PLZ Ort",
        )
        bm_PLZ = st.text_input(
            "Postleitzahl und Ort",
            value=default_bm_plz,
            placeholder="PLZ Ort",
            key="baumanagement_plz_input",
        )

        # Formular-Submit-Button - Text ändert sich je nachdem ob Daten vorhanden sind
        button_text = "Projektdaten aktualisieren" if existing_data else "Projektdaten speichern"
        submitted = st.form_submit_button(button_text)

    if submitted:
        # Prüfe ob es ein Update ist (vor dem Speichern!)
        is_update = existing_data is not None

        # Erzeugen der Datenobjekte bei erfolgreichem Submit
        objekt_info = ObjektInfo(
            projektname=objekt_projektname.strip(),
            adresse=objekt_adresse.strip(),
            plz_ort=objekt_PLZ.strip(),
        )
        bauherr_info = BauherrInfo(
            name=bauherr_name.strip(),
            adresse=bauherr_adresse.strip(),
            plz_ort=bauherr_PLZ.strip(),
        )
        baumanagement_info = BaumanagementInfo(
            firma=bm_firma.strip(),
            kontaktperson=bm_kontakt.strip(),
            adresse=bm_adresse.strip(),
            plz_ort=bm_PLZ.strip(),
        )

        projekt_daten = ProjektDaten(
            objekt=objekt_info,
            bauherr=bauherr_info,
            baumanagement=baumanagement_info,
        )

        # Im Session State speichern, damit später weitere Seiten
        # (z.B. PDF-Export) darauf zugreifen können.
        set_state(DATA_PROJEKT_DATEN, projekt_daten)

        # Toast-Benachrichtigung - Text abhängig davon ob Update oder neu
        if is_update:
            toast("Projektdaten erfolgreich aktualisiert!", NotificationType.SUCCESS)
            st.success("Projektdaten wurden aktualisiert.")
        else:
            toast("Projektdaten erfolgreich gespeichert!", NotificationType.SUCCESS)
            st.success("Projektdaten wurden gespeichert.")


def render_preview_and_download() -> None:
    """
    Zeigt eine Vorschau der aktuell gespeicherten Projektdaten
    und bietet einen JSON-Download an.
    """
    st.header("Vorschau & Export")

    # Zentrale get_state Funktion verwenden
    projekt_daten: ProjektDaten | None = get_state(DATA_PROJEKT_DATEN)

    if projekt_daten is None:
        st.info("Noch keine Projektdaten erfasst. Bitte Formular ausfüllen.")
        return

    # Strukturierte Vorschau als JSON-Viewer
    st.subheader("Strukturierte Daten (JSON-Vorschau)")
    json_string = serialize_to_json(projekt_daten)
    st.json(json.loads(json_string))

    # Download-Button für JSON-Datei
    st.download_button(
        label="Daten als JSON herunterladen",
        data=json_string,
        file_name="projektdaten.json",
        mime="application/json",
    )


def main() -> None:
    """Entry-Point der Streamlit-App."""
    st.set_page_config(
        page_title="Projektdaten Bauprojekt",
        page_icon="🏗️",
        layout="wide",
    )

    # Zentrale Session State Initialisierung
    init_session_state()

    # Sidebar rendern
    render_sidebar()

    # Page Header mit neuem Design
    render_page_header("Projektdaten – Erfassung Bauprojekt",
                      "Eingabe von Objekt-, Bauherr- und Baumanagement-Daten als Basis für weitere Auswertungen und PDF-Reports.")

    render_divider("gradient")

    render_form()
    render_divider("section")
    render_preview_and_download()

    # Footer rendern
    render_page_footer()


if __name__ == "__main__":
    main()