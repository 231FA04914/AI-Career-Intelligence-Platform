"""
Test Suite for Milestone 3: Task 2 – Embedding Generation
Tests embedding generation for transcript sections, summaries, decisions, and action items,
database persistence, meeting record linkage verification, cosine similarity ranking,
and semantic vector search.
"""

import sys
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import DatabaseManager
from src.embeddings import EmbeddingGenerator
from src.repository import MeetingKnowledgeRepository
from src.pipeline import MeetingIntelligencePipeline


class TestEmbeddingGenerationTask2:
    """Test suite for Milestone 3 Task 2: Embedding Generation."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_embeddings.db"
        self.db_manager = DatabaseManager(db_path=str(self.db_path))
        self.embedder = EmbeddingGenerator(dimension=64, chunk_size=120, chunk_overlap=20)
        self.repo = MeetingKnowledgeRepository(
            db_manager=self.db_manager,
            embedding_generator=self.embedder
        )

        # Seed sample meeting
        self.m1_id = self.db_manager.save_meeting_intelligence(
            title="Cloud Migration & DevOps Sync",
            transcript_text=(
                "Alice explained the Kubernetes migration strategy for microservices. "
                "Bob confirmed that Docker images are being pushed to AWS ECR. "
                "Charlie will configure Terraform scripts for infrastructure automation by Monday. "
                "Diana will review the SOC2 security compliance checklist."
            ),
            summary_text="Team aligned on AWS ECR image deployment, Kubernetes container migration, and Terraform automation.",
            decisions=[
                "Migrate all production microservices to Kubernetes EKS.",
                "Enforce SOC2 security auditing for cloud infrastructure."
            ],
            action_items=[
                {
                    "action": "Configure Terraform automation scripts",
                    "owner": "Charlie",
                    "deadline": "Monday",
                    "priority": "High",
                    "status": "In Progress"
                },
                {
                    "action": "Complete SOC2 compliance checklist review",
                    "owner": "Diana",
                    "deadline": "2026-10-01",
                    "priority": "Medium",
                    "status": "Pending"
                }
            ],
            participants=[
                {"name": "Alice", "canonical_name": "Alice", "role": "DevOps Lead"},
                {"name": "Bob", "canonical_name": "Bob", "role": "Cloud Architect"},
                {"name": "Charlie", "canonical_name": "Charlie", "role": "Site Reliability Engineer"},
                {"name": "Diana", "canonical_name": "Diana", "role": "Security Compliance"}
            ],
            original_filename="devops_sync.mp4",
            duration=2400.0
        )

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_single_and_batch_embedding_generation(self):
        """Test generating single and batch embedding vectors with correct dimensions and normalization."""
        text = "Kubernetes cloud architecture"
        vec = self.embedder.generate_embedding(text)
        assert isinstance(vec, list)
        assert len(vec) == 64
        # Verify L2 unit normalization (norm close to 1.0)
        norm = sum(v * v for v in vec) ** 0.5
        assert 0.99 <= norm <= 1.01

        # Batch generation
        batch = self.embedder.generate_batch_embeddings(["Docker", "Terraform", "Security"])
        assert len(batch) == 3
        assert all(len(v) == 64 for v in batch)

    def test_generate_transcript_section_embeddings(self):
        """Test transcript chunking and generating embeddings for each section."""
        transcript = (
            "Section 1: Initial introduction and sprint objectives. "
            "Section 2: Deep dive into API performance benchmarks and database indexing. "
            "Section 3: Review of customer feedback and frontend latency metrics."
        )
        sections = self.embedder.generate_transcript_section_embeddings(self.m1_id, transcript)
        assert len(sections) >= 2
        for sec in sections:
            assert sec["meeting_id"] == self.m1_id
            assert sec["entity_type"] == "transcript_section"
            assert isinstance(sec["section_index"], int)
            assert len(sec["text_content"]) > 0
            assert len(sec["embedding_vector"]) == 64

    def test_generate_summary_embedding(self):
        """Test generating embedding for executive summary."""
        summary_text = "Executive summary outlining sprint deliverables and cloud migration goals."
        sum_rec = self.embedder.generate_summary_embedding(self.m1_id, summary_text)
        assert sum_rec is not None
        assert sum_rec["meeting_id"] == self.m1_id
        assert sum_rec["entity_type"] == "summary"
        assert sum_rec["text_content"] == summary_text
        assert len(sum_rec["embedding_vector"]) == 64

    def test_generate_decisions_embeddings(self):
        """Test generating individual embeddings for each decision."""
        decisions = [
            "Adopt GraphQL for mobile client endpoints.",
            "Deprecate v1 legacy REST controllers by end of Q4."
        ]
        dec_recs = self.embedder.generate_decisions_embeddings(self.m1_id, decisions)
        assert len(dec_recs) == 2
        assert dec_recs[0]["entity_type"] == "decision"
        assert "GraphQL" in dec_recs[0]["text_content"]
        assert dec_recs[1]["entity_type"] == "decision"
        assert "Deprecate" in dec_recs[1]["text_content"]

    def test_generate_action_items_embeddings(self):
        """Test generating embeddings for action items enriched with owner, deadline, and priority."""
        actions = [
            {"action": "Deploy Redis caching layer", "owner": "Alice", "deadline": "Friday", "priority": "High", "status": "Pending"}
        ]
        act_recs = self.embedder.generate_action_items_embeddings(self.m1_id, actions)
        assert len(act_recs) == 1
        assert act_recs[0]["entity_type"] == "action_item"
        assert "Action Item: Deploy Redis caching layer" in act_recs[0]["text_content"]
        assert "Assignee: Alice" in act_recs[0]["text_content"]
        assert "Priority: High" in act_recs[0]["text_content"]

    def test_consolidate_and_save_meeting_embeddings(self):
        """Test consolidating all 4 entity types and persisting to SQLite database."""
        all_embs = self.embedder.generate_all_meeting_embeddings(
            meeting_id=self.m1_id,
            transcript_text="Alice and Bob discussed cloud infrastructure.",
            summary_text="Summary of cloud sync.",
            decisions=["Use AWS EKS."],
            action_items=[{"action": "Setup cluster", "owner": "Alice"}]
        )
        # Should have at least 1 transcript section, 1 summary, 1 decision, 1 action item
        assert len(all_embs) == 4
        saved_count = self.db_manager.save_embeddings(all_embs)
        assert saved_count == 4

        # Query back from DB
        db_embs = self.db_manager.get_embeddings_for_meeting(self.m1_id)
        assert len(db_embs) == 4
        types = {e["entity_type"] for e in db_embs}
        assert types == {"transcript_section", "summary", "decision", "action_item"}

    def test_embedding_linkage_and_integrity_verification(self):
        """
        Verify that all generated embeddings are correctly linked to their corresponding meeting
        and zero orphaned embeddings exist.
        """
        self.repo.generate_embeddings_for_meeting(self.m1_id)
        audit = self.db_manager.verify_database_integrity()

        assert audit["is_healthy"] is True
        assert audit["embedding_count"] > 0
        assert audit["orphans"]["embeddings"] == 0

    def test_semantic_vector_search_and_ranking(self):
        """Test semantic vector search matching query concept to most relevant meeting entities."""
        # Generate embeddings for meeting 1
        self.repo.generate_embeddings_for_meeting(self.m1_id)

        # Search for infrastructure automation
        results = self.repo.semantic_search("infrastructure automation scripts", top_k=5, min_score=0.1)
        assert len(results) > 0
        top_match = results[0]
        assert top_match["meeting_id"] == self.m1_id
        assert top_match["similarity_score"] > 0.3
        assert "Terraform" in top_match["text_content"] or "infrastructure" in top_match["text_content"]

    def test_cascading_deletion_of_embeddings(self):
        """Test that deleting a meeting removes all its linked embeddings."""
        self.repo.generate_embeddings_for_meeting(self.m1_id)
        assert len(self.db_manager.get_embeddings_for_meeting(self.m1_id)) > 0

        # Delete meeting
        deleted = self.db_manager.delete_meeting(self.m1_id)
        assert deleted is True

        # Verify embeddings were cascaded
        assert len(self.db_manager.get_embeddings_for_meeting(self.m1_id)) == 0
        audit = self.db_manager.verify_database_integrity()
        assert audit["embedding_count"] == 0

    def test_pipeline_dynamic_embedding_generation(self):
        """Test end-to-end pipeline automatically generates and persists embeddings upon ingestion."""
        mock_llm = MagicMock()
        mock_llm.process_transcript.return_value = {
            "summary": "Sprint alignment on API gateways.",
            "key_points": ["FastAPI architecture"],
            "decisions": ["Deploy Kong Gateway."],
            "action_items": [{"action": "Configure routes", "owner": "John", "deadline": "Friday", "priority": "High", "status": "Pending"}],
            "participants": ["John"]
        }

        pipeline = MeetingIntelligencePipeline(
            llm_service=mock_llm,
            db_manager=self.db_manager,
            embedding_generator=self.embedder
        )

        result = pipeline.process_transcript_text(
            transcript_text="John outlined the API gateway architecture with FastAPI and Kong.",
            meeting_title="API Gateway Architecture"
        )

        m_id = result["meeting_id"]
        embs = self.db_manager.get_embeddings_for_meeting(m_id)
        assert len(embs) > 0
        assert any(e["entity_type"] == "summary" for e in embs)
        assert any(e["entity_type"] == "decision" for e in embs)
        assert any(e["entity_type"] == "action_item" for e in embs)
        assert any(e["entity_type"] == "transcript_section" for e in embs)
