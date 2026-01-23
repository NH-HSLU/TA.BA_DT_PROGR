"""
Shared helper modules for eBKP-H BIM data processing.
Provides BKP classification, batch processing, and reference data.
"""

# All imports are lazy-loaded via __getattr__ to prevent circular dependencies
# (Removed eager imports to avoid RecursionError with streamlit initialization)

__all__ = [
    'load_ebkp_catalog',
    'validate_bkp_code',
    'get_code_description',
    'filter_by_levels',
    'get_hauptgruppen',
    'batch_manager',
]

def __getattr__(name):
    """
    Lazy import for all module members to prevent circular dependencies.
    - Classes with external dependencies (anthropic) are imported on demand
    - Functions from ebkp_reference (which uses streamlit) are imported on demand
    - batch_manager module is imported on demand
    """
    # Lazy import for Anthropic-dependent classes
    if name == 'eBKPHClassifier':
        from .ebkp_h_classifier import eBKPHClassifier
        return eBKPHClassifier
    elif name == 'TokenRateLimiter':
        from .ebkp_h_classifier import TokenRateLimiter
        return TokenRateLimiter

    # Lazy import for ebkp_reference functions (to avoid streamlit import at module load)
    elif name == 'load_ebkp_catalog':
        from .ebkp_reference import load_ebkp_catalog
        return load_ebkp_catalog
    elif name == 'validate_bkp_code':
        from .ebkp_reference import validate_bkp_code
        return validate_bkp_code
    elif name == 'get_code_description':
        from .ebkp_reference import get_code_description
        return get_code_description
    elif name == 'filter_by_levels':
        from .ebkp_reference import filter_by_levels
        return filter_by_levels
    elif name == 'get_hauptgruppen':
        from .ebkp_reference import get_hauptgruppen
        return get_hauptgruppen

    # Lazy import for batch_manager module
    elif name == 'batch_manager':
        import importlib
        return importlib.import_module('.batch_manager', package='helpers_shared')

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
