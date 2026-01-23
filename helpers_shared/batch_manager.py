"""
Batch Job Manager für Anthropic Batch API

Speichert und verwaltet Batch-IDs für asynchrone BKP-Klassifizierungen.
Batch-Metadaten werden in Logs/batch_jobs.json gespeichert.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


# Pfad zur Batch-Jobs-Datei
BATCH_FILE = Path("Logs/batch_jobs.json")


def save_batch_metadata(
    batch_id: str,
    num_elements: int,
    df_path: Optional[str] = None,
    csv_filename: Optional[str] = None
) -> None:
    """
    Speichert Batch-Metadata für späteren Abruf.

    Args:
        batch_id: Anthropic Batch-ID
        num_elements: Anzahl der Elemente im Batch
        df_path: Optional: Pfad zum DataFrame (für Wiederherstellung)
        csv_filename: Optional: Original-CSV-Dateiname
    """
    batches = load_all_batches()

    batches[batch_id] = {
        "batch_id": batch_id,
        "created_at": datetime.now().isoformat(),
        "num_elements": num_elements,
        "status": "processing",
        "df_path": df_path,
        "csv_filename": csv_filename
    }

    # Logs-Verzeichnis erstellen, falls nicht vorhanden
    BATCH_FILE.parent.mkdir(exist_ok=True, parents=True)

    # Batch-Datei schreiben
    BATCH_FILE.write_text(json.dumps(batches, indent=2, ensure_ascii=False))


def load_all_batches() -> Dict:
    """
    Lädt alle gespeicherten Batches aus der Datei.

    Returns:
        Dict mit Batch-ID als Key und Metadata als Value
    """
    if BATCH_FILE.exists():
        try:
            return json.loads(BATCH_FILE.read_text())
        except json.JSONDecodeError:
            # Korrupte Datei - leeres Dict zurückgeben
            return {}
    return {}


def update_batch_status(
    batch_id: str,
    status: str,
    results_path: Optional[str] = None,
    error_message: Optional[str] = None
) -> None:
    """
    Aktualisiert den Status eines Batches.

    Args:
        batch_id: Batch-ID
        status: Neuer Status (processing/completed/failed)
        results_path: Optional: Pfad zu den Ergebnissen
        error_message: Optional: Fehlermeldung bei Fehler
    """
    batches = load_all_batches()

    if batch_id in batches:
        batches[batch_id]["status"] = status
        batches[batch_id]["updated_at"] = datetime.now().isoformat()

        if results_path:
            batches[batch_id]["results_path"] = results_path

        if error_message:
            batches[batch_id]["error_message"] = error_message

        BATCH_FILE.write_text(json.dumps(batches, indent=2, ensure_ascii=False))


def get_pending_batches() -> List[Dict]:
    """
    Gibt alle Batches mit Status 'processing' zurück.

    Returns:
        Liste von Batch-Metadata-Dicts
    """
    batches = load_all_batches()
    return [
        batch
        for batch in batches.values()
        if batch.get("status") == "processing"
    ]


def get_batch_metadata(batch_id: str) -> Optional[Dict]:
    """
    Gibt Metadata für einen bestimmten Batch zurück.

    Args:
        batch_id: Batch-ID

    Returns:
        Batch-Metadata oder None, falls nicht gefunden
    """
    batches = load_all_batches()
    return batches.get(batch_id)


def delete_batch(batch_id: str) -> bool:
    """
    Löscht einen Batch aus der Datei.

    Args:
        batch_id: Batch-ID

    Returns:
        True, falls erfolgreich gelöscht, sonst False
    """
    batches = load_all_batches()

    if batch_id in batches:
        del batches[batch_id]
        BATCH_FILE.write_text(json.dumps(batches, indent=2, ensure_ascii=False))
        return True

    return False


def cleanup_old_batches(days: int = 7) -> int:
    """
    Löscht Batches, die älter als X Tage sind.

    Args:
        days: Anzahl der Tage

    Returns:
        Anzahl der gelöschten Batches
    """
    batches = load_all_batches()
    now = datetime.now()
    deleted_count = 0

    for batch_id, batch in list(batches.items()):
        created_at = datetime.fromisoformat(batch["created_at"])
        age_days = (now - created_at).days

        if age_days > days:
            del batches[batch_id]
            deleted_count += 1

    if deleted_count > 0:
        BATCH_FILE.write_text(json.dumps(batches, indent=2, ensure_ascii=False))

    return deleted_count
