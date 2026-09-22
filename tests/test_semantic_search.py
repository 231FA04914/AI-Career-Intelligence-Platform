"""
Test Suite for Milestone 3: Task 4 – Semantic Search
Tests the complete natural-language query flow:
User Query -> Query Embedding -> Vector Search -> Relevant Meetings -> Search Results

Validates:
- Correct relevant meeting retrieval for: "Which meeting discussed the database migration?"
- Sub-3-second latency SLA (< 3000ms)
- Dynamic generation on newly ingested meeting intelligence
- Relevance ranking and contextual snippet extraction
"""

import sys
import time
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import DatabaseManager
from src.embeddings import EmbeddingGenerator
from src.vector_db import VectorDatabase
from src.semantic_search import SemanticSearchEngine, RelevantMeeting, SemanticSearchResult


class TestSemanticSearchTask4:
    """Test suite for Milestone 3 Task 4: Semantic Search."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_semantic_search.db"
        self.db_manager = DatabaseManager(db_path=str(self.db_path))
        self.embedder = EmbeddingGenerator(dimension=64)
        self.vdb = VectorDatabase(
            db_manager=self.db_manager,
            embedding_generator=self.embedder
        )
        self.mock_llm = MagicMock()

        self.engine = SemanticSearchEngine(
            db_manager=self.db_manager,
            embedding_generator=self.embedder,
            vector_db=self.vdb,
            llm_service=self.mock_llm,
            max_latency_ms=3000.0
        )

        # 1. Seed Meeting 1: Database Migration
        self.m1_id = self.db_manager.save_meeting_intelligence(
            title="Database Migration & Schema Refactoring",
            transcript_text=(
                "Ravi discussed the PostgreSQL database migration strategy. "
                "We need to migrate legacy MySQL tables into PostgreSQL 16 schema by Friday. "
                "Alice will supervise database connection pooling and zero-downtime cutover."
            ),
            summary_text="Engineering sync on PostgreSQL database migration, table partitioning, and connection pooling.",
            decisions=[
                "Migrate production database from MySQL to PostgreSQL 16.",
                "Use connection pooling with PgBouncer."
            ],
            action_items=[
                {"id": "act_m1_1", "action": "Run database migration scripts", "owner": "Ravi", "deadline": "Friday", "priority": "High", "status": "In Progress"},
                {"id": "act_m1_2", "action": "Configure PgBouncer pooling", "owner": "Alice", "deadline": "Monday", "priority": "Medium", "status": "Pending"}
            ],
            participants=[{"name": "Ravi", "canonical_name": "Ravi"}, {"name": "Alice", "canonical_name": "Alice"}],
            original_filename="db_migration_sync.mp4",
            duration=3600.0
        )

        # 2. Seed Meeting 2: Frontend Design System
        self.m2_id = self.db_manager.save_meeting_intelligence(
            title="Frontend UI Design System & Figma Tokens",
            transcript_text=(
                "Priya presented the dark mode color tokens in Figma. "
                "The web team will implement React components using Tailwind CSS. "
                "John will optimize bundle size and page load speed."
            ),
            summary_text="Design review of Tailwind UI components, Figma color tokens, and web performance.",
            decisions=[
                "Adopt Tailwind CSS for all web components.",
                "Implement dark mode toggle."
            ],
            action_items=[
                {"id": "act_m2_1", "action": "Implement React button components", "owner": "Priya", "deadline": "Wednesday", "priority": "High", "status": "Pending"}
            ],
            participants=[{"name": "Priya", "canonical_name": "Priya"}, {"name": "John", "canonical_name": "John"}],
            original_filename="frontend_ui.mp4",
            duration=1800.0
        )

        # 3. Seed Meeting 3: Marketing & User Acquisition
        self.m3_id = self.db_manager.save_meeting_intelligence(
            title="Q4 Marketing Campaign & Social Media Ads",
            transcript_text=(
                "Bob reviewed paid advertising campaigns on LinkedIn and Twitter. "
                "Sarah will finalize the marketing budget and creative copywriting assets."
            ),
            summary_text="Marketing team planned Q4 digital ad campaigns and budget allocation.",
            decisions=["Approve $30,000 digital advertising spend."],
            action_items=[
                {"id": "act_m3_1", "action": "Deliver ad creative copy", "owner": "Sarah", "deadline": "Next week", "priority": "Medium", "status": "Pending"}
            ],
            participants=[{"name": "Bob", "canonical_name": "Bob"}, {"name": "Sarah", "canonical_name": "Sarah"}],
            original_filename="marketing_q4.mp3",
            duration=1200.0
        )

        # Index vectors for all 3 meetings
        for m_id, m_data in [
            (self.m1_id, self.db_manager.get_meeting(self.m1_id)),
            (self.m2_id, self.db_manager.get_meeting(self.m2_id)),
            (self.m3_id, self.db_manager.get_meeting(self.m3_id))
        ]:
            embs = self.embedder.generate_all_meeting_embeddings(
                meeting_id=m_id,
                transcript_text=m_data["transcript_text"],
                summary_text=m_data["summary"],
                decisions=m_data["decisions"],
                action_items=m_data["action_items"]
            )
            self.vdb.insert_batch(embs)

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_database_migration_natural_language_query(self):
        """
        Explicit Milestone 3 Task 4 Requirement:
        Query: "Which meeting discussed the database migration?"
        Must return the database migration meeting with highest relevance rank.
        """
        query = "Which meeting discussed the database migration?"
        result = self.engine.search(query, top_k_meetings=3)

        assert isinstance(result, SemanticSearchResult)
        assert result.total_meetings_found >= 1
        top_meeting = result.relevant_meetings[0]

        # Verify correct meeting returned
        assert top_meeting.meeting_id == self.m1_id
        assert top_meeting.title == "Database Migration & Schema Refactoring"
        assert top_meeting.relevance_score > 0.3
        assert "database" in top_meeting.best_matching_text.lower() or "migration" in top_meeting.best_matching_text.lower()
        assert result.direct_answer is not None
        assert "Database Migration & Schema Refactoring" in result.direct_answer

    def test_sub_3_second_latency_sla(self):
        """
        Explicit Milestone 3 Task 4 Requirement:
        The project requires relevant meetings to be retrieved within 3 seconds (< 3000ms).
        """
        queries = [
            "Which meeting discussed the database migration?",
            "Who is working on the frontend design system?",
            "What decisions were made about paid marketing ads?",
            "Tell me about PostgreSQL 16 schema refactoring",
            "Show action items for Priya"
        ]

        latencies = []
        for q in queries:
            res = self.engine.search(q, top_k_meetings=3)
            assert res.sla_met is True
            assert res.latency_ms < 3000.0, f"Query '{q}' took {res.latency_ms}ms, exceeding 3000ms SLA!"
            latencies.append(res.latency_ms)

        avg_latency = sum(latencies) / len(latencies)
        print(f"✅ Semantic search average latency: {avg_latency:.2f}ms (All well below 3000ms SLA)")

    def test_semantic_search_full_flow(self):
        """
        Verify the complete 5-step flow:
        User Query -> Query Embedding -> Vector Search -> Relevant Meetings -> Search Results
        """
        query = "Frontend UI design tokens and Tailwind CSS"
        res = self.engine.search(query, top_k_meetings=2)

        # 1. Query
        assert res.query == query
        # 2. Query Embedding
        assert res.query_vector_dim == 64
        # 3. Vector search executed
        assert res.total_meetings_found >= 1
        # 4. Relevant meetings ranked
        top_m = res.relevant_meetings[0]
        assert top_m.meeting_id == self.m2_id
        assert top_m.title == "Frontend UI Design System & Figma Tokens"
        assert len(top_m.snippets) > 0
        assert "decision" in top_m.matched_entities or "summary" in top_m.matched_entities or "transcript_section" in top_m.matched_entities
        # 5. Search results formatted with direct answer
        assert res.direct_answer is not None

    def test_dynamic_generation_on_newly_added_meetings(self):
        """
        Verify that newly added meetings are dynamically searchable without restarting or manual reloads.
        """
        # Search before new meeting exists
        q = "Cloud Kubernetes cluster security audit"
        res_before = self.engine.search(q, top_k_meetings=1)
        top_id_before = res_before.relevant_meetings[0].meeting_id if res_before.relevant_meetings else None

        # Dynamically add new meeting
        new_m_id = self.db_manager.save_meeting_intelligence(
            title="Kubernetes Security & SOC2 Compliance",
            transcript_text="Diana is running penetration tests and security vulnerability scans on the EKS Kubernetes cluster.",
            summary_text="Security team discussed Kubernetes SOC2 compliance and cluster vulnerability remediation.",
            decisions=["Enforce network security policies on all pods."],
            action_items=[{"action": "Remediate open cluster vulnerabilities", "owner": "Diana", "priority": "High", "status": "Pending"}],
            participants=[{"name": "Diana", "canonical_name": "Diana"}]
        )

        # Dynamic embedding generation
        new_embs = self.embedder.generate_all_meeting_embeddings(
            meeting_id=new_m_id,
            transcript_text="Diana is running penetration tests and security vulnerability scans on the EKS Kubernetes cluster.",
            summary_text="Security team discussed Kubernetes SOC2 compliance.",
            decisions=["Enforce network security policies."],
            action_items=[{"action": "Remediate vulnerabilities", "owner": "Diana"}]
        )
        self.vdb.insert_batch(new_embs)

        # Search immediately after ingestion
        res_after = self.engine.search(q, top_k_meetings=1)
        assert len(res_after.relevant_meetings) >= 1
        assert res_after.relevant_meetings[0].meeting_id == new_m_id
        assert res_after.relevant_meetings[0].title == "Kubernetes Security & SOC2 Compliance"
        assert res_after.sla_met is True

    def test_metadata_filtered_semantic_search(self):
        """Test combining natural language semantic search with metadata filters."""
        # Query with owner filter
        res_ravi = self.engine.search(
            query="tasks and deliverables",
            filters={"owner": "Ravi"}
        )
        assert len(res_ravi.relevant_meetings) >= 1
        assert res_ravi.relevant_meetings[0].meeting_id == self.m1_id

    def test_edge_cases_empty_and_special_chars(self):
        """Test edge cases with empty queries and special characters."""
        res_empty = self.engine.search("")
        assert res_empty.total_meetings_found == 0
        assert res_empty.sla_met is True

        res_special = self.engine.search("@#$%^&*()_+")
        assert res_special.sla_met is True

    def test_llm_direct_answer_synthesis(self):
        """Test LLM direct answer synthesis when LLM is available."""
        self.mock_llm.generate.return_value = (
            "The Database Migration & Schema Refactoring meeting (ID: " + self.m1_id + ") "
            "discussed migrating legacy MySQL tables into PostgreSQL 16 by Friday."
        )

        res = self.engine.search("Which meeting discussed database migration?", include_direct_answer=True)
        assert "Database Migration & Schema Refactoring" in res.direct_answer
        assert res.sla_met is True
