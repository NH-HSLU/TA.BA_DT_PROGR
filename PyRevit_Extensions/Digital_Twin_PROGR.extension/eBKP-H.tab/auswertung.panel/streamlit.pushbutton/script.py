# -*- coding: utf-8 -*-
"""
Streamlit App Launcher
Startet die BKP Streamlit-Anwendung im Standard-Browser
"""

__title__ = "Streamlit\nApp"
__author__ = "TA.BA_DT_PROGR_Gruppe21"
__doc__ = "Startet die BKP Streamlit-Anwendung im Browser"

from pyrevit import forms, script
import subprocess
import os
import sys

# Output fuer Meldungen
output = script.get_output()


def get_project_root():
    """
    Ermittelt das Projekt-Stammverzeichnis ausgehend vom Script-Ordner.

    Pfad-Struktur:
    script.py / streamlit.pushbutton / auswertung.panel / eBKP-H.tab /
    Digital_Twin_PROGR.extension / PyRevit_Extensions / PROJECT_ROOT
    """
    script_dir = os.path.dirname(__file__)
    # 5 Ebenen nach oben: pushbutton / panel / tab / extension / PyRevit_Extensions / PROJECT_ROOT
    project_root = os.path.abspath(os.path.join(script_dir, "..", "..", "..", "..", ".."))
    return project_root


def validate_paths(project_root):
    """
    Validiert, ob die benoetigten Dateien existieren.

    Args:
        project_root: Absoluter Pfad zum Projekt-Stammverzeichnis

    Returns:
        tuple: (venv_streamlit_path, streamlit_app_path, error_message)
               error_message ist None wenn alles OK ist
    """
    # Pfade zusammenbauen
    venv_streamlit = os.path.join(project_root, ".venv", "Scripts", "streamlit.exe")
    streamlit_app = os.path.join(project_root, "Streamlit", "streamlit_app.py")

    # Validierung .venv
    if not os.path.exists(venv_streamlit):
        error_msg = (
            "Die virtuelle Python-Umgebung wurde nicht gefunden.\n\n"
            "Erwarteter Pfad:\n{}\n\n"
            "Bitte installieren Sie die Abhängigkeiten:\n"
            "1. öffnen Sie ein Terminal im Projekt-Ordner\n"
            "2. Führen Sie aus: pip install -r requirements.txt"
        ).format(venv_streamlit)
        return None, None, error_msg

    # Validierung Streamlit App
    if not os.path.exists(streamlit_app):
        error_msg = (
            "Die Streamlit-Anwendung wurde nicht gefunden.\n\n"
            "Erwarteter Pfad:\n{}\n\n"
            "Bitte prüfen Sie die Projekt-Struktur."
        ).format(streamlit_app)
        return None, None, error_msg

    return venv_streamlit, streamlit_app, None


def launch_streamlit(venv_streamlit, streamlit_app, project_root):
    """
    Startet die Streamlit-Anwendung in einem neuen Konsolen-Fenster.

    Args:
        venv_streamlit: Pfad zur streamlit.exe
        streamlit_app: Pfad zur streamlit_app.py
        project_root: Projekt-Stammverzeichnis (Working Directory)

    Returns:
        bool: True bei Erfolg, False bei Fehler
    """
    try:
        # Versuch 1: subprocess.Popen (funktioniert in CPython und IronPython 2.7+)
        if sys.platform == "win32":
            # Windows: Neues Konsolen-Fenster erstellen
            subprocess.Popen(
                [venv_streamlit, "run", streamlit_app],
                cwd=project_root,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:
            # Linux/macOS
            subprocess.Popen(
                [venv_streamlit, "run", streamlit_app],
                cwd=project_root
            )

        return True

    except Exception as e:
        # Versuch 2: .NET Process (IronPython Fallback)
        try:
            from System.Diagnostics import Process, ProcessStartInfo

            start_info = ProcessStartInfo()
            start_info.FileName = venv_streamlit
            start_info.Arguments = "run \"{}\"".format(streamlit_app)
            start_info.WorkingDirectory = project_root
            start_info.CreateNoWindow = False
            start_info.UseShellExecute = True

            Process.Start(start_info)
            return True

        except Exception as e2:
            # Beide Versuche fehlgeschlagen
            error_msg = (
                "Fehler beim Starten der Streamlit-App:\n\n"
                "Versuch 1 (subprocess): {}\n\n"
                "Versuch 2 (.NET Process): {}\n\n"
                "Bitte kontaktieren Sie den Support."
            ).format(str(e), str(e2))

            forms.alert(error_msg, title="Start-Fehler", warn_icon=True)
            return False


def main():
    """Hauptfunktion: Streamlit App starten"""

    output.print_md("# BKP Streamlit App Launcher")
    output.print_md("---")

    # Schritt 1: Projekt-Root ermitteln
    project_root = get_project_root()
    output.print_md("**Projekt-Verzeichnis:** `{}`".format(project_root))

    # Schritt 2: Pfade validieren
    output.print_md("**Status:** Validiere Pfade...")
    venv_streamlit, streamlit_app, error_msg = validate_paths(project_root)

    if error_msg:
        # Fehler: Dateien nicht gefunden
        output.print_md("**L Fehler:** Benötigte Dateien nicht gefunden")
        forms.alert(error_msg, title="Streamlit App - Fehler", warn_icon=True)
        return

    output.print_md("**✔** Streamlit-Executable gefunden")
    output.print_md("**✔** Streamlit-App gefunden")

    # Schritt 3: Streamlit starten
    output.print_md("---")
    output.print_md("**Status:** Starte Streamlit-Anwendung...")

    success = launch_streamlit(venv_streamlit, streamlit_app, project_root)

    if success:
        output.print_md("---")
        output.print_md("BKP Streamlit App wurde gestartet!")
        output.print_md("")
        output.print_md("Die Anwendung wird automatisch in Ihrem Standard-Browser geöffnet.")
        output.print_md("")
        output.print_md("**URL:** http://localhost:8501")
        output.print_md("")
        output.print_md("*(Falls mehrere Instanzen laufen: 8502, 8503, ...)*")
        output.print_md("")
        output.print_md("---")
        output.print_md("### Hinweise:")
        output.print_md("")
        output.print_md("- **Konsolen-Fenster:** Ein neues Fenster mit Streamlit-Logs wurde geöffnet")
        output.print_md("- **App beenden:** Schließen Sie das Konsolen-Fenster")
        output.print_md("- **Browser-Tab schließen:** Die App läuft weiter im Hintergrund")
        output.print_md("")
        output.print_md("---")
        output.print_md("*BKP Datenverarbeitungs-Suite v1.0*")


# Script ausfuehren
if __name__ == "__main__":
    main()
