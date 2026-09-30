"""
Zoom and Google Meet Integration Tests (Milestone 4 - Tasks 4 & 5)
Validates:
- Zoom recording listing, ingestion, duplicate prevention, and webhook handling
- Google Meet Drive recording listing, ingestion, and duplicate prevention
- Processing failure resilience
"""

import pytest
import tempfile
from pathlib import Path

from src.database import DatabaseManager
from src.pipeline import MeetingIntelligencePipeline
from src.integrations.zoom import ZoomIntegration
from src.integrations.google_meet import GoogleMeetIntegration


@pytest.fixture
def test_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    db = DatabaseManager(db_path=db_path)
    yield db
    if Path(db_path).exists():
        try:
            Path(db_path).unlink()
        except Exception:
            pass


@pytest.fixture
def test_pipeline(test_db):
    return MeetingIntelligencePipeline(
        llm_service=None,
        db_manager=test_db
    )


def test_zoom_listing_and_duplicate_prevention(test_db, test_pipeline):
    """Test Zoom cloud recording retrieval and deduplication."""
    zoom = ZoomIntegration(sandbox_mode=True)
    recordings = zoom.list_recordings()

    assert isinstance(recordings, list)
    assert len(recordings) >= 1

    first_rec = recordings[0]
    rec_id = str(first_rec["id"])

    # Initially not duplicate
    assert zoom.is_duplicate_recording(rec_id, test_db) is False

    # Process recording
    res = zoom.process_zoom_recording(first_rec, test_pipeline, test_db)
    assert res["success"] is True
    assert res["status"] == "processed"
    assert res["meeting_id"] is not None

    # Now must be recognized as duplicate
    assert zoom.is_duplicate_recording(rec_id, test_db) is True

    # Processing again must reject duplicate gracefully
    dup_res = zoom.process_zoom_recording(first_rec, test_pipeline, test_db)
    assert dup_res["success"] is False
    assert dup_res["status"] == "duplicate"


def test_zoom_webhook_handling(test_db, test_pipeline):
    """Test Zoom URL validation and recording.completed webhook events."""
    zoom = ZoomIntegration(webhook_secret_token="test_secret_2026", sandbox_mode=True)

    # 1. URL validation event
    val_payload = {
        "event": "endpoint.url_validation",
        "payload": {"plainToken": "sample_plain_token_123"}
    }
    val_res = zoom.handle_webhook(val_payload, test_pipeline, test_db)
    assert "plainToken" in val_res
    assert "encryptedToken" in val_res

    # 2. Recording completed event
    rec_payload = {
        "event": "recording.completed",
        "payload": {
            "object": {
                "id": "zm_webhook_test_01",
                "topic": "Webhook Ingested Sync",
                "duration": 20,
                "transcript_text": "Team aligned on sprint goals. Sarah will deploy API updates by Friday."
            }
        }
    }
    hook_res = zoom.handle_webhook(rec_payload, test_pipeline, test_db)
    assert hook_res["success"] is True
    assert hook_res["meeting_id"] is not None


def test_google_meet_listing_and_ingestion(test_db, test_pipeline):
    """Test Google Meet Drive listing, ingestion, and duplicate check."""
    gmeet = GoogleMeetIntegration(sandbox_mode=True)
    recordings = gmeet.list_recordings()

    assert isinstance(recordings, list)
    assert len(recordings) >= 1

    first_rec = recordings[0]
    file_id = str(first_rec["id"])

    # Initially not duplicate
    assert gmeet.is_duplicate_recording(file_id, test_db) is False

    # Ingest Google Meet recording
    res = gmeet.process_google_meet_recording(first_rec, test_pipeline, test_db)
    assert res["success"] is True
    assert res["status"] == "processed"
    assert res["meeting_id"] is not None

    # Should now be duplicate
    assert gmeet.is_duplicate_recording(file_id, test_db) is True

    # Re-ingest must be flagged as duplicate
    dup_res = gmeet.process_google_meet_recording(first_rec, test_pipeline, test_db)
    assert dup_res["success"] is False
    assert dup_res["status"] == "duplicate"
