"""
Test Suite for Milestone 3: Task 1 – Meeting Knowledge Repository
Tests organization, indexing, multi-entity search (metadata, transcript, summary,
decisions, action items, participants, deadlines), AI search with citations,
and database record linkage verification.
"""

import sys
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import DatabaseManager
from src.repository import MeetingKnowledgeRepository


class TestMeetingKnowledgeRepository:
    """Test suite for Milestone 3 Task 1: Meeting Knowledge Repository."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_knowledge_repo.db"
        self.db_manager = DatabaseManager(db_path=str(self.db_path))
        self.mock_llm = MagicMock()
        self.repo = MeetingKnowledgeRepository(
            db_manager=self.db_manager,
            llm_service=self.mock_llm
        )

        # Seed sample historical meetings
        self.m1_id = self.db_manager.save_meeting_intelligence(
            title="Q3 Roadmap & Backend Architecture",
            transcript_text="Ravi will deploy the new PostgreSQL database and migrate existing tables by Friday. Priya is responsible for leading the front-end redesign using React. Alice will review security compliance.",
            summary_text="The engineering leadership aligned on the Q3 roadmap. Ravi takes ownership of backend infrastructure and DB migration, while Priya leads UI architecture.",
            decisions=[
                "Migrate legacy database schema to PostgreSQL 16.",
                "Adopt Tailwind CSS for next-generation UI components."
            ],
            action_items=[
                {
                    "action": "Deploy PostgreSQL database and run schema migration",
                    "owner": "Ravi",
                    "deadline": "2026-09-25",
                    "priority": "High",
                    "status": "In Progress"
                },
                {
                    "action": "Complete React UI component redesign",
                    "owner": "Priya",
                    "deadline": "2026-09-30",
                    "priority": "Medium",
                    "status": "Pending"
                },
                {
                    "action": "Perform security audit",
                    "owner": "Alice",
                    "deadline": "2026-10-05",
                    "priority": "High",
                    "status": "Pending"
                }
            ],
            participants=[
                {"name": "Ravi", "canonical_name": "Ravi", "role": "Lead Architect"},
                {"name": "Priya", "canonical_name": "Priya", "role": "UI Lead"},
                {"name": "Alice", "canonical_name": "Alice", "role": "Security Engineer"}
            ],
            original_filename="q3_roadmap_sync.mp4",
            duration=3600.0
        )

        self.m2_id = self.db_manager.save_meeting_intelligence(
            title="Marketing Strategy & Launch Campaign",
            transcript_text="Bob presented the global launch timeline. John will finalize social media ad spend before next Wednesday. Priya will supply product demo screenshots.",
            summary_text="Marketing team planned the worldwide launch event and social media advertising strategy.",
            decisions=[
                "Approve $50,000 budget for paid social media campaigns."
            ],
            action_items=[
                {
                    "action": "Finalize ad spend budget allocation",
                    "owner": "John",
                    "deadline": "Next Wednesday",
                    "priority": "High",
                    "status": "Completed"
                },
                {
                    "action": "Deliver product demo screenshots",
                    "owner": "Priya",
                    "deadline": "Friday",
                    "priority": "Low",
                    "status": "Pending"
                }
            ],
            participants=[
                {"name": "Bob", "canonical_name": "Bob", "role": "CMO"},
                {"name": "John", "canonical_name": "John", "role": "Marketing Manager"},
                {"name": "Priya", "canonical_name": "Priya", "role": "UI Lead"}
            ],
            original_filename="marketing_sync.mp3",
            duration=1800.0
        )

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_search_metadata(self):
        """Test searching meeting metadata by title and filename."""
        results = self.repo.search_metadata("Architecture")
        assert len(results) == 1
        assert results[0]["id"] == self.m1_id
        assert results[0]["title"] == "Q3 Roadmap & Backend Architecture"
        assert results[0]["entity_type"] == "metadata"

        # Search by filename
        results_fn = self.repo.search_metadata("marketing_sync")
        assert len(results_fn) == 1
        assert results_fn[0]["id"] == self.m2_id

    def test_search_transcripts_with_snippets(self):
        """Test full-text search within transcripts and snippet extraction."""
        results = self.repo.search_transcripts("PostgreSQL")
        assert len(results) == 1
        assert results[0]["meeting_id"] == self.m1_id
        assert results[0]["entity_type"] == "transcript"
        assert len(results[0]["snippets"]) >= 1
        assert "PostgreSQL" in results[0]["snippets"][0]

    def test_search_summaries(self):
        """Test searching within executive summaries."""
        results = self.repo.search_summaries("worldwide launch")
        assert len(results) == 1
        assert results[0]["meeting_id"] == self.m2_id
        assert results[0]["entity_type"] == "summary"
        assert "worldwide launch" in results[0]["summary_text"]

    def test_search_decisions(self):
        """Test searching meeting decisions linked to parent meetings."""
        results = self.repo.search_decisions("Tailwind")
        assert len(results) == 1
        assert results[0]["meeting_id"] == self.m1_id
        assert "Tailwind CSS" in results[0]["decision_text"]
        assert results[0]["meeting_title"] == "Q3 Roadmap & Backend Architecture"

    def test_search_action_items_with_filters(self):
        """Test searching action items by query, owner, status, and priority."""
        # Query by keyword
        act_results = self.repo.search_action_items(query="redesign")
        assert len(act_results) == 1
        assert act_results[0]["owner"] == "Priya"
        assert act_results[0]["meeting_id"] == self.m1_id

        # Query by owner
        priya_tasks = self.repo.search_action_items(owner="Priya")
        assert len(priya_tasks) == 2  # 1 in meeting 1, 1 in meeting 2

        # Query by status
        completed_tasks = self.repo.search_action_items(status="Completed")
        assert len(completed_tasks) == 1
        assert completed_tasks[0]["owner"] == "John"

        # Query by priority
        high_tasks = self.repo.search_action_items(priority="High")
        assert len(high_tasks) == 3

    def test_search_participants_and_linkage(self):
        """Test searching participants and verifying linked meetings."""
        results = self.repo.search_participants("Priya")
        assert len(results) == 2
        meeting_ids = {r["meeting_id"] for r in results}
        assert self.m1_id in meeting_ids
        assert self.m2_id in meeting_ids
        assert all(r["canonical_name"] == "Priya" for r in results)

    def test_search_deadlines(self):
        """Test searching non-empty deadlines across meetings."""
        all_deadlines = self.repo.search_deadlines()
        assert len(all_deadlines) == 5

        sept_deadlines = self.repo.search_deadlines("2026-09")
        assert len(sept_deadlines) == 2
        assert {d["owner"] for d in sept_deadlines} == {"Ravi", "Priya"}

    def test_unified_search_all_entities(self):
        """Test unified search across all 7 entities simultaneously."""
        results = self.repo.search_all("Priya")
        assert results["total_matches"] > 0
        assert len(results["entities"]["participant"]) == 2
        assert len(results["entities"]["action_item"]) == 2
        assert len(results["entities"]["transcript"]) == 2

        # Verify linked meetings summary
        linked = results["linked_meetings"]
        assert self.m1_id in linked
        assert self.m2_id in linked
        assert "participant" in linked[self.m1_id]["match_types"]
        assert "action_item" in linked[self.m1_id]["match_types"]

    def test_verify_records_linkage_integrity(self):
        """
        Test Milestone 3 Task 1 requirement:
        Verify that existing database records can be retrieved correctly and linked to corresponding meeting.
        """
        verification = self.repo.verify_records_linkage()
        assert verification["is_healthy"] is True
        assert verification["total_meetings"] == 2
        assert verification["summary_count"] == 2
        assert verification["decision_count"] == 3
        assert verification["action_count"] == 5
        assert verification["participant_count"] == 6
        assert verification["orphans"]["summaries"] == 0
        assert verification["orphans"]["decisions"] == 0
        assert verification["orphans"]["actions"] == 0
        assert verification["orphans"]["participants"] == 0
        assert verification["meetings_verified"] == 2

        # Verify details of each meeting
        for v in verification["verification_details"]:
            assert v["linkage_valid"] is True
            assert v["has_transcript"] is True
            assert v["has_summary"] is True

    def test_get_meeting_knowledge_graph(self):
        """Test retrieving complete interconnected knowledge graph for a meeting."""
        graph = self.repo.get_meeting_knowledge_graph(self.m1_id)
        assert graph is not None
        assert graph["metadata"]["title"] == "Q3 Roadmap & Backend Architecture"
        assert len(graph["decisions"]) == 2
        assert len(graph["action_items"]) == 3
        assert len(graph["participants"]) == 3
        assert len(graph["deadlines"]) == 3
        assert graph["transcript"]["length"] > 0

    def test_ai_search_with_llm(self):
        """Test AI search answering questions with citations."""
        self.mock_llm.generate.return_value = (
            "According to the Q3 Roadmap & Backend Architecture meeting (ID: " + self.m1_id + "), "
            "Ravi is scheduled to deploy the PostgreSQL database by 2026-09-25."
        )

        response = self.repo.ai_search("What is Ravi responsible for?")
        assert response is not None
        assert "Ravi is scheduled" in response["answer"]
        assert len(response["citations"]) >= 1
        assert any(c["id"] == self.m1_id for c in response["citations"])

    def test_ai_search_fallback_without_llm(self):
        """Test AI search fallback behavior when LLM is unavailable."""
        repo_no_llm = MeetingKnowledgeRepository(db_manager=self.db_manager, llm_service=None)
        response = repo_no_llm.ai_search("PostgreSQL")
        assert response is not None
        assert "Search Results for" in response["answer"]
        assert len(response["citations"]) >= 1

    def test_edge_cases_empty_and_special_chars(self):
        """Test edge cases with empty query and special characters."""
        res_empty = self.repo.search_all("")
        assert res_empty["total_matches"] == 0

        res_special = self.repo.search_all("!@#$%^&*()")
        assert res_special["total_matches"] == 0

        # Non-existent ID graph
        graph_none = self.repo.get_meeting_knowledge_graph("non_existent_id")
        assert graph_none is None
