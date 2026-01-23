"""
Zentrale Konfigurationsdatei für die eBKP-H+.

Alle Hardcoded Values werden hier definiert für einfache Wartung.
"""

from pathlib import Path
from typing import Dict, List, Tuple


# === PATHS ===
PROJECT_ROOT = Path(__file__).parent.parent
HELPERS_SHARED_DIR = PROJECT_ROOT / "helpers_shared"
LOGS_DIR = PROJECT_ROOT / "Logs"
EBKP_CATALOG_PATH = HELPERS_SHARED_DIR / "eBKP-H.csv"


# === API CONFIGURATION ===
class APIConfig:
    """Anthropic API Konfiguration."""

    # Model Names
    DEFAULT_MODEL = "claude-3-5-haiku-20241022"
    HAIKU_MODEL = "claude-3-5-haiku-20241022"
    SONNET_MODEL = "claude-3-5-sonnet-20241022"
    OPUS_MODEL = "claude-opus-4-20250514"

    # Fallback
    FALLBACK_MODEL = "claude-3-haiku-20240307"

    # Rate Limits (tokens per minute)
    HAIKU_TOKEN_LIMIT = 50_000
    SONNET_TOKEN_LIMIT = 40_000
    OPUS_TOKEN_LIMIT = 10_000

    # Pricing (USD per 1M tokens) - Stand November 2024
    PRICING: Dict[str, Dict[str, float]] = {
        "claude-3-5-haiku-20241022": {
            "input": 0.80,
            "output": 4.00,
            "input_cached": 0.08,      # 90% discount
            "batch_discount": 0.50      # 50% discount for Batch API
        },
        "claude-3-5-sonnet-20241022": {
            "input": 3.00,
            "output": 15.00,
            "input_cached": 0.30,
            "batch_discount": 0.50
        },
        "claude-opus-4-20250514": {
            "input": 15.00,
            "output": 75.00,
            "input_cached": 1.50,
            "batch_discount": 0.50
        }
    }

    # Timeouts (seconds)
    DEFAULT_TIMEOUT = 30
    BATCH_TIMEOUT = 300

    # System Prompt Token Estimate
    SYSTEM_PROMPT_TOKENS = 3000
    CACHE_HIT_RATE = 0.4  # Conservative estimate (40%)


# === CLASSIFICATION CONFIGURATION ===
class ClassificationConfig:
    """BKP Klassifizierungs-Einstellungen."""

    # Batch Processing
    MIN_ELEMENTS_FOR_BATCH_API = 300  # Ab dieser Anzahl → Batch API empfehlen
    DEFAULT_BATCH_SIZE = 40           # Elemente pro Batch (Synchron-Modus)
    MAX_BATCH_SIZE = 100

    # Retry Settings
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds
    RETRY_BACKOFF_MULTIPLIER = 2

    # Confidence Thresholds
    HIGH_CONFIDENCE = 0.9
    MEDIUM_CONFIDENCE = 0.7
    LOW_CONFIDENCE = 0.5

    # Default Settings
    DEFAULT_SETTINGS = {
        'use_batch': True,
        'batch_size': DEFAULT_BATCH_SIZE,
        'debug_mode': False,
        'confidence_threshold': MEDIUM_CONFIDENCE,
        'model': APIConfig.DEFAULT_MODEL,
        'bim_complexity': 'medium'
    }


# === UI CONFIGURATION ===
class UIConfig:
    """Streamlit UI Einstellungen."""

    PAGE_ICON = "🏗️"
    LAYOUT = "wide"

    # Colors für Custom CSS
    COLORS = {
        'primary': '#667eea',
        'secondary': '#764ba2',
        'success': '#43e97b',
        'warning': '#fee140',
        'error': '#f5576c',
        'info': '#4facfe'
    }

    # Workflow Steps (Label, Filename)
    WORKFLOW_STEPS: List[Tuple[str, str]] = [
        ("1️⃣ Kostenermittlung", "01_Kostenermittlung.py"),
        ("2️⃣ Daten Vorbereiten", "02_Daten_Vorbereiten.py"),
        ("3️⃣ KI-Klassifizierung", "03_KI_Klassifizierung.py"),
        ("4️⃣ BKP Bearbeiten", "04_eBKP_Bearbeiten.py"),
        ("5️⃣ Daten Zusammenführen", "05_Daten_Zusammenfuehren.py"),
        ("6️⃣ Auswertung", "06_eBKP_Auswertung.py"),
    ]

    # Progress Bar Colors
    PROGRESS_COLORS = {
        'not_started': '#e0e0e0',
        'in_progress': '#4facfe',
        'completed': '#43e97b',
        'error': '#f5576c'
    }


