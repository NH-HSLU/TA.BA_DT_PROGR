"""
SIA LHO 102 Kostenermittlungs-Konfiguration
Zentrale Definition aller Kostenermittlungsarten und deren Parameter nach SIA LHO 102 Standard.
"""

from typing import Optional

# Definition aller 6 Kostenermittlungsstufen nach SIA LHO 102
COST_ESTIMATION_LEVELS = [
    {
        'level': 1,
        'name': 'Schätzung des Finanzbedarfs',
        'tolerance': 30,
        'ebkp_depth': 'Hauptgruppe eBKP',
        'ebkp_levels': [1],
        'project_phase': 'Strategische Planung',
        'phase_code': 'TP11',
        'description': 'Grobe Schätzung für strategische Entscheidungen auf Hauptgruppenebene',
        'emoji': '🎯'
    },
    {
        'level': 2,
        'name': 'Schätzung der Baukosten',
        'tolerance': 25,
        'ebkp_depth': 'Elementgruppe eBKP',
        'ebkp_levels': [1, 2],
        'project_phase': 'Vorstudie',
        'phase_code': 'TP21/22',
        'description': 'Kostenschätzung auf Elementgruppenebene',
        'emoji': '📋'
    },
    {
        'level': 3,
        'name': 'Kostengrobschätzung',
        'tolerance': 20,
        'ebkp_depth': 'Element eBKP',
        'ebkp_levels': [1, 2, 3],
        'project_phase': 'Studium von Lösungsmöglichkeiten',
        'phase_code': 'TP31',
        'description': 'Detaillierte Kostenschätzung nach Elementen',
        'emoji': '📊'
    },
    {
        'level': 4,
        'name': 'Kostenschätzung',
        'tolerance': 15,
        'ebkp_depth': 'Element eBKP',
        'ebkp_levels': [1, 2, 3],
        'project_phase': 'Vorprojekt',
        'phase_code': 'TP31',
        'description': 'Präzise Kostenschätzung für Vorprojekt',
        'emoji': '📐'
    },
    {
        'level': 5,
        'name': 'Kostenvoranschlag',
        'tolerance': 10,
        'ebkp_depth': 'Teilelement und Komponente eBKP ganz',
        'ebkp_levels': [1, 2, 3, 4, 5],
        'project_phase': 'Bauprojekt',
        'phase_code': 'TP32/33',
        'description': 'Vollständiger Kostenvoranschlag mit allen Details',
        'emoji': '🏗️'
    },
    {
        'level': 6,
        'name': 'Schlussabrechnung',
        'tolerance': 0,
        'ebkp_depth': 'Leistungsbeschreibung NPK',
        'ebkp_levels': [1, 2, 3, 4, 5],
        'project_phase': 'Ausschreibung Realisierung',
        'phase_code': 'TP41, TP51-53',
        'description': 'Finale Abrechnung nach Normalpositionen-Katalog',
        'emoji': '✅'
    }
]


def get_level_config(level: int) -> Optional[dict]:
    """
    Gibt Konfiguration für ein bestimmtes Level zurück.

    Args:
        level: Level-Nummer (1-6)

    Returns:
        Dictionary mit Level-Konfiguration oder None wenn nicht gefunden
    """
    for config in COST_ESTIMATION_LEVELS:
        if config['level'] == level:
            return config.copy()
    return None


def get_level_by_tolerance(tolerance: int) -> Optional[dict]:
    """
    Findet Level anhand der Toleranz.

    Args:
        tolerance: Toleranz in Prozent (30, 25, 20, 15, 10, 0)

    Returns:
        Dictionary mit Level-Konfiguration oder None wenn nicht gefunden
    """
    for config in COST_ESTIMATION_LEVELS:
        if config['tolerance'] == tolerance:
            return config.copy()
    return None


def format_tolerance(tolerance: int) -> str:
    """
    Formatiert Toleranz für Anzeige.

    Args:
        tolerance: Toleranz in Prozent

    Returns:
        Formatierter String (z.B. '± 25%' oder 'exakt' für 0%)
    """
    if tolerance == 0:
        return 'exakt'
    return f'± {tolerance}%'


def get_all_levels() -> list:
    """
    Gibt alle verfügbaren Levels zurück.

    Returns:
        Liste aller Level-Konfigurationen
    """
    return [config.copy() for config in COST_ESTIMATION_LEVELS]
