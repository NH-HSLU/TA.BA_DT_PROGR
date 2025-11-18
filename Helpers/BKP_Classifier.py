"""
BKP Classifier mit Anthropic Claude AI
Klassifiziert Revit Bauelemente nach e-BKP-h Standard mit minimalem Token-Verbrauch.
"""

import os
import json
from typing import Dict, List, Optional
from dotenv import load_dotenv
from anthropic import Anthropic

# .env Datei laden
load_dotenv()


class BKPClassifier:
    """
    Klassifiziert Bauelemente nach e-BKP-h Standard mit Claude AI.
    Optimiert für minimalen Token-Verbrauch.
    """

    # e-BKP-h Hauptgruppen (kompakte Referenz)
    BKP_REFERENCE = """
C: Elektroinstallationen
C1: Starkstrom
C11: Starkstromhauptverteilung
C12: Installationsverteilungen
C13: Steckdosen
C14: Leuchten
C15: Sicherheitsbeleuchtung
C2: Schwachstrom
C21: Telefon/Daten
C22: Alarm/Sicherheit
C23: Zeitdienstanlagen

D: Heizung/Lüftung/Klima/Sanitär
D1: Heizung
D2: Lüftung/Klima
D3: Sanitär
D31: Kalt-/Warmwasser
D32: Abwasser

E: Bauwerk - Rohbau
E1: Fundament
E2: Wände/Stützen
E21: Tragende Wände
E22: Trennwände
E3: Decken

F: Bauwerk - Technik
F1: Fenster/Fenstertüren
F2: Aussentüren
F3: Innentüren
"""

    def __init__(self):
        """Initialisiert den Classifier mit Anthropic API."""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY nicht in .env gefunden")

        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-5-haiku-20241022"  # Günstiges Modell

    def classify_element(
        self,
        element_type: str,
        category: Optional[str] = None,
        family: Optional[str] = None,
        additional_info: Optional[str] = None,
        debug: bool = False
    ) -> Dict[str, any]:
        """
        Klassifiziert ein einzelnes Bauelement.

        Args:
            element_type: Typ des Elements (z.B. "Steckdose", "Wand", "Leuchte")
            category: Revit Kategorie (optional)
            family: Revit Family Name (optional)
            additional_info: Zusätzliche Beschreibung (optional)
            debug: Wenn True, zeigt API Response (optional)

        Returns:
            Dict mit 'bkp_code', 'bkp_description', 'confidence' (0-1)
        """
        # Kompakter Prompt - nur essenzielle Infos
        element_info = f"{element_type}"
        if category:
            element_info += f" ({category})"
        if family:
            element_info += f" - {family}"
        if additional_info:
            element_info += f" | {additional_info}"

        prompt = f"""Klassifiziere: {element_info}

Antworte NUR mit diesem JSON Format (keine Markdown, kein Text):
{{"code": "C13", "desc": "Steckdosen", "conf": 0.95}}"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=150,  # Etwas mehr für Sicherheit
                system=self.BKP_REFERENCE,  # System prompt wird gecacht
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Parse JSON Response
            content = response.content[0].text.strip()

            if debug:
                print(f"DEBUG - API Response: {content}")

            # Entferne Markdown Code Blocks falls vorhanden
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            # Entferne mögliche Zeilenumbrüche und Whitespace
            content = content.strip()

            # Parse JSON
            result = json.loads(content)

            # Standardisiere Output Format
            return {
                'bkp_code': result.get('code') or result.get('bkp_code') or result.get('BKP', 'UNKNOWN'),
                'bkp_description': result.get('desc') or result.get('description') or result.get('beschreibung', ''),
                'confidence': float(result.get('conf') or result.get('confidence', 0.5))
            }

        except json.JSONDecodeError as e:
            if debug:
                print(f"DEBUG - JSON Parse Error: {e}")
                print(f"DEBUG - Content: {content}")

            # Versuche einfaches Text-Parsing als Fallback
            # Erwarte Format wie "C13"
            parts = content.strip().split()
            if parts and len(parts[0]) <= 5:  # BKP Code ist kurz
                return {
                    'bkp_code': parts[0],
                    'bkp_description': ' '.join(parts[1:]) if len(parts) > 1 else '',
                    'confidence': 0.5
                }

            return {
                'bkp_code': 'PARSE_ERROR',
                'bkp_description': content[:50],
                'confidence': 0.0
            }

        except Exception as e:
            if debug:
                print(f"DEBUG - Exception: {e}")
            return {
                'bkp_code': 'ERROR',
                'bkp_description': str(e),
                'confidence': 0.0
            }

    def classify_batch(self, elements: List[Dict], debug: bool = False) -> List[Dict]:
        """
        Klassifiziert mehrere Elemente in einem Batch.
        Effizienter als Einzelabfragen.

        Args:
            elements: Liste von Dicts mit 'type', optional 'category', 'family', 'info'
            debug: Debug-Modus aktivieren

        Returns:
            Liste von Classification Results
        """
        # Batch-Prompt erstellen (mehrere Elemente auf einmal)
        elements_str = "\n".join([
            f"{i+1}. {e.get('type', 'N/A')} "
            f"({e.get('category', '')} {e.get('family', '')})"
            for i, e in enumerate(elements)
        ])

        prompt = f"""Klassifiziere diese {len(elements)} Elemente nach BKP:
{elements_str}