# === DATA VALIDATION ===
class DataValidation:
    """Datenvalidierungs-Regeln."""

    # Required Columns (mindestens eine davon)
    REQUIRED_UPLOAD_COLUMNS = ['Elementtyp', 'Kategorie', 'Type', 'Category']

    # Required Columns after Classification
    REQUIRED_CLASSIFICATION_COLUMNS = ['bkp_code', 'bkp_description', 'confidence']

    # BKP Code Format (Regex)
    BKP_CODE_PATTERN = r'^[A-G][0-9.]*$'

    # File Size Limits
    MAX_CSV_SIZE_MB = 50
    MAX_ROWS = 100_000

    # Column Name Patterns for Auto-Detection
    TYPE_COLUMN_PATTERNS = ['elementtyp', 'type', 'family', 'name', 'typ']
    CATEGORY_COLUMN_PATTERNS = ['kategorie', 'category', 'class', 'gruppe']
    DESCRIPTION_COLUMN_PATTERNS = ['beschreibung', 'description', 'desc', 'zusatzinfo']
    FAMILY_COLUMN_PATTERNS = ['familie', 'family', 'familienname']


# === LOGGING ===
class LoggingConfig:
    """Logging-Einstellungen."""

    LOG_LEVEL = "INFO"
    LOG_FORMAT = '%(asctime)s | %(name)s | %(levelname)s | %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

    # Log File Settings
    LOG_FILE_PREFIX = "app"
    LOG_FILE_SUFFIX = ".log"

    # Log Retention
    MAX_LOG_AGE_DAYS = 30
    MAX_LOG_FILES = 50


# === DEDUPLICATION ===
class DeduplicationConfig:
    """Deduplizierungs-Einstellungen."""

    # Default columns for deduplication
    DEFAULT_DEDUP_COLUMNS = ['Elementtyp', 'Kategorie']

    # Minimum elements to suggest deduplication
    MIN_ELEMENTS_FOR_DEDUP = 100

    # Minimum dedup ratio to show savings (2.0 = 50% reduction)
    MIN_DEDUP_RATIO_FOR_DISPLAY = 1.5


# === EXPORT SETTINGS ===
class ExportConfig:
    """Export-Einstellungen."""

    CSV_SEPARATOR = ';'
    CSV_ENCODING = 'utf-8-sig'  # BOM for Excel compatibility

    # PDF Export
    PDF_PAGE_SIZE = 'A4'
    PDF_ORIENTATION = 'portrait'

    # Excel Export
    EXCEL_ENGINE = 'openpyxl'


# === HELPER FUNCTIONS ===
def get_model_pricing(model: str) -> Dict[str, float]:
    """
    Gibt Pricing für ein Modell zurück.

    Args:
        model: Model name

    Returns:
        Dict mit Pricing-Info oder Default für Haiku
    """
    return APIConfig.PRICING.get(
        model,
        APIConfig.PRICING[APIConfig.DEFAULT_MODEL]
    )


def get_token_limit(model: str) -> int:
    """
    Gibt Token-Limit für ein Modell zurück.

    Args:
        model: Model name

    Returns:
        Token limit per minute
    """
    if 'haiku' in model.lower():
        return APIConfig.HAIKU_TOKEN_LIMIT
    elif 'sonnet' in model.lower():
        return APIConfig.SONNET_TOKEN_LIMIT
    elif 'opus' in model.lower():
        return APIConfig.OPUS_TOKEN_LIMIT
    return APIConfig.HAIKU_TOKEN_LIMIT


def is_high_confidence(confidence: float) -> bool:
    """Prüft ob Konfidenz als hoch gilt."""
    return confidence >= ClassificationConfig.HIGH_CONFIDENCE


def is_medium_confidence(confidence: float) -> bool:
    """Prüft ob Konfidenz als mittel gilt."""
    return ClassificationConfig.MEDIUM_CONFIDENCE <= confidence < ClassificationConfig.HIGH_CONFIDENCE


def is_low_confidence(confidence: float) -> bool:
    """Prüft ob Konfidenz als niedrig gilt."""
    return confidence < ClassificationConfig.MEDIUM_CONFIDENCE
