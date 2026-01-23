"""
Streamlit UI helper modules.
Provides sidebar navigation, notifications, configuration, and session state management.
"""

from .sidebar_navigation import (
    render_sidebar,
    render_page_header,
    render_divider,
    render_page_footer
)
from .notifications import toast, NotificationType
from .sia_lho_102_config import get_level_config
from .ebkp_trivia import get_daily_fact
from .logging_config import get_logger, setup_logging, cleanup_old_logs
from .session_state import (
    init_session_state,
    get_state,
    set_state,
    has_classification_results,
    validate_dataframe,
    clear_classification_data,
    get_workflow_completion,
    add_to_processing_log,
    get_classification_stats,
    # State key constants
    DATA_CLASSIFICATION_RESULTS,
    DATA_PREPARED,
    DATA_ORIGINAL_UPLOADED,
    DATA_DEDUP_MAPPING,
    DATA_UNIQUE_ELEMENTS,
    PROC_API_RESPONSES,
    PROC_PROCESSING_LOG,
    PROC_TOTAL_COST,
    PROC_ACTIVE_TAB,
    CFG_API_KEY,
    CFG_API_KEY_VALIDATED,
    CFG_CLASSIFICATION_SETTINGS,
    UI_USE_PREPARED_DATA,
)

__all__ = [
    'render_sidebar',
    'render_page_header',
    'render_divider',
    'render_page_footer',
    'toast',
    'NotificationType',
    'get_level_config',
    'get_daily_fact',
    'init_session_state',
    'get_state',
    'set_state',
    'has_classification_results',
    'validate_dataframe',
    'clear_classification_data',
    'get_workflow_completion',
    'add_to_processing_log',
    'get_classification_stats',
    'DATA_CLASSIFICATION_RESULTS',
    'DATA_PREPARED',
    'DATA_ORIGINAL_UPLOADED',
    'PROC_API_RESPONSES',
    'PROC_PROCESSING_LOG',
    'CFG_API_KEY',
]
