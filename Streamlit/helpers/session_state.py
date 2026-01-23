"""
Centralized session state initialization and management.

Ensures consistent state keys across all pages and provides helper functions
for state management.
"""

import streamlit as st
import pandas as pd
from typing import Any, Optional, Dict, List, Tuple
from datetime import datetime


# === STATE KEY CONSTANTS ===
# Using constants prevents typos and makes refactoring easier

# Data States
DATA_CLASSIFICATION_RESULTS = 'classification_results'  # pd.DataFrame
DATA_ORIGINAL_UPLOADED = 'original_uploaded_data'      # pd.DataFrame
DATA_PREPARED = 'prepared_data'                        # pd.DataFrame
DATA_DEDUP_MAPPING = 'dedup_mapping'                   # Dict
DATA_UNIQUE_ELEMENTS = 'unique_elements'               # pd.DataFrame
DATA_PROJEKT_DATEN = 'projekt_daten'                   # ProjektDaten object
DATA_COST_RESULTS = 'cost_results_df'                  # pd.DataFrame mit Kostenberechnung
DATA_COST_SUMMARIES = 'cost_summaries'                 # Dict mit Kostenzusammenfassungen
DATA_CUSTOM_KENNWERTE = 'custom_kennwerte'             # pd.DataFrame mit benutzerdefinierten Kennwerten
DATA_MANUAL_COSTS = 'manual_costs'                     # Dict für manuelle Kosteneingaben (A, B, V, W, Y, Z)
CFG_USE_CUSTOM_KENNWERTE = 'use_custom_kennwerte'      # bool: Eigene Kennwerte verwenden

# Processing States
PROC_API_RESPONSES = 'api_responses'                   # List[Dict]
PROC_PROCESSING_LOG = 'processing_log'                 # List[Dict]
PROC_TOTAL_COST = 'total_cost'                         # float
PROC_ACTIVE_TAB = 'active_tab'                         # int

# Configuration States
CFG_API_KEY = 'api_key'                                # str
CFG_API_KEY_VALIDATED = 'api_key_validated'            # bool
CFG_TOKEN_LIMIT = 'token_limit'                        # int
CFG_FORCE_BATCH_API = 'force_batch_api'                # bool
CFG_COST_ESTIMATION_CONFIG = 'cost_estimation_config'  # Dict
CFG_CLASSIFICATION_SETTINGS = 'classification_settings' # Dict
CFG_SELECTED_COST_LEVEL = 'selected_cost_level'        # str: 'tief', 'mittel', 'hoch'

# UI States
UI_SELECTED_WORKFLOW_STEP = 'selected_workflow_step'   # int
UI_USE_PREPARED_DATA = 'use_prepared_data'             # bool
UI_SELECTED_FOR_DETAILS = 'selected_for_details'       # str/None


def init_session_state() -> None:
    """
    Initialisiert alle Session State Variablen mit Standardwerten.

    Sollte in jeder Page aufgerufen werden (idempotent).
    """
    defaults = {
        # Data States
        DATA_CLASSIFICATION_RESULTS: None,
        DATA_ORIGINAL_UPLOADED: None,
        DATA_PREPARED: None,
        DATA_DEDUP_MAPPING: None,
        DATA_UNIQUE_ELEMENTS: None,
        DATA_PROJEKT_DATEN: None,
        DATA_COST_RESULTS: None,
        DATA_COST_SUMMARIES: None,
        DATA_CUSTOM_KENNWERTE: None,
        DATA_MANUAL_COSTS: {},
        CFG_USE_CUSTOM_KENNWERTE: False,

        # Processing States
        PROC_API_RESPONSES: [],
        PROC_PROCESSING_LOG: [],
        PROC_TOTAL_COST: 0.0,
        PROC_ACTIVE_TAB: 0,

        # Configuration States
        CFG_API_KEY: None,
        CFG_API_KEY_VALIDATED: False,
        CFG_TOKEN_LIMIT: 50000,  # Default for Haiku
        CFG_FORCE_BATCH_API: False,
        CFG_COST_ESTIMATION_CONFIG: {},
        CFG_CLASSIFICATION_SETTINGS: {
            'use_batch': True,
            'batch_size': 40,
            'debug_mode': False,
            'confidence_threshold': 0.7,
            'model': 'claude-3-5-haiku-20241022',
            'bim_complexity': 'medium'
        },
        CFG_SELECTED_COST_LEVEL: 'mittel',

        # UI States
        UI_SELECTED_WORKFLOW_STEP: 0,
        UI_USE_PREPARED_DATA: False,
        UI_SELECTED_FOR_DETAILS: None,
    }

    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def get_state(key: str, default: Any = None) -> Any:
    """
    Sicherer Getter mit Fallback.

    Args:
        key: Session state key
        default: Fallback value if key doesn't exist

    Returns:
        Value from session state or default
    """
    return st.session_state.get(key, default)


