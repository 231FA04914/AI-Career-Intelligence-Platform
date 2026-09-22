"""
Test Suite for Task 5: Meeting Data Model & Database Persistence
Tests SQLite schema, relational persistence, queries, updates, and cascading deletes.
"""

import sys
import shutil
import tempfile
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import DatabaseManager


class TestDatabaseManagerTask5:
    """Test suite for Task 5 Database Persistence."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_meetings.db"
        self.db = DatabaseManager(db_path=str(self.db_path))

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_and_get_meeting(self):
        """Test persisting complete meeting intelligence and retrieving by ID."""
        meeting_id = self.db.save_meeting_intelligence(
            title="Sprint Planning Q3",
            transcript_text="Ravi will finish API integration by Friday. Priya is handling UI testing.",
            summary_text="The team discussed the upcoming sprint tasks.",
            decisions=["Proceed with v2 release."],
            action_items=[
                {"action": "Complete API integration", "owner": "Ravi", "deadline": "Friday", "priority": "High", "status": "Pending"},
                {"action": "Prepare UI testing report", "owner": "Priya", "deadline": "Monday", "priority": "Medium", "status": "In Progress"}
            ],
            participants=[
                {"name": "Ravi", "canonical_name": "Ravi"},
                {"name": "Priya", "canonical_name": "Priya"}
            ],
            original_filename="meeting_audio.mp4",
            duration=120.5
        )

        assert meeting_id is not None

        # Retrieve meeting
        record = self.db.get_meeting(meeting_id)
        assert record is not None
        assert record["title"] == "Sprint Planning Q3"
        assert record["summary"] == "The team discussed the upcoming sprint tasks."
        assert len(record["decisions"]) == 1
        assert record["decisions"][0] == "Proceed with v2 release."
        assert len(record["action_items"]) == 2
        assert len(record["participants"]) == 2
        print("✅ TEST 1 - Save and get meeting intelligence: PASSED")

    def test_get_all_meetings_and_counts(self):
        """Test querying all meetings summary list with counts."""
        self.db.save_meeting_intelligence(
            title="Meeting 1",
            transcript_text="Transcript 1",
            summary_text="Summary 1",
            decisions=["Dec 1"],
            action_items=[{"action": "Act 1", "owner": "Alice"}],
            participants=[{"name": "Alice", "canonical_name": "Alice"}]
        )
        self.db.save_meeting_intelligence(
            title="Meeting 2",
            transcript_text="Transcript 2",
            summary_text="Summary 2",
            decisions=[],
            action_items=[],
            participants=[]
        )

        all_meetings = self.db.get_all_meetings()
        assert len(all_meetings) == 2
        assert all_meetings[0]["title"] == "Meeting 2"  # newest first
        assert all_meetings[1]["action_item_count"] == 1
        print("✅ TEST 2 - Get all meetings with counts: PASSED")

    def test_get_and_filter_action_items(self):
        """Test querying action items with status and owner filters."""
        self.db.save_meeting_intelligence(
            title="Team Sync",
            transcript_text="...",
            summary_text="...",
            decisions=[],
            action_items=[
                {"action": "Task A", "owner": "Ravi", "status": "Pending", "priority": "High"},
                {"action": "Task B", "owner": "Ravi", "status": "Completed", "priority": "Low"},
                {"action": "Task C", "owner": "Priya", "status": "Pending", "priority": "Medium"}
            ],
            participants=[]
        )

        # Filter by owner
        ravi_tasks = self.db.get_all_action_items(owner="Ravi")
        assert len(ravi_tasks) == 2

        # Filter by status
        completed_tasks = self.db.get_all_action_items(status="Completed")
        assert len(completed_tasks) == 1
        assert completed_tasks[0]["action"] == "Task B"
        print("✅ TEST 3 - Query & filter action items: PASSED")

    def test_update_action_item_status(self):
        """Test updating action item status."""
        self.db.save_meeting_intelligence(
            title="Sync",
            transcript_text="...",
            summary_text="...",
            decisions=[],
            action_items=[{"id": "act_test_1", "action": "Fix bug", "status": "Pending"}],
            participants=[]
        )

        success = self.db.update_action_item_status("act_test_1", "Completed")
        assert success is True

        tasks = self.db.get_all_action_items(status="Completed")
        assert len(tasks) == 1
        assert tasks[0]["id"] == "act_test_1"
        print("✅ TEST 4 - Update action item status: PASSED")

    def test_cascading_delete_meeting(self):
        """Test deleting a meeting removes child records."""
        meeting_id = self.db.save_meeting_intelligence(
            title="To Delete",
            transcript_text="...",
            summary_text="...",
            decisions=["Dec 1"],
            action_items=[{"action": "Act 1"}],
            participants=[{"name": "Bob", "canonical_name": "Bob"}]
        )

        assert self.db.get_meeting(meeting_id) is not None
        deleted = self.db.delete_meeting(meeting_id)
        assert deleted is True
        assert self.db.get_meeting(meeting_id) is None
        assert len(self.db.get_all_action_items()) == 0
        print("✅ TEST 5 - Cascading delete meeting: PASSED")

    def test_search_and_integrity_verification(self):
        """Test database search methods across entities and integrity verification."""
        m_id = self.db.save_meeting_intelligence(
            title="Sprint Review",
            transcript_text="Alice completed the payment API deployment. Bob needs to finish docs.",
            summary_text="Sprint review covered payment API deployment and documentation.",
            decisions=["Deploy payment service to staging."],
            action_items=[
                {"action": "Deploy payment service", "owner": "Alice", "deadline": "Friday", "priority": "High", "status": "Completed"},
                {"action": "Write API docs", "owner": "Bob", "deadline": "Monday", "priority": "Medium", "status": "Pending"}
            ],
            participants=[
                {"name": "Alice", "canonical_name": "Alice", "role": "Backend Lead"},
                {"name": "Bob", "canonical_name": "Bob", "role": "Technical Writer"}
            ],
            original_filename="sprint_review.mp4"
        )

        # 1. Search metadata
        assert len(self.db.search_meetings_raw("Sprint")) == 1
        # 2. Search transcripts
        assert len(self.db.search_transcripts_raw("payment API")) == 1
        # 3. Search summaries
        assert len(self.db.search_summaries_raw("documentation")) == 1
        # 4. Search decisions
        assert len(self.db.search_decisions_raw("staging")) == 1
        # 5. Search action items
        assert len(self.db.search_action_items_raw(query="docs")) == 1
        # 6. Search participants
        assert len(self.db.search_participants_raw("Alice")) == 1
        # 7. Search deadlines
        assert len(self.db.search_deadlines_raw("Friday")) == 1

        # 8. Verify database integrity
        audit = self.db.verify_database_integrity()
        assert audit["is_healthy"] is True
        assert audit["meeting_count"] == 1
        assert audit["summary_count"] == 1
        assert audit["decision_count"] == 1
        assert audit["action_count"] == 2
        assert audit["participant_count"] == 2
        assert audit["orphans"]["summaries"] == 0
        print("✅ TEST 6 - Database search and integrity verification: PASSED")


def run_all_tests():
    """Run all Task 5 database tests."""
    print("=" * 60)
    print("Running Task 5: Database Persistence Tests")
    print("=" * 60)
    print()

    tests = [
        "test_save_and_get_meeting",
        "test_get_all_meetings_and_counts",
        "test_get_and_filter_action_items",
        "test_update_action_item_status",
        "test_cascading_delete_meeting"
    ]

    for test_name in tests:
        tester = TestDatabaseManagerTask5()
        tester.setup_method()
        getattr(tester, test_name)()
        tester.teardown_method()

    print()
    print("=" * 60)
    print("✅ All Task 5 Database Tests PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
