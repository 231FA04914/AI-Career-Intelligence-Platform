"""
Test Suite for Task 6: Processing API & Service Integration Pipeline
Tests full end-to-end orchestration:
Upload/Audio -> Whisper -> Transcript -> LLM Processing -> Summary
-> Action Extraction -> Participant Mapping -> Database Persistence.
"""

import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline import MeetingIntelligencePipeline
from src.database import DatabaseManager


class TestPipelineTask6:
    """Test suite for Task 6 Pipeline Integration."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_pipeline.db"
        self.db = DatabaseManager(db_path=str(self.db_path))

        self.mock_audio = Mock()
        self.mock_transcriber = Mock()
        self.mock_llm = Mock()

        # Mock LLM process_transcript response
        self.mock_llm.process_transcript.return_value = {
            "summary": "Team aligned on mobile release and delegated action items.",
            "decisions": ["Proceed with mobile app release."],
            "action_items": [
                {"action": "Complete API integration", "owner": "Ravi", "deadline": "Friday", "priority": "High", "status": "Pending"},
                {"action": "Prepare UI testing report", "owner": "Priya", "deadline": "Monday", "priority": "Medium", "status": "In Progress"}
            ],
            "participants": ["Ravi", "Priya"],
            "key_points": ["Mobile app release planning"],
            "deadlines": ["Friday", "Monday"],
            "priorities": [{"item": "API integration", "priority": "High"}]
        }

        # Mock specialized action extractor prompt response
        self.mock_llm._call_llm_with_retry.return_value = '{"action_items": [{"action": "Complete API integration", "owner": "Ravi", "deadline": "Friday", "priority": "High", "status": "Pending"}, {"action": "Prepare UI testing report", "owner": "Priya", "deadline": "Monday", "priority": "Medium", "status": "In Progress"}]}'

        self.pipeline = MeetingIntelligencePipeline(
            audio_processor=self.mock_audio,
            transcriber=self.mock_transcriber,
            llm_service=self.mock_llm,
            db_manager=self.db
        )

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_transcript_text_pipeline(self):
        """Test pipeline starting from transcript text."""
        progress_events = []
        def on_progress(msg, pct):
            progress_events.append((msg, pct))

        transcript = "Ravi will complete API integration by Friday. Priya will prepare the UI testing report. The decision is to proceed with the mobile release."
        result = self.pipeline.process_transcript_text(
            transcript_text=transcript,
            meeting_title="Sprint Planning Meeting",
            original_filename="sprint_audio.mp4",
            duration=95.0,
            progress_callback=on_progress
        )

        assert result["database_persisted"] is True
        assert result["meeting_id"] is not None
        assert "mobile release" in result["summary"]
        assert len(result["decisions"]) == 1
        assert len(result["action_items"]) == 2
        assert len(result["participants"]) == 2
        assert len(progress_events) >= 4

        # Verify database record exists
        db_record = self.db.get_meeting(result["meeting_id"])
        assert db_record is not None
        assert db_record["title"] == "Sprint Planning Meeting"
        assert len(db_record["action_items"]) == 2
        print("✅ TEST 1 - Transcript text pipeline to database: PASSED")

    def test_audio_file_pipeline_mocked(self):
        """Test full audio file pipeline with Whisper transcription mock."""
        # Create a dummy test audio file
        test_file = Path(self.temp_dir) / "sample_meeting.mp3"
        test_file.write_bytes(b"dummy audio data")

        self.mock_audio.extract_audio.return_value = str(test_file)
        self.mock_audio.get_audio_duration.return_value = 180.0
        self.mock_transcriber.transcribe.return_value = {
            "text": "Ravi agreed to complete API integration by Friday. Priya will handle UI testing. We will launch the mobile app as planned.",
            "duration": 180.0,
            "language": "en"
        }

        with patch.object(self.pipeline.file_validator, 'validate_file', return_value=(True, "")):
            with patch.object(self.pipeline.transcript_validator, 'validate_transcript', return_value=(True, "")):
                result = self.pipeline.process_audio_file(str(test_file), meeting_title="Mobile Launch Sync")

                assert result["database_persisted"] is True
                assert result["duration"] == 180.0
                assert result["title"] == "Mobile Launch Sync"

                # Check database
                db_record = self.db.get_meeting(result["meeting_id"])
                assert db_record is not None
                assert len(db_record["participants"]) == 2
                print("✅ TEST 2 - Full audio file pipeline: PASSED")


def run_all_tests():
    """Run all pipeline tests."""
    print("=" * 60)
    print("Running Task 6: Processing API & Service Pipeline Tests")
    print("=" * 60)
    print()

    tests = [
        "test_transcript_text_pipeline",
        "test_audio_file_pipeline_mocked"
    ]

    for test_name in tests:
        tester = TestPipelineTask6()
        tester.setup_method()
        getattr(tester, test_name)()
        tester.teardown_method()

    print()
    print("=" * 60)
    print("✅ All Task 6 Pipeline Tests PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
