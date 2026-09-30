"""
Complete End-to-End Workflow Testing (Milestone 4 - Task 8)
Flow:
User Login -> Upload/Import Meeting -> Audio/Transcript Validation -> Whisper Transcription
-> Transcript Storage -> LLM Summary -> Action Item Extraction -> Participant Assignment
-> Knowledge Repository -> Embeddings -> Vector Database -> RAG Search -> FastAPI -> Streamlit Data -> Reports (PDF/CSV).
"""

import pytest
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient

from src.api import app, ServiceContainer
from src.database import DatabaseManager
from src.auth import AuthManager
from src.embeddings import EmbeddingGenerator
from src.vector_db import VectorDatabase
from src.pipeline import MeetingIntelligencePipeline
from src.reports.exporter import generate_meeting_pdf, generate_meeting_csv


@pytest.fixture
def e2e_environment():
    """Setup isolated end-to-end database, vector store, and test client."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    db = DatabaseManager(db_path=db_path)
    embedder = EmbeddingGenerator()
    vdb = VectorDatabase(db_manager=db, embedding_generator=embedder)
    auth = AuthManager(db_manager=db)
    pipeline = MeetingIntelligencePipeline(llm_service=None, db_manager=db, embedding_generator=embedder)

    # Set container singletons for FastAPI client
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


def test_complete_end_to_end_workflow(e2e_environment):
    """
    Execute full unassisted end-to-end pipeline:
    Auth -> Ingestion -> LLM intelligence -> Vector indexing -> RAG query -> Report Export.
    """
    client = e2e_environment["client"]
    db = e2e_environment["db"]
    pipeline = e2e_environment["pipeline"]
    auth = e2e_environment["auth"]

    # 1. User Registration & Login
    reg_res = client.post("/auth/register", json={
        "username": "executive_user",
        "email": "exec@company.com",
        "password": "ExecPassword2026!",
        "role": "user"
    })
    assert reg_res.status_code == 200
    user_data = reg_res.json()
    token = user_data["token"]
    user_id = user_data["id"]

    headers = {"Authorization": f"Bearer {token}"}

    # 2. Ingest Meeting Transcript through Pipeline
    transcript_text = (
        "Project Lead (Marcus): Welcome team to our milestone 4 alignment review. "
        "We need to ensure our FastAPI and Streamlit dashboard integration is rock solid. "
        "Lead Architect (Elena): I have completed the database isolation and vector embedding generation. "
        "I will deliver the load testing report by Friday at 5 PM. "
        "Marcus: Approved. Decision made: we are releasing the platform to production this month. "
        "Ravi, please finalize the PDF and CSV report exporter by Wednesday."
    )

    ingest_result = pipeline.process_transcript_text(
        transcript_text=transcript_text,
        meeting_title="Milestone 4 Executive Review",
        original_filename="milestone4_review.txt",
        duration=180.0,
        user_id=user_id
    )

    meeting_id = ingest_result["meeting_id"]
    assert meeting_id is not None
    assert ingest_result["database_persisted"] is True

    # 3. Verify Database Persistence & Linkages
    meeting = db.get_meeting(meeting_id, user_id=user_id)
    assert meeting is not None
    assert meeting["title"] == "Milestone 4 Executive Review"
    assert len(meeting["action_items"]) >= 1
    assert len(meeting["participants"]) >= 1

    # 4. Verify Vector Database Indexing
    vectors = e2e_environment["vdb"].get_vectors_for_meeting(meeting_id)
    assert len(vectors) >= 1

    # 5. Execute RAG Question Answering via API
    ask_res = client.post("/ask", json={
        "question": "What did Marcus decide regarding the release?",
        "meeting_id": meeting_id
    }, headers=headers)

    assert ask_res.status_code == 200
    ask_data = ask_res.json()
    assert ask_data["answer"] is not None
    assert len(ask_data["citations"]) >= 1
    assert ask_data["citations"][0]["meeting_id"] == meeting_id

    # 6. Execute Semantic Search via API
    search_res = client.post("/search", json={
        "query": "FastAPI Streamlit dashboard integration and reports"
    }, headers=headers)

    assert search_res.status_code == 200
    search_data = search_res.json()
    assert search_data["sla_met"] is True
    assert search_data["total_meetings_found"] >= 1
    assert search_data["relevant_meetings"][0]["meeting_id"] == meeting_id

    # 7. Fetch Meeting Analytics via API
    analytics_res = client.get(f"/meetings/{meeting_id}/analytics", headers=headers)
    assert analytics_res.status_code == 200
    analytics_data = analytics_res.json()
    assert analytics_data["meeting_id"] == meeting_id
    assert "priority_distribution" in analytics_data

    # 8. Generate & Export PDF and CSV Reports via API
    pdf_res = client.get(f"/meetings/{meeting_id}/export?format=pdf", headers=headers)
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert len(pdf_res.content) > 500

    csv_res = client.get(f"/meetings/{meeting_id}/export?format=csv", headers=headers)
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    assert "Milestone 4 Executive Review" in csv_res.text
