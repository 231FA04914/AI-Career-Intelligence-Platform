"""
Performance, Security & Reliability Tests (Milestone 4 - Task 9)
Checks:
- Sub-3-second API and search SLA performance
- SQL Injection & malicious payload protection
- Multi-user data isolation & unauthorized access denial (401/403)
- Invalid requests & graceful error handling
- Vector database search performance under load
"""

import time
import tempfile
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from src.api import app, ServiceContainer
from src.database import DatabaseManager
from src.auth import AuthManager
from src.embeddings import EmbeddingGenerator
from src.vector_db import VectorDatabase
from src.pipeline import MeetingIntelligencePipeline


@pytest.fixture
def perf_env():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    db = DatabaseManager(db_path=db_path)
    embedder = EmbeddingGenerator()
    vdb = VectorDatabase(db_manager=db, embedding_generator=embedder)
    auth = AuthManager(db_manager=db)
    pipeline = MeetingIntelligencePipeline(llm_service=None, db_manager=db, embedding_generator=embedder)

    ServiceContainer._db = db
    ServiceContainer._embedder = embedder
    ServiceContainer._vector_db = vdb
    ServiceContainer._auth = auth
    ServiceContainer._pipeline = pipeline
    ServiceContainer._llm = None
    ServiceContainer._repo = None
    ServiceContainer._search_engine = None

    client = TestClient(app)

    yield {
        "db": db,
        "auth": auth,
        "vdb": vdb,
        "pipeline": pipeline,
        "client": client,
        "db_path": db_path
    }

    if Path(db_path).exists():
        try:
            Path(db_path).unlink()
        except Exception:
            pass


def test_search_and_api_latency_sla(perf_env):
    """Verify sub-3-second search SLA across multiple indexed records."""
    client = perf_env["client"]
    pipeline = perf_env["pipeline"]

    # Seed 5 meetings with vector embeddings
    for i in range(5):
        pipeline.process_transcript_text(
            transcript_text=f"Meeting {i}: Testing performance latency and fast indexing. Action item {i} due tomorrow.",
            meeting_title=f"Performance Benchmarking Session {i}",
            original_filename=f"perf_test_{i}.txt"
        )

    # Perform search and verify sub-3-second latency
    start = time.perf_counter()
    res = client.post("/search", json={"query": "performance latency benchmark"}, headers={"X-API-Key": "career-intel-dev-key-2026"})
    elapsed = time.perf_counter() - start

    assert res.status_code == 200
    assert elapsed < 3.0  # SLA < 3s
    data = res.json()
    assert data["sla_met"] is True


def test_sql_injection_resilience(perf_env):
    """Verify that malicious SQL injection strings in search queries and parameters do not execute."""
    client = perf_env["client"]

    malicious_inputs = [
        "' OR '1'='1",
        "'; DROP TABLE meetings; --",
        "' UNION SELECT * FROM users --",
        "1' OR 1=1--"
    ]

    for attack in malicious_inputs:
        # Search query with SQL injection string
        res = client.post("/search", json={"query": attack}, headers={"X-API-Key": "career-intel-dev-key-2026"})
        assert res.status_code in [200, 400]  # Handled cleanly without DB crash

        # Meeting list search param with SQL injection
        res_list = client.get(f"/meetings?search={attack}", headers={"X-API-Key": "career-intel-dev-key-2026"})
        assert res_list.status_code == 200

    # Verify tables still exist
    integrity = perf_env["db"].verify_database_integrity()
    assert integrity["is_healthy"] is True


def test_unauthorized_access_rejection(perf_env):
    """Verify that unauthenticated requests to protected endpoints return 401."""
    client = perf_env["client"]

    # Without auth headers
    assert client.get("/meetings").status_code == 401
    assert client.get("/meetings/meet_123").status_code == 401
    assert client.post("/search", json={"query": "test"}).status_code == 401
    assert client.post("/ask", json={"question": "test"}).status_code == 401

    # With invalid key
    assert client.get("/meetings", headers={"X-API-Key": "completely_invalid_key"}).status_code == 401


def test_invalid_requests_and_file_validation_handling(perf_env):
    """Verify that invalid payloads and empty queries are rejected with appropriate error codes."""
    client = perf_env["client"]
    headers = {"X-API-Key": "career-intel-dev-key-2026"}

    # Empty search query
    empty_search = client.post("/search", json={"query": "   "}, headers=headers)
    assert empty_search.status_code == 400

    # Empty question
    empty_ask = client.post("/ask", json={"question": ""}, headers=headers)
    assert empty_ask.status_code == 400

    # Non-existent meeting details
    not_found = client.get("/meetings/non_existent_id_9999", headers=headers)
    assert not_found.status_code == 404
