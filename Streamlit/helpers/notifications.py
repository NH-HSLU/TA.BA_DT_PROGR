"""
Toast Notification System für Streamlit
Zentrale Benachrichtigungsfunktion für User Feedback
"""

import streamlit as st
from enum import Enum


class NotificationType(Enum):
    """Notification-Typen mit Icons"""
    SUCCESS = "✅"
    ERROR = "❌"
    WARNING = "⚠️"
    INFO = "ℹ️"


def toast(message: str, notification_type: NotificationType = NotificationType.INFO):
    """
    Zeigt Toast-Benachrichtigung an

    Args:
        message: Anzuzeigende Nachricht
        notification_type: Typ der Benachrichtigung (SUCCESS, ERROR, WARNING, INFO)

    Example:
        toast("Klassifizierung abgeschlossen!", NotificationType.SUCCESS)
        toast("API-Key fehlt", NotificationType.ERROR)
    """
    st.toast(message, icon=notification_type.value)
