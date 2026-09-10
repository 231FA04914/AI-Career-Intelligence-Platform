"""
Test Suite for Meeting Summarizer Module (Milestone 2 Task 2)
Tests summarizer logic, markdown/text formatting, export functions, and persistence.
"""

import sys
import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.summarizer import MeetingSummarizer, MeetingSummaryResult, ActionItem
from src.summary_manager import SummaryManager
from src.llm.exceptions import InputValidationError


class TestActionItem:
    """Test ActionItem formatting."""

    def test_full_action_item(self):
        """Test action item with owner and deadline."""
        item = ActionItem(action="Complete API integration", owner="Ravi", deadline="Friday")
        assert item.formatted_string() == "Complete API integration – Ravi Friday"
        print("✅ TEST 1 - Full action item format: PASSED")

    def test_action_item_owner_only(self):
        """Test action item with owner only."""
        item = ActionItem(action="Prepare UI testing report", owner="Priya")
        assert item.formatted_string() == "Prepare UI testing report – Priya"
        print("✅ TEST 2 - Owner-only action item: PASSED")

    def test_action_item_no_details(self):
        """Test action item without owner or deadline."""
        item = ActionItem(action="Refactor database queries")
        assert item.formatted_string() == "Refactor database queries"
        print("✅ TEST 3 - Basic action item: PASSED")


class TestMeetingSummarizer:
    """Test MeetingSummarizer logic and formatting."""

    def setup_method(self):
        self.mock_llm = Mock()
        self.summarizer = MeetingSummarizer(llm_service=self.mock_llm)

    def test_summarize_success(self):
        """Test meeting summarization flow."""
        self.mock_llm.process_transcript.return_value = {
            "summary": "The team discussed the mobile application launch and assigned API integration and UI testing responsibilities.",
            "decisions": ["Continue with the planned mobile application launch."],
            "action_items": [
                {"action": "Complete API integration", "owner": "Ravi", "deadline": "Friday", "priority": "High"},
                {"action": "Prepare UI testing report", "owner": "Priya", "deadline": None, "priority": "Medium"}
            ],
            "key_points": ["Mobile app launch planning", "Task delegation"],
            "participants": ["Ravi", "Priya"],
            "deadlines": ["Friday"],
            "priorities": [{"item": "API integration", "priority": "High"}]
        }

        transcript = "Team meeting: Ravi will complete API integration by Friday. Priya will prepare the UI testing report. We will proceed with the mobile launch."
        result = self.summarizer.summarize(transcript)

        assert isinstance(result, MeetingSummaryResult)
        assert "mobile application launch" in result.summary
        assert len(result.key_decisions) == 1
        assert len(result.action_items) == 2
        assert result.action_items[0]["owner"] == "Ravi"
        assert result.action_items[0]["deadline"] == "Friday"
        print("✅ TEST 4 - Summarize success: PASSED")

    def test_input_validation_empty(self):
        """Test summarization rejects empty input."""
        try:
            self.summarizer.summarize("")
            assert False, "Should raise InputValidationError"
        except InputValidationError:
            print("✅ TEST 5 - Empty input validation: PASSED")

    def test_format_markdown(self):
        """Test markdown output formatting matching Task 2 spec."""
        sample_data = {
            "summary": "The team discussed the mobile application launch and assigned API integration and UI testing responsibilities.",
            "key_decisions": ["Continue with the planned mobile application launch."],
            "action_items": [
                {"action": "Complete API integration", "owner": "Ravi", "deadline": "Friday"},
                {"action": "Prepare UI testing report", "owner": "Priya", "deadline": None}
            ]
        }

        md = self.summarizer.format_markdown(sample_data)
        assert "### Summary:" in md
        assert "The team discussed the mobile application launch" in md
        assert "### Key Decisions:" in md
        assert "- Continue with the planned mobile application launch." in md
        assert "### Action Items:" in md
        assert "- Complete API integration – Ravi Friday" in md
        assert "- Prepare UI testing report – Priya" in md
        print("✅ TEST 6 - Format Markdown: PASSED")

    def test_format_plain_text(self):
        """Test plain text formatting matching Task 2 spec."""
        sample_data = {
            "summary": "The team discussed the mobile application launch and assigned API integration and UI testing responsibilities.",
            "key_decisions": ["Continue with the planned mobile application launch."],
            "action_items": [
                {"action": "Complete API integration", "owner": "Ravi", "deadline": "Friday"},
                {"action": "Prepare UI testing report", "owner": "Priya", "deadline": None}
            ]
        }

        txt = self.summarizer.format_plain_text(sample_data)
        assert "Summary:\nThe team discussed" in txt
        assert "Key Decisions:\n- Continue with the planned mobile application launch." in txt
        assert "Action Items:\n- Complete API integration – Ravi Friday\n- Prepare UI testing report – Priya" in txt
        print("✅ TEST 7 - Format Plain Text: PASSED")

    def test_export_summary_json(self):
        """Test JSON export format."""
        sample_data = {
            "summary": "Meeting summary text.",
            "key_decisions": ["Decision 1"],
            "action_items": [{"action": "Task 1", "owner": "Alice", "deadline": "Monday"}]
        }

        json_out = self.summarizer.export_summary(sample_data, export_format="json")
        parsed = json.loads(json_out)
        assert parsed["summary"] == "Meeting summary text."
        assert parsed["key_decisions"] == ["Decision 1"]
        print("✅ TEST 8 - Export Summary JSON: PASSED")


class TestSummaryManager:
    """Test SummaryManager storage operations."""

    def setup_method(self):
        self.test_dir = tempfile.mkdtemp()
        self.manager = SummaryManager(storage_dir=self.test_dir)

    def teardown_method(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_save_load_list_delete(self):
        """Test saving, listing, loading, and deleting summaries."""
        data = {
            "summary": "Discussed roadmap.",
            "key_decisions": ["Ship v1.0"],
            "action_items": [{"action": "Code freeze", "owner": "Dev", "deadline": "Tomorrow"}]
        }

        saved_path = self.manager.save_summary(data, source_name="interview_audio.mp4")
        assert Path(saved_path).exists()
        print("✅ TEST 9 - SummaryManager save: PASSED")

        summaries = self.manager.list_summaries()
        assert len(summaries) == 1
        print("✅ TEST 10 - SummaryManager list: PASSED")

        loaded = self.manager.load_summary(saved_path)
        assert loaded["data"]["summary"] == "Discussed roadmap."
        assert loaded["source_name"] == "interview_audio.mp4"
        print("✅ TEST 11 - SummaryManager load: PASSED")

        deleted = self.manager.delete_summary(saved_path)
        assert deleted is True
        assert len(self.manager.list_summaries()) == 0
        print("✅ TEST 12 - SummaryManager delete: PASSED")


def run_all_tests():
    """Run all test suites."""
    print("=" * 60)
    print("Running Meeting Summarizer Tests (Milestone 2 Task 2)")
    print("=" * 60)
    print()

    # ActionItem tests
    t1 = TestActionItem()
    t1.test_full_action_item()
    t1.test_action_item_owner_only()
    t1.test_action_item_no_details()
    print()

    # Summarizer tests
    t2 = TestMeetingSummarizer()
    t2.setup_method()
    t2.test_summarize_success()
    t2.test_input_validation_empty()
    t2.test_format_markdown()
    t2.test_format_plain_text()
    t2.test_export_summary_json()
    print()

    # Storage tests
    t3 = TestSummaryManager()
    t3.setup_method()
    t3.test_save_load_list_delete()
    t3.teardown_method()
    print()

    print("=" * 60)
    print("✅ All Milestone 2 Task 2 Tests PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