def set_state(key: str, value: Any) -> None:
    """
    Setter für Session State.

    Args:
        key: Session state key
        value: Value to set
    """
    st.session_state[key] = value


def clear_classification_data() -> None:
    """Löscht alle Klassifizierungs-Daten (z.B. bei neuem Upload)."""
    keys_to_clear = [
        DATA_CLASSIFICATION_RESULTS,
        DATA_PREPARED,
        DATA_DEDUP_MAPPING,
        DATA_UNIQUE_ELEMENTS,
        PROC_API_RESPONSES,
        PROC_PROCESSING_LOG,
        PROC_TOTAL_COST,
    ]
    for key in keys_to_clear:
        if key in [PROC_API_RESPONSES, PROC_PROCESSING_LOG]:
            st.session_state[key] = []
        elif key == PROC_TOTAL_COST:
            st.session_state[key] = 0.0
        else:
            st.session_state[key] = None


def has_classification_results() -> bool:
    """
    Prüft ob Klassifizierungsergebnisse vorhanden sind.

    Returns:
        True if classification results exist and are not empty
    """
    results = get_state(DATA_CLASSIFICATION_RESULTS)
    if results is None:
        return False
    if isinstance(results, pd.DataFrame):
        return not results.empty
    return False


def has_project_data() -> bool:
    """
    Prüft ob Projektdaten vorhanden sind.

    Returns:
        True if project data exists
    """
    return get_state(DATA_PROJEKT_DATEN) is not None


def get_workflow_completion() -> Dict[str, bool]:
    """
    Gibt den Abschlussstatus aller Workflow-Schritte zurück.

    Returns:
        Dict mit Schritt-Namen und Completion-Status
    """
    return {
        'cost_estimation': bool(get_state(CFG_COST_ESTIMATION_CONFIG)),
        'data_preparation': get_state(DATA_PREPARED) is not None,
        'classification': has_classification_results(),
        'editing': has_classification_results(),  # Same as classification
        'evaluation': has_classification_results(),
    }


def validate_dataframe(
    df: pd.DataFrame,
    required_columns: List[str]
) -> Tuple[bool, str]:
    """
    Validiert einen DataFrame gegen erforderliche Spalten.

    Args:
        df: DataFrame zum Validieren
        required_columns: Liste erforderlicher Spaltennamen

    Returns:
        Tuple von (is_valid, error_message)
    """
    if df is None:
        return False, "DataFrame ist None"

    if df.empty:
        return False, "DataFrame ist leer"

    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        return False, f"Fehlende Spalten: {', '.join(missing_columns)}"

    return True, ""


def add_to_processing_log(
    message: str,
    level: str = 'info'
) -> None:
    """
    Fügt eine Nachricht zum Processing Log hinzu.

    Args:
        message: Log-Nachricht
        level: Log-Level (info, success, warning, error)
    """
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'level': level,
        'message': message
    }

    log = get_state(PROC_PROCESSING_LOG, [])
    log.append(log_entry)
    set_state(PROC_PROCESSING_LOG, log)


def get_classification_stats() -> Optional[Dict[str, Any]]:
    """
    Berechnet Statistiken über Klassifizierungsergebnisse.

    Returns:
        Dict mit Statistiken oder None wenn keine Daten
    """
    if not has_classification_results():
        return None

    df = get_state(DATA_CLASSIFICATION_RESULTS)

    stats = {
        'total_elements': len(df),
        'classified': len(df[df['bkp_code'].notna()]),
        'unclassified': len(df[df['bkp_code'].isna()]),
    }

    # Confidence statistics if available
    if 'confidence' in df.columns:
        confidence_data = df['confidence'].dropna()
        if len(confidence_data) > 0:
            stats['avg_confidence'] = confidence_data.mean()
            stats['min_confidence'] = confidence_data.min()
            stats['max_confidence'] = confidence_data.max()
            stats['high_confidence'] = len(df[df['confidence'] >= 0.9])
            stats['medium_confidence'] = len(df[(df['confidence'] >= 0.7) & (df['confidence'] < 0.9)])
            stats['low_confidence'] = len(df[df['confidence'] < 0.7])

    return stats
