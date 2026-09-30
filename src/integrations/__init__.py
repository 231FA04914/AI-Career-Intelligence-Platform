"""
Meeting Platform Integrations Module (Milestone 4 - Tasks 4 & 5)
Provides cloud recording ingestion and webhook automation for Zoom and Google Meet.
"""

from .zoom import ZoomIntegration
from .google_meet import GoogleMeetIntegration

__all__ = ["ZoomIntegration", "GoogleMeetIntegration"]
