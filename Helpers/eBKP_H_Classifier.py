"""
eBKP-H Classifier mit Anthropic Claude AI
Klassifiziert Revit Bauelemente nach eBKP-H Standard (Level 1+2) mit minimalem Token-Verbrauch.

Optimiert für:
- Kosteneffizienz: Batch-Verarbeitung + Prompt Caching
- Flexibilität: CLI + Streamlit Integration
- Wartbarkeit: Dynamischer Katalog aus CSV
"""

import os
import json
import pandas as pd
from typing import Dict, List
from dotenv import load_dotenv
from anthropic import Anthropic

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    print("Hinweis: 'tqdm' nicht installiert. Progress-Bar nicht verfügbar.")

# .env Datei laden
load_dotenv()


class eBKPHClassifier:
    """
    Klassifiziert Bauelemente nach eBKP-H Standard (Level 1+2) mit Claude AI.
    Optimiert für minimalen Token-Verbrauch durch Batch-Verarbeitung und Prompt Caching.
    """

    def __init__(self, ebkp_csv_path: str = None, api_key: str = None):
        """
        Initialisiert den Classifier mit eBKP-H Katalog (Level 1+2).

        Args:
            ebkp_csv_path: Pfad zur eBKP-H CSV (default: Helpers/eBKP-H.csv)
            api_key: Anthropic API Key (optional, sonst aus .env)
        """
        # API Key
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY nicht gefunden. "
                "Bitte in .env setzen oder als Parameter übergeben."
            )

        # Anthropic Client
        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-3-5-haiku-20241022"  # Kosteneffizientes Modell

        # eBKP-H Katalog laden
        if ebkp_csv_path is None:
            # Default: Helpers/eBKP-H.csv relativ zu diesem Script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            ebkp_csv_path = os.path.join(script_dir, 'eBKP-H.csv')

        if not os.path.exists(ebkp_csv_path):
            raise FileNotFoundError(f"eBKP-H Katalog nicht gefunden: {ebkp_csv_path}")

        # CSV einlesen und Level 1+2 filtern
        df = pd.read_csv(ebkp_csv_path, encoding='utf-8-sig')
        self.ebkp_catalog = df[df['Level'].isin([1, 2])].copy()

        print(f"✓ eBKP-H Katalog geladen: {len(self.ebkp_catalog)} Codes "
              f"(Level 1: {len(df[df['Level'] == 1])}, "
              f"Level 2: {len(df[df['Level'] == 2])})")

        # System Prompt generieren (wird gecacht von Anthropic)
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """
        Baut kompakten System Prompt mit eBKP-H Katalog (Level 1+2).
        Dieser Prompt wird von Anthropic gecacht für 5 Minuten.

        Returns:
            System Prompt String (kompakt formatiert)
        """
        # Level 1 Codes (Hauptgruppen)
        level_1 = self.ebkp_catalog[self.ebkp_catalog['Level'] == 1]
        level_1_lines = [f"{row['Code']}: {row['Description']}"
                         for _, row in level_1.iterrows()]

        # Level 2 Codes (Untergruppen)
        level_2 = self.ebkp_catalog[self.ebkp_catalog['Level'] == 2]
        level_2_lines = [f"{row['Code']}: {row['Description']}"
                         for _, row in level_2.iterrows()]

        prompt = f"""eBKP-H Klassifizierung (Schweizer Baukostenplan)

Du bist ein Experte für Bauwesen und Kostenkalkulation nach eBKP-H Standard.

LEVEL 1 (Hauptgruppen):
{chr(10).join(level_1_lines)}

LEVEL 2 (Untergruppen):
{chr(10).join(level_2_lines)}

Aufgabe: Klassifiziere Bauelemente nach eBKP-H Level 1+2 basierend auf:
- Kategorie (z.B. Waende, Tueren, Decken, Beleuchtung)
- Typ (z.B. "Interior - Partition (92mm Stud)")
- Familie (z.B. "Basic Wall", "M_Single-Flush")
- Zusatzinfo (optional)

Regeln:
1. Gib IMMER einen Level 2 Code zurück (z.B. "C02", nicht nur "C")
2. Falls unsicher zwischen mehreren Codes, wähle den spezifischsten
3. Confidence: 0.9+ = sicher, 0.7-0.9 = wahrscheinlich, <0.7 = unsicher
4. Antworte NUR mit dem angeforderten JSON Format, KEIN zusätzlicher Text"""

        return prompt

    def _build_batch_prompt(self, elements: List[Dict]) -> str:
        """
        Baut kompakten User Prompt für Batch-Klassifizierung.

        Args:
            elements: Liste von Elementen mit 'kategorie', 'typ', 'familie', 'zusatzinfo'

        Returns:
            User Prompt String
        """
        # Elemente formatieren (kompakt)
        element_lines = []
        for i, elem in enumerate(elements, 1):
            parts = []

            # Sichere String-Konvertierung (behandelt NaN, None, float, etc.)
            kategorie = str(elem.get('kategorie', '')).strip() if elem.get('kategorie') not in [None, '', 'nan', 'NaN'] else ''
            typ = str(elem.get('typ', '')).strip() if elem.get('typ') not in [None, '', 'nan', 'NaN'] else ''
            familie = str(elem.get('familie', '')).strip() if elem.get('familie') not in [None, '', 'nan', 'NaN'] else ''
            zusatzinfo = str(elem.get('zusatzinfo', '')).strip() if elem.get('zusatzinfo') not in [None, '', 'nan', 'NaN'] else ''

            if kategorie:
                parts.append(f"Kat: {kategorie}")
            if typ:
                parts.append(f"Typ: {typ}")
            if familie:
                parts.append(f"Fam: {familie}")
            if zusatzinfo:
                parts.append(f"Info: {zusatzinfo}")

            line = f"{i}. {', '.join(parts)}" if parts else f"{i}. (keine Info)"
            element_lines.append(line)

        prompt = f"""Klassifiziere diese {len(elements)} Bauelemente nach eBKP-H (Level 1+2):

{chr(10).join(element_lines)}

Antworte NUR mit diesem JSON Array (keine Markdown, kein Text davor/danach):
[{{"id":1,"code":"C02","desc":"Wandkonstruktion","conf":0.95}},{{"id":2,"code":"F03","desc":"Innentüren","conf":0.90}}]"""

        return prompt

    def _parse_batch_response(self, response_text: str) -> List[Dict]:
        """
        Parst JSON Response von Claude API.

        Args:
            response_text: Raw Response Text von API

        Returns:
            Liste von Dicts mit 'code', 'desc', 'conf'
        """
        try:
            # Bereinige Response (entferne Markdown Code Blocks falls vorhanden)
            content = response_text.strip()

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            # Finde JSON Array in der Response
            start_idx = content.find('[')
            end_idx = content.rfind(']') + 1
            if start_idx >= 0 and end_idx > start_idx:
                content = content[start_idx:end_idx]

            # Parse JSON
            results = json.loads(content)

            # Formatiere Ergebnisse (standardisiere Keys)
            formatted = []
            for r in results:
                formatted.append({
                    'code': r.get('code') or r.get('bkp_code', 'UNKNOWN'),
                    'desc': r.get('desc') or r.get('description', ''),
                    'conf': float(r.get('conf') or r.get('confidence', 0.5))
                })

            return formatted

        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {e}")
            print(f"Response: {response_text[:200]}")
            # Fallback: Leere Ergebnisse mit ERROR
            return [{'code': 'ERROR', 'desc': 'Parse Error', 'conf': 0.0}] * 10

        except Exception as e:
            print(f"Unerwarteter Fehler beim Parsing: {e}")
            return [{'code': 'ERROR', 'desc': str(e), 'conf': 0.0}] * 10

    def classify_element(
        self,
        kategorie: str = "",
        typ: str = "",
        familie: str = "",
        zusatzinfo: str = "",
        debug: bool = False,
        log_file: str = None
    ) -> Dict[str, any]:
        """
        Klassifiziert ein einzelnes Bauelement.

        Args:
            kategorie: Revit Kategorie (z.B. "Waende", "Tueren")
            typ: Element Typ (z.B. "Interior - Partition")
            familie: Familie Name (z.B. "Basic Wall")
            zusatzinfo: Zusätzliche Info (optional)
            debug: Debug-Ausgaben aktivieren
            log_file: Pfad zu Log-Datei für Response-Logging (optional)

        Returns:
            Dict mit 'code', 'desc', 'conf'
        """
        # Verwende Batch-Klassifizierung mit einem Element
        elements = [{
            'kategorie': kategorie,
            'typ': typ,
            'familie': familie,
            'zusatzinfo': zusatzinfo
        }]

        results = self.classify_batch(elements, debug=debug, log_file=log_file)
        return results[0] if results else {'code': 'ERROR', 'desc': 'No result', 'conf': 0.0}

    def classify_batch(
        self,
        elements: List[Dict],
        debug: bool = False,
        log_file: str = None
    ) -> List[Dict]:
        """
        Klassifiziert einen Batch von Elementen (30-50 empfohlen).

        Args:
            elements: Liste von Dicts mit 'kategorie', 'typ', 'familie', 'zusatzinfo'
            debug: Debug-Ausgaben aktivieren
            log_file: Pfad zu Log-Datei für Response-Logging (optional)

        Returns:
            Liste von Dicts mit 'code', 'desc', 'conf'
        """
        if not elements:
            return []

        # Batch Prompt bauen
        prompt = self._build_batch_prompt(elements)

        if debug:
            print(f"\n=== DEBUG: Batch-Klassifizierung ({len(elements)} Elemente) ===")
            print(f"Prompt (erste 300 Zeichen):\n{prompt[:300]}...\n")

        try:
            # API Call
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,  # Genug für ~50 Elemente
                system=self.system_prompt,  # ← Wird gecacht!
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Response extrahieren
            response_text = response.content[0].text

            # Logging in Datei (falls gewünscht)
            if log_file:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n{'='*80}\n")
                    f.write(f"Timestamp: {timestamp}\n")
                    f.write(f"Batch: {len(elements)} Elemente\n")
                    f.write(f"Tokens: Input={response.usage.input_tokens}, Output={response.usage.output_tokens}\n")
                    f.write(f"\nPrompt:\n{prompt}\n")
                    f.write(f"\nResponse:\n{response_text}\n")
                    f.write(f"{'='*80}\n")

            if debug:
                print(f"Response (erste 300 Zeichen):\n{response_text[:300]}...\n")
                print(f"Token Usage: Input={response.usage.input_tokens}, "
                      f"Output={response.usage.output_tokens}")

            # Response parsen
            results = self._parse_batch_response(response_text)

            # Sicherstellen, dass wir für jedes Element ein Ergebnis haben
            if len(results) < len(elements):
                print(f"⚠ Warnung: Nur {len(results)} von {len(elements)} "
                      f"Elementen klassifiziert")
                # Fülle fehlende Ergebnisse auf
                while len(results) < len(elements):
                    results.append({'code': 'MISSING', 'desc': 'No result', 'conf': 0.0})

            return results[:len(elements)]  # Schneide auf exakte Länge

        except Exception as e:
            print(f"Fehler bei API-Call: {e}")
            # Fallback: ERROR für alle Elemente
            return [{'code': 'ERROR', 'desc': str(e), 'conf': 0.0}] * len(elements)

    def classify_csv(
        self,
        input_csv: str,
        output_csv: str = None,
        column_mapping: Dict[str, str] = None,
        batch_size: int = 40,
        show_progress: bool = True,
        debug: bool = False,
        log_file: str = None
    ) -> pd.DataFrame:
        """
        Klassifiziert komplette CSV-Datei mit eBKP-H Codes.

        Args:
            input_csv: Pfad zur Input-CSV (z.B. Revit Export)
            output_csv: Pfad zur Output-CSV (optional, sonst kein Export)
            column_mapping: Custom Spalten-Mapping (optional)
                           z.B. {'kategorie': 'Category', 'typ': 'Type'}
            batch_size: Elemente pro API-Call (30-50 empfohlen)
            show_progress: Progress-Bar anzeigen (benötigt tqdm)
            debug: Debug-Ausgaben aktivieren
            log_file: Pfad zu Log-Datei für API-Response-Logging (optional)

        Returns:
            DataFrame mit neuen Spalten: eBKP_Code, eBKP_Beschreibung, eBKP_Confidence
        """
        print(f"\n=== eBKP-H Klassifizierung ===")
        print(f"Input: {input_csv}")

        # CSV einlesen (unterstützt verschiedene Encodings)
        try:
            df = pd.read_csv(input_csv, sep=';', encoding='utf-8-sig')
        except UnicodeDecodeError:
            df = pd.read_csv(input_csv, sep=';', encoding='latin1')

        print(f"✓ {len(df)} Zeilen eingelesen")

        # Standard Column Mapping
        if column_mapping is None:
            column_mapping = {
                'kategorie': 'Kategorie',
                'typ': 'Typ',
                'familie': 'Familie',
                'zusatzinfo': 'Zusatzinfo'
            }

        # Element-Infos extrahieren (mit sicherer NaN-Behandlung)
        elements = []
        for _, row in df.iterrows():
            # Sichere Konvertierung: behandelt NaN, None, float
            def safe_str(val):
                if pd.isna(val) or val is None or str(val).lower() == 'nan':
                    return ''
                return str(val).strip()

            elements.append({
                'kategorie': safe_str(row.get(column_mapping['kategorie'], '')),
                'typ': safe_str(row.get(column_mapping['typ'], '')),
                'familie': safe_str(row.get(column_mapping['familie'], '')),
                'zusatzinfo': safe_str(row.get(column_mapping['zusatzinfo'], ''))
            })

        # Batch-Klassifizierung mit Progress
        print(f"Klassifizierung (Batch-Size: {batch_size})...")

        # Log-Datei initialisieren
        if log_file:
            from datetime import datetime
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"eBKP-H Klassifizierung Log\n")
                f.write(f"Gestartet: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Input CSV: {input_csv}\n")
                f.write(f"Elemente: {len(elements)}\n")
                f.write(f"Batch-Größe: {batch_size}\n")
                f.write(f"{'='*80}\n")
            print(f"✓ Log-Datei erstellt: {log_file}")

        all_results = []

        # Progress-Bar Setup
        if show_progress and TQDM_AVAILABLE:
            pbar = tqdm(total=len(elements), desc="Klassifizierung", unit="elem")
        else:
            pbar = None

        # Batches verarbeiten
        num_batches = (len(elements) + batch_size - 1) // batch_size
        for batch_idx in range(num_batches):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, len(elements))
            batch = elements[start_idx:end_idx]

            if debug or (not show_progress):
                print(f"Batch {batch_idx + 1}/{num_batches} "
                      f"(Elemente {start_idx + 1}-{end_idx})...")

            # Klassifizierung
            batch_results = self.classify_batch(batch, debug=debug, log_file=log_file)
            all_results.extend(batch_results)

            # Progress update
            if pbar:
                pbar.update(len(batch))

        if pbar:
            pbar.close()

        # Ergebnisse in DataFrame schreiben
        df['eBKP_Code'] = [r['code'] for r in all_results]
        df['eBKP_Beschreibung'] = [r['desc'] for r in all_results]
        df['eBKP_Confidence'] = [r['conf'] for r in all_results]

        # Statistik
        print(f"\n✓ Klassifizierung abgeschlossen!")
        print(f"  - {len(df)} Elemente klassifiziert")
        print(f"  - Durchschnittliche Confidence: {df['eBKP_Confidence'].mean():.1%}")
        print(f"  - Niedrigste Confidence: {df['eBKP_Confidence'].min():.1%}")

        # Top 5 Codes
        print(f"\nTop 5 eBKP Codes:")
        top_codes = df['eBKP_Code'].value_counts().head(5)
        for code, count in top_codes.items():
            desc = df[df['eBKP_Code'] == code]['eBKP_Beschreibung'].iloc[0]
            print(f"  - {code} ({desc}): {count}x")

        # Optional: CSV exportieren
        if output_csv:
            df.to_csv(output_csv, sep=';', index=False, encoding='utf-8-sig')
            print(f"\n✓ Output gespeichert: {output_csv}")

        return df


