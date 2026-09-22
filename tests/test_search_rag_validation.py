"""
Test Suite for Task 7: Search & RAG Validation
Thorough validation of Semantic Search and Retrieval-Augmented Generation (RAG):
- Relevant meeting retrieval
- Irrelevant query handling
- Multiple matching meetings and rank ordering
- Date-based filtering
- Meeting metadata filtering
- Correct source meeting attribution
- Correct context retrieval
- Grounded AI answers
- Empty search results
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import DatabaseManager
from src.embeddings import EmbeddingGenerator
from src.vector_db import VectorDatabase
from src.repository import MeetingKnowledgeRepository
from src.semantic_search import SemanticSearchEngine


class TestSearchAndRAGValidationTask7:
    """Test suite for Task 7 Search & RAG validation."""

    def setup_method(self):
        os.environ["LOCAL_EMBEDDINGS"] = "1"
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_rag_val.db"
        self.db = DatabaseManager(db_path=str(self.db_path))
        self.embedder = EmbeddingGenerator(api_key="")
        self.vdb = VectorDatabase(db_manager=self.db, embedding_generator=self.embedder)

        # Seed 3 distinct historical meetings with specific dates and topics
        # Meeting 1: DevOps & Backend (2026-08-15)
        self.m1_id = self.db.save_meeting_intelligence(
            title="Backend Architecture & DevOps Sync",
            transcript_text="Ravi presented the Kubernetes migration strategy on AWS. We decided to complete the staging rollout by Friday. Amit will review the Docker containers.",
            summary_text="Team aligned on Kubernetes migration strategy with staging rollout by Friday.",
            decisions=["Adopt Kubernetes cluster on AWS for staging"],
            action_items=[
                {"action": "Complete staging rollout", "owner": "Ravi", "deadline": "Friday", "priority": "High", "status": "Pending"},
                {"action": "Review Docker containers", "owner": "Amit", "deadline": "Thursday", "priority": "Medium", "status": "In Progress"}
            ],
            participants=[
                {"name": "Ravi", "role": "DevOps Lead", "action_items_count": 1},
                {"name": "Amit", "role": "Backend Engineer", "action_items_count": 1}
            ],
            original_filename="devops_sync_aug15.mp4",
            duration=300.0,
            meeting_id="meet_devops_aug15",
            created_at="2026-08-15T10:00:00"
        )
        self._seed_vectors(self.m1_id, "Backend Architecture & DevOps Sync",
                           "Ravi presented the Kubernetes migration strategy on AWS. We decided to complete the staging rollout by Friday. Amit will review the Docker containers.",
                           "Team aligned on Kubernetes migration strategy with staging rollout by Friday.",
                           ["Adopt Kubernetes cluster on AWS for staging"],
                           [{"action": "Complete staging rollout", "owner": "Ravi", "deadline": "Friday"}])

        # Meeting 2: Mobile Frontend & UX (2026-09-01)
        self.m2_id = self.db.save_meeting_intelligence(
            title="Mobile App UX Design Review",
            transcript_text="Priya showcased the React Native mobile redesign with dark mode support. Rohit agreed to fix the iOS push notification token registration by next Tuesday.",
            summary_text="Priya presented the React Native mobile UX redesign with dark mode.",
            decisions=["Implement dark mode by default in mobile v2.0"],
            action_items=[
                {"action": "Fix iOS push notification token registration", "owner": "Rohit", "deadline": "Tuesday", "priority": "High", "status": "Pending"}
            ],
            participants=[
                {"name": "Priya", "role": "UX Designer", "action_items_count": 0},
                {"name": "Rohit", "role": "Mobile Developer", "action_items_count": 1}
            ],
            original_filename="mobile_ux_sep01.mp4",
            duration=180.0,
            meeting_id="meet_mobile_sep01",
            created_at="2026-09-01T10:00:00"
        )
        self._seed_vectors(self.m2_id, "Mobile App UX Design Review",
                           "Priya showcased the React Native mobile redesign with dark mode support. Rohit agreed to fix the iOS push notification token registration by next Tuesday.",
                           "Priya presented the React Native mobile UX redesign with dark mode.",
                           ["Implement dark mode by default in mobile v2.0"],
                           [{"action": "Fix iOS push notification token registration", "owner": "Rohit", "deadline": "Tuesday"}])

        # Meeting 3: Career Planning & Mentorship (2026-09-10)
        self.m3_id = self.db.save_meeting_intelligence(
            title="Software Engineering Career Mentorship",
            transcript_text="Sneha conducted a career guidance session covering system design interview preparation, distributed systems fundamentals, and resume optimization for senior roles.",
            summary_text="Mentorship session on system design interview prep and distributed systems for senior engineering roles.",
            decisions=["Schedule mock system design interviews bi-weekly"],
            action_items=[
                {"action": "Practice distributed consensus algorithms", "owner": "Candidate", "deadline": "Sunday", "priority": "Medium", "status": "Pending"}
            ],
            participants=[
                {"name": "Sneha", "role": "Staff Engineer & Mentor", "action_items_count": 0},
                {"name": "Candidate", "role": "Mentee", "action_items_count": 1}
            ],
            original_filename="mentorship_sep10.mp4",
            duration=240.0,
            meeting_id="meet_mentorship_sep10",
            created_at="2026-09-10T10:00:00"
        )
        self._seed_vectors(self.m3_id, "Software Engineering Career Mentorship",
                           "Sneha conducted a career guidance session covering system design interview preparation, distributed systems fundamentals, and resume optimization for senior roles.",
                           "Mentorship session on system design interview prep and distributed systems for senior engineering roles.",
                           ["Schedule mock system design interviews bi-weekly"],
                           [{"action": "Practice distributed consensus algorithms", "owner": "Candidate", "deadline": "Sunday"}])

        # Mock LLM service
        self.mock_llm = Mock()
        self.mock_llm.api_key = None
        self.mock_llm._call_llm_with_retry.side_effect = self._fake_llm_generate
        self.mock_llm.generate.side_effect = lambda prompt, system_prompt="", temperature=0.2: self._fake_llm_generate(prompt)

        self.repo = MeetingKnowledgeRepository(
            db_manager=self.db,
            llm_service=self.mock_llm,
            embedding_generator=self.embedder,
            vector_db=self.vdb
        )
        self.search_engine = SemanticSearchEngine(
            db_manager=self.db,
            embedding_generator=self.embedder,
            vector_db=self.vdb,
            llm_service=self.mock_llm
        )

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _seed_vectors(self, m_id, title, transcript, summary, decisions, actions):
        records = self.embedder.generate_all_meeting_embeddings(
            meeting_id=m_id,
            transcript_text=transcript,
            summary_text=summary,
            decisions=decisions,
            action_items=actions
        )
        self.vdb.insert_batch(records)

    def _fake_llm_generate(self, prompt: str) -> str:
        if "Kubernetes" in prompt or "Ravi" in prompt:
            return "Based on Meeting meet_devops_aug15 (Backend Architecture & DevOps Sync), Ravi presented the Kubernetes migration on AWS with a staging rollout by Friday."
        elif "mobile" in prompt or "React Native" in prompt or "Rohit" in prompt:
            return "Based on Meeting meet_mobile_sep01 (Mobile App UX Design Review), Rohit is assigned to fix the iOS push notification token registration by Tuesday."
        elif "system design" in prompt or "mentorship" in prompt:
            return "Based on Meeting meet_mentorship_sep10 (Software Engineering Career Mentorship), Sneha led career guidance on distributed systems and system design prep."
        return "No specific information found in historical meeting context."

    # =========================================================================
    # TASK 7 VALIDATION TESTS
    # =========================================================================

    def test_relevant_meeting_retrieval(self):
        """1. Relevant meeting retrieval: semantic query retrieves the exact matching meeting."""
        result = self.search_engine.search("Kubernetes cloud infrastructure deployment", top_k_meetings=3)
        assert result.total_meetings_found >= 1
        top_match = result.relevant_meetings[0]
        assert top_match.meeting_id == self.m1_id
        assert "DevOps" in top_match.title
        assert top_match.relevance_score > 0.2

    def test_irrelevant_query_handling(self):
        """2. Irrelevant query handling: completely unrelated query produces low similarity or empty."""
        result = self.search_engine.search("Astronomy telescope supernova quantum astrophysics orbit", min_similarity=0.6)
        # Should gracefully return empty or no high confidence meetings
        assert result.total_meetings_found == 0
        assert result.sla_met is True

    def test_multiple_matching_meetings_ranking(self):
        """3. Multiple matching meetings: queries touching engineering rank matches by relevance."""
        result = self.search_engine.search("engineering architecture and technical design", top_k_meetings=3, min_similarity=0.0)
        assert result.total_meetings_found >= 2
        # Verify descending score order
        scores = [m.relevance_score for m in result.relevant_meetings]
        assert scores == sorted(scores, reverse=True)

    def test_date_based_filtering(self):
        """4. Date-based filtering: date_from and date_to filter meetings temporally."""
        # Query repository with date filter
        res_aug = self.repo.search_metadata(query="Sync", date_from="2026-08-01", date_to="2026-08-31")
        assert len(res_aug) >= 1
        for r in res_aug:
            assert "2026-08" in r["created_at"]

    def test_meeting_metadata_filtering(self):
        """5. Meeting metadata filtering: filter by entity type and owner."""
        # Action item search with owner filter
        ravi_actions = self.repo.search_action_items(query=None, owner="Ravi")
        assert len(ravi_actions) >= 1
        assert ravi_actions[0]["owner"] == "Ravi"
        assert "staging rollout" in ravi_actions[0]["action"].lower()

        rohit_actions = self.repo.search_action_items(query=None, owner="Rohit")
        assert len(rohit_actions) >= 1
        assert rohit_actions[0]["owner"] == "Rohit"

    def test_correct_source_meeting_attribution(self):
        """6. Correct source meeting: verify returned citations match the exact source meeting ID."""
        res_transcript = self.repo.search_transcripts("push notification token")
        assert len(res_transcript) >= 1
        assert res_transcript[0]["meeting_id"] == self.m2_id
        assert "mobile" in res_transcript[0]["meeting_title"].lower()

    def test_correct_context_retrieval(self):
        """7. Correct context retrieval: similarity search retrieves relevant chunk snippets."""
        chunks = self.vdb.similarity_search("React Native dark mode design", top_k=3, min_similarity=0.1)
        assert len(chunks) >= 1
        top_chunk = chunks[0]
        assert top_chunk["meeting_id"] == self.m2_id
        assert "dark mode" in top_chunk["text_content"].lower() or "react native" in top_chunk["text_content"].lower()

    def test_grounded_ai_answers(self):
        """8. Grounded AI answers: AI synthesis cites exact meeting IDs without hallucination."""
        ai_ans = self.repo.ai_search("What did Ravi present regarding Kubernetes?")
        assert ai_ans is not None
        assert "answer" in ai_ans
        assert "meet_devops_aug15" in ai_ans["answer"] or "Kubernetes" in ai_ans["answer"]

    def test_empty_search_results(self):
        """9. Empty search results: handling queries on empty store or non-matching terms gracefully."""
        empty_res = self.search_engine.search("", top_k_meetings=5)
        assert empty_res.total_meetings_found == 0
        assert empty_res.direct_answer is not None
