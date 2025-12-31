"""
MODULE DESCRIPTION
Dieses Modul enthält Konfiguration für die Interaktion mit Anthropic's AI Claude.

Hauptfunktion: BKP-Klassifizierung von Revit Bauelementen
Siehe: BKP_Classifier.py für die Implementation
"""

# Der BKP Classifier ist in BKP_Classifier.py implementiert
# Import hier für Kompatibilität:
try:
    from .ebkp_h_classifier import eBKPHClassifier, classify_revit_element
    __all__ = ['eBKPHClassifier', 'classify_revit_element']
except ImportError:
    from ebkp_h_classifier import eBKPHClassifier, classify_revit_element
    __all__ = ['eBKPHClassifier', 'classify_revit_element']