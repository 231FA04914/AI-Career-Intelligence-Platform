"""
Test Suite for Milestone 3: Task 3 – Vector Database Integration
Tests vector database operations:
- Insert embeddings (single & batch)
- Update embeddings
- Delete embeddings
- Similarity search
- Metadata filtering
- Meeting-to-vector mapping
- Vector-to-meeting traceability verification
"""

import sys
import shutil
import tempfile
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import DatabaseManager
from src.embeddings import EmbeddingGenerator
from src.vector_db import VectorDatabase


class TestVectorDatabaseTask3:
    """Test suite for Milestone 3 Task 3: Vector Database Integration."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_vector_db.db"
        self.db_manager = DatabaseManager(db_path=str(self.db_path))
        self.embedder = EmbeddingGenerator(dimension=32)
        self.vdb = VectorDatabase(
            db_manager=self.db_manager,
            embedding_generator=self.embedder
        )

        # Seed 2 sample meetings
        self.m1_id = self.db_manager.save_meeting_intelligence(
            title="Backend Architecture Sync",
            transcript_text="Ravi is implementing PostgreSQL partitioned tables. Priya is testing API latency.",
            summary_text="Discussion on PostgreSQL database partitioning and latency optimization.",
            decisions=["Use PostgreSQL table partitioning for event logs."],
            action_items=[
                {"id": "act_101", "action": "Implement table partitioning", "owner": "Ravi", "priority": "High", "status": "In Progress"}
            ],
            participants=[{"name": "Ravi", "canonical_name": "Ravi"}]
        )

        self.m2_id = self.db_manager.save_meeting_intelligence(
            title="Design System Review",
            transcript_text="Priya presented the dark mode color palette and button design tokens.",
            summary_text="Review of the new design tokens and dark mode UI palette.",
            decisions=["Adopt Tailwind dark mode tokens."],
            action_items=[
                {"id": "act_201", "action": "Update color variables in CSS", "owner": "Priya", "priority": "Medium", "status": "Pending"}
            ],
            participants=[{"name": "Priya", "canonical_name": "Priya"}]
        )

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_insert_single_and_batch_embeddings(self):
        """Test inserting single and batch vectors with rich metadata."""
        # 1. Single insert
        v1_id = self.vdb.insert(
            meeting_id=self.m1_id,
            entity_type="decision",
            text_content="Use PostgreSQL table partitioning for event logs.",
            metadata={"category": "database", "priority": "High"}
        )
        assert v1_id is not None

        # Retrieve inserted vector record
        v1_rec = self.db_manager.get_embedding_by_id(v1_id)
        assert v1_rec is not None
        assert v1_rec["meeting_id"] == self.m1_id
        assert v1_rec["entity_type"] == "decision"
        assert v1_rec["dimension"] == 32
        assert v1_rec["metadata"]["category"] == "database"

        # 2. Batch insert
        batch_records = [
            {
                "id": "vec_batch_1",
                "meeting_id": self.m2_id,
                "entity_type": "summary",
                "text_content": "Review of the new design tokens and dark mode UI palette.",
                "metadata": {"theme": "design"}
            },
            {
                "id": "vec_batch_2",
                "meeting_id": self.m2_id,
                "entity_type": "action_item",
                "text_content": "Update color variables in CSS",
                "metadata": {"owner": "Priya", "status": "Pending", "priority": "Medium"}
            }
        ]
        count = self.vdb.insert_batch(batch_records)
        assert count == 2

        v2_rec = self.db_manager.get_embedding_by_id("vec_batch_2")
        assert v2_rec is not None
        assert v2_rec["metadata"]["owner"] == "Priya"

    def test_update_embeddings(self):
        """Test updating vector arrays, text contents, and metadata."""
        v_id = self.vdb.insert(
            meeting_id=self.m1_id,
            entity_type="action_item",
            text_content="Initial action task",
            metadata={"status": "Pending"}
        )

        # Update text & metadata with dynamic vector recomputation
        updated = self.vdb.update(
            vector_id=v_id,
            new_text="Completed action task with new deliverables",
            new_metadata={"status": "Completed", "owner": "Ravi"},
            recompute_vector=True
        )
        assert updated is True

        # Verify updated fields
        rec = self.db_manager.get_embedding_by_id(v_id)
        assert rec["text_content"] == "Completed action task with new deliverables"
        assert rec["metadata"]["status"] == "Completed"
        assert rec["metadata"]["owner"] == "Ravi"

    def test_delete_embeddings(self):
        """Test deleting embeddings by vector ID, entity type, and meeting ID."""
        v1 = self.vdb.insert(meeting_id=self.m1_id, entity_type="decision", text_content="Dec 1")
        v2 = self.vdb.insert(meeting_id=self.m1_id, entity_type="action_item", text_content="Act 1")
        v3 = self.vdb.insert(meeting_id=self.m2_id, entity_type="summary", text_content="Sum 2")

        # 1. Delete single vector
        assert self.vdb.delete(v1) is True
        assert self.db_manager.get_embedding_by_id(v1) is None

        # 2. Delete by meeting
        deleted_count = self.vdb.delete_by_meeting(self.m2_id)
        assert deleted_count == 1
        assert self.db_manager.get_embedding_by_id(v3) is None

        # v2 should still exist
        assert self.db_manager.get_embedding_by_id(v2) is not None

    def test_similarity_search_and_score_ranking(self):
        """Test vector similarity search ranks closest vectors highest."""
        self.vdb.insert(
            meeting_id=self.m1_id,
            entity_type="decision",
            text_content="Deploy microservices to Kubernetes cluster in AWS cloud."
        )
        self.vdb.insert(
            meeting_id=self.m2_id,
            entity_type="decision",
            text_content="Use Figma design tokens for CSS component styling."
        )

        results = self.vdb.similarity_search("Kubernetes container orchestration", top_k=5)
        assert len(results) >= 1
        top_match = results[0]
        assert top_match["meeting_id"] == self.m1_id
        assert "Kubernetes" in top_match["text_content"]
        assert top_match["similarity_score"] > 0.2

    def test_similarity_search_with_metadata_filtering(self):
        """Test metadata filtering during vector similarity search."""
        self.vdb.insert(
            meeting_id=self.m1_id,
            entity_type="action_item",
            text_content="Implement database migration scripts",
            metadata={"owner": "Ravi", "status": "Pending", "priority": "High"}
        )
        self.vdb.insert(
            meeting_id=self.m1_id,
            entity_type="action_item",
            text_content="Implement UI frontend tests",
            metadata={"owner": "Priya", "status": "Completed", "priority": "Medium"}
        )
        self.vdb.insert(
            meeting_id=self.m2_id,
            entity_type="summary",
            text_content="Design tokens review summary",
            metadata={"owner": "Priya"}
        )

        # Filter 1: By entity_type
        dec_results = self.vdb.similarity_search("database UI", filters={"entity_type": "action_item"})
        assert all(r["entity_type"] == "action_item" for r in dec_results)

        # Filter 2: By owner in metadata
        ravi_results = self.vdb.similarity_search("database", filters={"owner": "Ravi"})
        assert len(ravi_results) == 1
        assert "database migration" in ravi_results[0]["text_content"]

        # Filter 3: By status in metadata
        pending_results = self.vdb.similarity_search("implement", filters={"status": "Pending"})
        assert len(pending_results) == 1
        assert pending_results[0]["metadata"]["status"] == "Pending"

        # Filter 4: By meeting_id
        m2_results = self.vdb.similarity_search("review", filters={"meeting_id": self.m2_id})
        assert all(r["meeting_id"] == self.m2_id for r in m2_results)

    def test_meeting_to_vector_mapping(self):
        """Test meeting-to-vector mapping retrieves all vectors for a specific meeting."""
        self.vdb.insert(meeting_id=self.m1_id, entity_type="summary", text_content="Summary 1")
        self.vdb.insert(meeting_id=self.m1_id, entity_type="decision", text_content="Decision 1")
        self.vdb.insert(meeting_id=self.m2_id, entity_type="summary", text_content="Summary 2")

        m1_vectors = self.vdb.get_vectors_for_meeting(self.m1_id)
        assert len(m1_vectors) == 2
        assert all(v["meeting_id"] == self.m1_id for v in m1_vectors)

        m2_vectors = self.vdb.get_vectors_for_meeting(self.m2_id)
        assert len(m2_vectors) == 1
        assert m2_vectors[0]["meeting_id"] == self.m2_id

    def test_trace_vector_to_meeting(self):
        """Test reverse traceability from any vector ID back to its parent meeting session."""
        v_id = self.vdb.insert(
            meeting_id=self.m1_id,
            entity_type="action_item",
            text_content="Implement table partitioning",
            metadata={"owner": "Ravi"}
        )

        trace = self.vdb.trace_vector_to_meeting(v_id)
        assert trace is not None
        assert trace["vector_id"] == v_id
        assert trace["meeting_id"] == self.m1_id
        assert trace["meeting_title"] == "Backend Architecture Sync"
        assert trace["is_orphaned"] is False
        assert trace["full_meeting"]["id"] == self.m1_id
        assert len(trace["full_meeting"]["action_items"]) == 1

    def test_verify_traceability_audit(self):
        """
        Verify that every stored vector can be traced back to the correct meeting
        (Explicit Milestone 3 Task 3 Requirement).
        """
        self.vdb.insert(meeting_id=self.m1_id, entity_type="summary", text_content="Sum 1")
        self.vdb.insert(meeting_id=self.m1_id, entity_type="decision", text_content="Dec 1")
        self.vdb.insert(meeting_id=self.m2_id, entity_type="action_item", text_content="Act 2")

        audit = self.vdb.verify_traceability()
        assert audit["is_valid"] is True
        assert audit["total_vectors"] == 3
        assert audit["validly_traced_vectors"] == 3
        assert audit["orphan_count"] == 0
        assert audit["total_meetings_indexed"] == 2
        assert self.m1_id in audit["meeting_mappings"]
        assert self.m2_id in audit["meeting_mappings"]

    def test_cascading_meeting_deletion_cleans_vectors(self):
        """Test deleting a meeting removes all its vectors from the vector database."""
        v_id = self.vdb.insert(meeting_id=self.m1_id, entity_type="summary", text_content="Summary 1")
        assert self.db_manager.get_embedding_by_id(v_id) is not None

        # Delete meeting
        self.db_manager.delete_meeting(self.m1_id)

        # Vector should be deleted
        assert self.db_manager.get_embedding_by_id(v_id) is None
        audit = self.vdb.verify_traceability()
        assert audit["total_vectors"] == 0
