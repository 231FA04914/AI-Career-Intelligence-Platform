"""
Test Suite for Task 6: Existing API Integration
Tests FastAPI endpoints:
- GET  /health
- GET  /meetings
- GET  /meetings/{id}
- POST /search
- POST /ask
- Authentication (Header, Bearer token, Invalid/Missing token)
- Error Handling & Input Validation
"""

import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api import app, ServiceContainer
from src.database import DatabaseManager
from src.embeddings import EmbeddingGenerator
from src.vector_db import VectorDatabase
from src.repository import MeetingKnowledgeRepository
from src.semantic_search import SemanticSearchEngine


class TestApiIntegrationTask6:
    """Test suite for Task 6 REST API endpoints and Authentication."""

    def setup_method(self):
        import os
        os.environ["LOCAL_EMBEDDINGS"] = "1"
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_api.db"
        self.db = DatabaseManager(db_path=str(self.db_path))
        self.embedder = EmbeddingGenerator(api_key="")
        self.vdb = VectorDatabase(db_manager=self.db, embedding_generator=self.embedder)

        # Seed test meeting
        self.meeting_id = self.db.save_meeting_intelligence(
            title="Q3 Strategy & Cloud Architecture",
            transcript_text="Ravi will deliver the Kubernetes migration by Friday. Priya is coordinating with AWS team.",
            summary_text="Team reviewed Q3 architecture and scheduled Kubernetes rollout for Friday.",
            decisions=["Adopt Kubernetes on AWS for Q3 deployment"],
            action_items=[
                {"action": "Complete Kubernetes migration", "owner": "Ravi", "deadline": "Friday", "priority": "High", "status": "Pending"},
                {"action": "Coordinate with AWS support", "owner": "Priya", "deadline": "Monday", "priority": "Medium", "status": "In Progress"}
            ],
            participants=[
                {"name": "Ravi", "role": "DevOps Engineer", "action_items_count": 1},
                {"name": "Priya", "role": "Cloud Architect", "action_items_count": 1}
            ],
            original_filename="q3_cloud_sync.mp4",
            duration=120.0
        )

        # Generate vectors for meeting
        records = self.embedder.generate_all_meeting_embeddings(
            meeting_id=self.meeting_id,
            transcript_text="Ravi will deliver the Kubernetes migration by Friday. Priya is coordinating with AWS team.",
            summary_text="Team reviewed Q3 architecture and scheduled Kubernetes rollout for Friday.",
            decisions=["Adopt Kubernetes on AWS for Q3 deployment"],
            action_items=[{"action": "Complete Kubernetes migration", "owner": "Ravi", "deadline": "Friday", "priority": "High", "status": "Pending"}]
        )
        self.vdb.insert_batch(records)

        self.mock_llm = Mock()
        self.mock_llm.api_key = None
        self.mock_llm._call_llm_with_retry.return_value = "Ravi is assigned to complete the Kubernetes migration by Friday as per Meeting."

        # Inject test dependencies into ServiceContainer
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
        self.valid_headers = {"X-API-Key": "career-intel-dev-key-2026"}

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        # Reset container
        ServiceContainer._db = None
        ServiceContainer._embedder = None
        ServiceContainer._vector_db = None
        ServiceContainer._llm = None
        ServiceContainer._repo = None
        ServiceContainer._search_engine = None

    def test_health_endpoint(self):
        """Test GET /health returns 200 without authentication."""
        resp = self.client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert data["persisted_meetings"] >= 1
        assert data["stored_vectors"] >= 1

    def test_authentication_enforcement(self):
        """Test API endpoints enforce authentication correctly."""
        # 1. Missing auth
        resp = self.client.get("/meetings")
        assert resp.status_code == 401
        assert "Missing authentication" in resp.json()["detail"]

        # 2. Invalid auth key
        resp = self.client.get("/meetings", headers={"X-API-Key": "invalid-secret-key-xyz"})
        assert resp.status_code == 401
        assert "Invalid API key" in resp.json()["detail"]

        # 3. Valid Header key
        resp = self.client.get("/meetings", headers=self.valid_headers)
        assert resp.status_code == 200

        # 4. Valid Bearer token
        bearer_headers = {"Authorization": "Bearer career-intel-dev-key-2026"}
        resp = self.client.get("/meetings", headers=bearer_headers)
        assert resp.status_code == 200

    def test_get_meetings_list_and_filters(self):
        """Test GET /meetings with pagination and query filters."""
        resp = self.client.get("/meetings", headers=self.valid_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert len(data["meetings"]) >= 1
        assert data["meetings"][0]["id"] == self.meeting_id
        assert data["meetings"][0]["title"] == "Q3 Strategy & Cloud Architecture"
        assert data["meetings"][0]["action_items_count"] == 2

        # Filter by search keyword
        resp_search = self.client.get("/meetings?search=Kubernetes", headers=self.valid_headers)
        assert resp_search.status_code == 200

        resp_nomatch = self.client.get("/meetings?search=NonExistentSubject999", headers=self.valid_headers)
        assert resp_nomatch.status_code == 200
        assert resp_nomatch.json()["total"] == 0

    def test_get_meeting_details(self):
        """Test GET /meetings/{id} retrieves complete meeting intelligence."""
        resp = self.client.get(f"/meetings/{self.meeting_id}", headers=self.valid_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == self.meeting_id
        assert data["title"] == "Q3 Strategy & Cloud Architecture"
        assert "Kubernetes migration" in data["transcript"]
        assert len(data["action_items"]) == 2
        assert len(data["participants"]) == 2
        assert data["vector_count"] >= 1

    def test_get_meeting_not_found(self):
        """Test GET /meetings/{id} returns 404 for invalid ID."""
        resp = self.client.get("/meetings/non_existent_id_404", headers=self.valid_headers)
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    def test_post_search_endpoint(self):
        """Test POST /search returns semantic search result with latency & SLA."""
        payload = {
            "query": "Kubernetes cloud migration deadline",
            "top_k": 3,
            "min_score": 0.0
        }
        resp = self.client.post("/search", json=payload, headers=self.valid_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["query"] == "Kubernetes cloud migration deadline"
        assert data["latency_ms"] < 3000.0
        assert data["sla_met"] is True
        assert len(data["relevant_meetings"]) >= 1
        assert data["relevant_meetings"][0]["meeting_id"] == self.meeting_id

    def test_post_ask_rag_endpoint(self):
        """Test POST /ask returns grounded answer with citations."""
        payload = {
            "question": "What is Ravi assigned to do by Friday?",
            "max_context_meetings": 3
        }
        resp = self.client.post("/ask", json=payload, headers=self.valid_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["question"] == "What is Ravi assigned to do by Friday?"
        assert data["grounded"] is True
        assert len(data["citations"]) >= 1
        assert self.meeting_id in data["source_meeting_ids"]
        assert "Ravi" in data["answer"]

    def test_input_validation_errors(self):
        """Test empty queries return 400 Bad Request."""
        resp = self.client.post("/search", json={"query": "   "}, headers=self.valid_headers)
        assert resp.status_code == 400

        resp_ask = self.client.post("/ask", json={"question": ""}, headers=self.valid_headers)
        assert resp_ask.status_code == 400