# Convenience-Funktion für einfache Nutzung
def classify_revit_element(kategorie: str = "", typ: str = "", **kwargs) -> Dict:
    """
    Quick-Helper: Klassifiziert ein einzelnes Element.

    Usage:
        result = classify_revit_element(kategorie="Waende", typ="Interior Partition")
        print(f"eBKP: {result['code']} (Confidence: {result['conf']:.0%})")
    """
    classifier = eBKPHClassifier()
    return classifier.classify_element(kategorie=kategorie, typ=typ, **kwargs)


# ============================================================================
# CLI INTERFACE
# ============================================================================

if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description='eBKP-H Klassifizierung für Revit Bauelemente',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Einfache Klassifizierung
  python eBKP_H_Classifier.py input.csv

  # Mit Output-Datei
  python eBKP_H_Classifier.py input.csv -o output_classified.csv

  # Custom Batch-Size und Debug
  python eBKP_H_Classifier.py input.csv -b 50 --debug

  # Ohne Progress-Bar
  python eBKP_H_Classifier.py input.csv --no-progress
        """
    )

    parser.add_argument('input_csv', help='Input CSV Datei (z.B. Revit Export)')
    parser.add_argument('-o', '--output', help='Output CSV Datei (optional)')
    parser.add_argument('-b', '--batch-size', type=int, default=40,
                        help='Batch-Größe (30-50 empfohlen, default: 40)')
    parser.add_argument('--no-progress', action='store_true',
                        help='Progress-Bar deaktivieren')
    parser.add_argument('--debug', action='store_true',
                        help='Debug-Modus (zeigt API Requests/Responses)')

    args = parser.parse_args()

    # Validierung
    if not os.path.exists(args.input_csv):
        print(f"❌ Fehler: Input-Datei nicht gefunden: {args.input_csv}")
        sys.exit(1)

    try:
        # Classifier initialisieren
        classifier = eBKPHClassifier()

        # Klassifizierung ausführen
        df = classifier.classify_csv(
            args.input_csv,
            output_csv=args.output,
            batch_size=args.batch_size,
            show_progress=not args.no_progress,
            debug=args.debug
        )

        # Erfolg
        print("\n✅ Klassifizierung erfolgreich abgeschlossen!")

    except KeyboardInterrupt:
        print("\n\n⚠ Abgebrochen durch Benutzer")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)
