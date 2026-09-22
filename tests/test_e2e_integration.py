"""
Test Suite for Task 9: End-to-End Integration Testing
Validates complete automated lifecycle:
1. Ingestion: Process transcript via MeetingIntelligencePipeline
2. Persistence: Store in SQLite database and Vector Database
3. API Access: Authenticate and query /meetings, /meetings/{id}, /search, /ask
4. Verification: Verify data integrity, traceability, and citations without manual intervention.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock
from fastapi.testclient import TestClient

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline import MeetingIntelligencePipeline
from src.database import DatabaseManager
from src.embeddings import EmbeddingGenerator
from src.vector_db import VectorDatabase
from src.repository import MeetingKnowledgeRepository
from src.semantic_search import SemanticSearchEngine
from src.api import app, ServiceContainer


class TestEndToEndIntegrationTask9:
    """Test suite for Task 9 Complete End-to-End Integration Workflow."""

    def setup_method(self):
        os.environ["LOCAL_EMBEDDINGS"] = "1"
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_e2e.db"
        self.db = DatabaseManager(db_path=str(self.db_path))
        self.embedder = EmbeddingGenerator(api_key="")
        self.vdb = VectorDatabase(db_manager=self.db, embedding_generator=self.embedder)

        # Mock LLM for deterministic pipeline execution
        self.mock_llm = Mock()
        self.mock_llm.api_key = None
        self.mock_llm.process_transcript.return_value = {
            "summary": "Engineering sync on cloud migration and mobile app performance optimization.",
            "decisions": [
                "Deploy backend microservices to AWS EKS",
                "Enable Redis caching for mobile feed API"
            ],
            "action_items": [
                {"action": "Deploy microservices to EKS", "owner": "Ravi", "deadline": "Friday", "priority": "High", "status": "Pending"},
                {"action": "Implement Redis cache layer", "owner": "Priya", "deadline": "Monday", "priority": "Medium", "status": "In Progress"}
            ],
            "participants": ["Ravi", "Priya"],
            "key_points": ["EKS microservices deployment", "Redis cache layer optimization"],
            "deadlines": ["Friday", "Monday"],
            "priorities": [{"item": "Deploy microservices", "priority": "High"}]
        }
        self.mock_llm._call_llm_with_retry.return_value = (
            "Based on Meeting records, Ravi is scheduled to deploy microservices to EKS by Friday, and Priya is implementing the Redis cache layer by Monday."
        )
        self.mock_llm.generate.return_value = (
            "Based on Meeting records, Ravi is scheduled to deploy microservices to EKS by Friday, and Priya is implementing the Redis cache layer by Monday."
        )

        self.mock_audio = Mock()
        self.mock_transcriber = Mock()

        self.pipeline = MeetingIntelligencePipeline(
            audio_processor=self.mock_audio,
            transcriber=self.mock_transcriber,
            llm_service=self.mock_llm,
            db_manager=self.db,
            embedding_generator=self.embedder
        )

        # Inject dependencies into API ServiceContainer
        ServiceContainer._db = self.db
        ServiceContainer._embedder = self.embedder
        ServiceContainer._vector_db = self.vdb
        ServiceContainer._llm = self.mock_llm
        ServiceContainer._repo = MeetingKnowledgeRepository(
            db_manager=self.db,
            llm_service=self.mock_llm,
            embedding_generator=self.embedder,
            vector_db=self.vdb
        )
        ServiceContainer._search_engine = SemanticSearchEngine(
            db_manager=self.db,
            embedding_generator=self.embedder,
            vector_db=self.vdb,
            llm_service=self.mock_llm
        )

        self.client = TestClient(app)
        self.auth_headers = {"X-API-Key": "career-intel-dev-key-2026"}

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        ServiceContainer._db = None
        ServiceContainer._embedder = None
        ServiceContainer._vector_db = None
        ServiceContainer._llm = None
        ServiceContainer._repo = None
        ServiceContainer._search_engine = None

    def test_complete_e2e_workflow(self):
        """
        Execute full end-to-end integration:
        Pipeline Ingestion -> DB Save -> Embedding Storage -> API Querying (/meetings, /search, /ask).
        """
        # Step 1: Ingest transcript through MeetingIntelligencePipeline
        transcript_text = (
            "Ravi agreed to deploy microservices to AWS EKS by Friday. "
            "Priya will implement the Redis cache layer for the mobile feed API by Monday. "
            "We decided to proceed with both initiatives immediately."
        )
        pipeline_result = self.pipeline.process_transcript_text(
            transcript_text=transcript_text,
            meeting_title="Q4 Cloud & Caching Architecture Review",
            original_filename="q4_architecture_sync.mp4",
            duration=210.0
        )
        assert pipeline_result["database_persisted"] is True
        meeting_id = pipeline_result["meeting_id"]
        assert meeting_id is not None

        # Step 2: Store vector embeddings for new meeting
        emb_records = self.embedder.generate_all_meeting_embeddings(
            meeting_id=meeting_id,
            transcript_text=transcript_text,
            summary_text=pipeline_result["summary"],
            decisions=pipeline_result["decisions"],
            action_items=pipeline_result["action_items"]
        )
        inserted_vectors = self.vdb.insert_batch(emb_records)
        assert inserted_vectors >= 4

        # Step 3: Verify Meeting via API GET /meetings
        res_list = self.client.get("/meetings", headers=self.auth_headers)
        assert res_list.status_code == 200
        list_data = res_list.json()
        assert list_data["total"] == 1
        assert list_data["meetings"][0]["id"] == meeting_id
        assert list_data["meetings"][0]["title"] == "Q4 Cloud & Caching Architecture Review"
        assert list_data["meetings"][0]["has_vectors"] is True

        # Step 4: Verify Meeting Details via API GET /meetings/{id}
        res_detail = self.client.get(f"/meetings/{meeting_id}", headers=self.auth_headers)
        assert res_detail.status_code == 200
        detail_data = res_detail.json()
        assert detail_data["id"] == meeting_id
        assert len(detail_data["key_decisions"]) == 2
        assert len(detail_data["action_items"]) == 2
        assert len(detail_data["participants"]) == 2
        assert detail_data["vector_count"] >= 4

        # Step 5: Execute Semantic Search via API POST /search
        search_payload = {
            "query": "Redis caching and mobile performance deliverables",
            "top_k": 3,
            "min_score": 0.1
        }
        res_search = self.client.post("/search", json=search_payload, headers=self.auth_headers)
        assert res_search.status_code == 200
        search_data = res_search.json()
        assert search_data["total_meetings_found"] >= 1
        assert search_data["sla_met"] is True
        assert search_data["relevant_meetings"][0]["meeting_id"] == meeting_id

        # Step 6: Perform Grounded RAG Question Answering via API POST /ask
        ask_payload = {
            "question": "What is Priya assigned to do and when is the deadline?",
            "max_context_meetings": 3
        }
        res_ask = self.client.post("/ask", json=ask_payload, headers=self.auth_headers)
        assert res_ask.status_code == 200
        ask_data = res_ask.json()
        assert ask_data["grounded"] is True
        assert len(ask_data["citations"]) >= 1
        assert meeting_id in ask_data["source_meeting_ids"]
        assert "Priya" in ask_data["answer"]
        assert "Redis" in ask_data["answer"] or "Monday" in ask_data["answer"]
