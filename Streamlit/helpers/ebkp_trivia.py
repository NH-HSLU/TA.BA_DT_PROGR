"""
eBKP-H Fun Facts und Trivia
Täglich wechselnde Wissensvermittlung über eBKP-H
"""

import hashlib
from datetime import datetime


EBKP_FUN_FACTS = [
    "🏗️ eBKP-H steht für 'erweiterte Baukostenplan Hochbau'",
    "📊 eBKP-H enthält exakt 10.210 detaillierte Kostenpositionen",
    "🇨🇭 eBKP-H ist der Standard für Kostenberechnung in der Schweiz seit 2001",
    "💰 Die Kostenermittlung nach SIA LHO 102 hat 6 Genauigkeitsstufen (±30% bis exakt)",
    "🔍 Level 1 der eBKP-H hat nur 14 Hauptgruppen",
    "📈 Mit allen 5 Levels können Sie bis zu 10.210 verschiedene Codes nutzen",
    "⚡ Claude 3.5 Haiku kostet nur ~$0.00005 pro klassifiziertem Element",
    "🎓 Dieses Projekt ist Teil von TA.BA_DT_PROGR an der HSLU",
    "🤖 AI-gestützte Klassifizierung reduziert manuelle Arbeit um ~90%",
    "💎 Präzise BKP-Klassifizierung spart bei großen Projekten 1000e CHF",
    "🌟 Die Hauptgruppe C umfasst alle elektrotechnischen Installationen",
    "🏆 Kostenvoranschlag (Stufe 6) ist die präziseste Kostenermittlung (±0%)",
]


def get_daily_fact() -> str:
    """
    Gibt einen täglichen Fun Fact basierend auf Datum zurück

    Returns:
        str: Ein Fun Fact aus der Liste

    Example:
        st.info(f"💡 **Wussten Sie?** {get_daily_fact()}")
    """
    day_hash = int(hashlib.md5(datetime.now().strftime('%Y-%m-%d').encode()).hexdigest(), 16)
    return EBKP_FUN_FACTS[day_hash % len(EBKP_FUN_FACTS)]