Antworte NUR mit einem JSON Array (keine Markdown, kein Text):
[{{"id":1,"code":"C13","desc":"Steckdosen","conf":0.9}},{{"id":2,"code":"C14","desc":"Leuchten","conf":0.95}}]"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=800,  # Für mehrere Elemente
                system=self.BKP_REFERENCE,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            content = response.content[0].text.strip()

            if debug:
                print(f"DEBUG - Batch API Response: {content}")

            # JSON extrahieren
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            # Finde JSON Array in der Response
            # Manchmal kommt Text vor/nach dem Array
            start_idx = content.find('[')
            end_idx = content.rfind(']') + 1
            if start_idx >= 0 and end_idx > start_idx:
                content = content[start_idx:end_idx]

            results = json.loads(content)

            # Formatiere Ergebnisse
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'bkp_code': result.get('code') or result.get('bkp_code', 'UNKNOWN'),
                    'bkp_description': result.get('desc') or result.get('description', ''),
                    'confidence': float(result.get('conf') or result.get('confidence', 0.5))
                })

            return formatted_results

        except Exception as e:
            # Fallback zu Einzelabfragen bei Fehler
            if debug:
                print(f"DEBUG - Batch-Fehler: {e}, verwende Einzelabfragen")
            else:
                print(f"Batch-Fehler: {e}, verwende Einzelabfragen")

            return [self.classify_element(e.get('type', ''),
                                          e.get('category'),
                                          e.get('family'),
                                          e.get('info'))
                    for e in elements]


# Convenience-Funktion für einfache Nutzung
def classify_revit_element(element_type: str, **kwargs) -> Dict:
    """
    Quick-Helper: Klassifiziert ein einzelnes Element.

    Usage:
        result = classify_revit_element("Steckdose", category="Electrical Fixtures")
        print(f"BKP: {result['bkp_code']} (Confidence: {result['confidence']:.0%})")
    """
    classifier = BKPClassifier()
    return classifier.classify_element(element_type, **kwargs)


if __name__ == "__main__":
    import sys

    # Test-Beispiele
    classifier = BKPClassifier()

    # Debug-Modus wenn --debug übergeben
    debug_mode = '--debug' in sys.argv

    print("=== Einzelklassifizierung ===\n")
    test_elements = [
        ("Steckdose T13", "Electrical Fixtures", None),
        ("LED Deckenleuchte", "Lighting Fixtures", "Deckenleuchte Standard"),
        ("Innenwand Gips", "Walls", "Trennwand 10cm"),
        ("Sanitär WC", "Plumbing Fixtures", "WC-Becken"),
    ]

    for element_type, category, family in test_elements:
        result = classifier.classify_element(element_type, category, family, debug=debug_mode)
        print(f"{element_type:25} -> {result['bkp_code']:6} "
              f"({result['confidence']:>4.0%}) {result['bkp_description']}")
        if debug_mode:
            print()

    print("\n=== Batch-Klassifizierung (effizienter) ===\n")
    batch_elements = [
        {'type': 'Steckdose', 'category': 'Electrical'},
        {'type': 'Leuchte', 'category': 'Lighting'},
        {'type': 'Wand', 'category': 'Walls'},
    ]

    batch_results = classifier.classify_batch(batch_elements)
    for elem, result in zip(batch_elements, batch_results):
        print(f"{elem['type']:15} -> {result['bkp_code']:6} ({result['confidence']:>4.0%})")

    print("\nHinweis: Verwende --debug für detaillierte API Responses")
