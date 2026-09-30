# 📘 AI Career Intelligence Platform — Complete Master Documentation (Milestones 1 – 4)

---

## Executive Summary

The **AI Career Intelligence Platform** is an enterprise-grade AI SaaS application designed to transform spoken conversations, meeting recordings, and interview sessions into structured, searchable, and actionable business intelligence. 

The platform provides an end-to-end automated lifecycle:
1. **Ingestion & Transcription**: Audio/video media validation and high-accuracy Whisper speech-to-text processing.
2. **LLM Extraction & Intelligence**: Executive summaries, key strategic decisions, prioritized action items, and participant responsibility mapping powered by Google Gemini with graceful heuristic fallbacks.
3. **Relational & Vector Knowledge Repository**: Multi-tenant SQLite database persistence coupled with dense vector embeddings and sub-3-second cosine similarity semantic search.
4. **Grounded RAG (Retrieval-Augmented Generation)**: Natural-language question answering with explicit source citations and groundness verification.
5. **Ecosystem Integrations**: Automated Zoom Cloud Recordings & Google Meet / Drive ingestion with duplicate detection and real-time webhook listeners.
6. **Executive Reporting**: One-click PDF generation (ReportLab) and structured CSV exports.
7. **Security & Multi-Tenancy**: PBKDF2-HMAC-SHA256 password hashing, anti-tamper signed session tokens, and strict tenant data isolation.

---

## 🗺️ High-Level System Architecture

```
+-----------------------------------------------------------------------------------+
|                              1. INGESTION LAYER                                   |
|   - Audio / Video Upload (.mp3, .mp4, .wav, .m4a)                                 |
|   - Zoom Cloud Recording API / Webhook (recording.completed)                      |
|   - Google Meet / Drive Ingestion API                                             |
|   - Direct Transcript Text Input                                                  |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------+-----------------------------------------+
|                       2. SPEECH & VALIDATION PIPELINE                             |
|   - FileValidator: Format verification, MIME check, max size (500MB)              |
|   - AudioProcessor: FFmpeg conversion to 16kHz Mono WAV                           |
|   - Transcriber: OpenAI Whisper / Faster-Whisper transcription                    |
|   - TranscriptValidator: Word count check & speech quality assurance              |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------+-----------------------------------------+
|                        3. AI INTELLIGENCE EXTRACTION                              |
|   - LLMService: Google Gemini with exponential backoff & ceiling retries          |
|   - MeetingSummarizer: Synthesizes executive summaries & decisions                |
|   - ActionItemExtractor: Extracts tasks, assignees, deadlines, priorities         |
|   - ParticipantMapper: Resolves aliases to canonical identities & roles           |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------+-----------------------------------------+
|                    4. RELATIONAL & VECTOR PERSISTENCE                             |
|   - DatabaseManager: SQLite relational persistence with foreign keys              |
|   - EmbeddingGenerator: Dense vector embeddings for all meeting entities          |
|   - VectorDatabase: Cosine similarity vector search with metadata filters         |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------+-----------------------------------------+
|                         5. RAG & SEMANTIC SEARCH                                  |
|   - SemanticSearchEngine: Multi-entity search with sub-3s latency SLA             |
|   - MeetingKnowledgeRepository: Grounded RAG Q&A with citations                   |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------+-----------------------------------------+
|                       6. PRESENTATION & DELIVERY                                  |
|   - FastAPI REST Gateway: 17+ endpoints with OpenAPI interactive docs             |
|   - Streamlit Executive UI: Responsive SaaS dashboard with theme tokens           |
|   - ReportLab Exporter: PDF & CSV export generation                               |
+-----------------------------------------------------------------------------------+
```

---

## 📦 Project Structure & File Index

```
AI-Career-Intelligence-Platform/
├── app.py                                # Streamlit UI application & view router
├── run_app.py                            # Unified production supervisor (FastAPI + Streamlit)
├── Dockerfile                            # Multi-stage production container build
├── docker-compose.yml                    # Container orchestration (API + Dashboard services)
├── requirements.txt                      # Python dependencies (ReportLab, FastAPI, Streamlit, etc.)
├── .env.example                          # Environment variable configuration template
├── .dockerignore                         # Docker build exclusion rules
├── PROJECT_DOCUMENTATION.md              # Complete project technical documentation
│
├── src/                                  # Core source code modules
│   ├── __init__.py                       # Package initializer
│   ├── auth.py                           # PBKDF2 hashing, signed session tokens & tenant security
│   ├── api.py                            # FastAPI REST API layer & OpenAPI schema documentation
│   ├── database.py                       # SQLite relational schema manager & user CRUD
│   ├── audio_processor.py                # FFmpeg audio conversion & duration calculation
│   ├── transcriber.py                    # OpenAI Whisper / Faster-Whisper transcription engine
│   ├── validator.py                      # Media file and transcript validation rules
│   ├── transcript_manager.py             # JSON transcript persistence & filesystem archive
│   ├── summary_manager.py                # JSON intelligence summary storage manager
│   ├── embeddings.py                     # Dense vector embedding generator
│   ├── vector_db.py                      # In-memory / persisted vector similarity store
│   ├── repository.py                     # MeetingKnowledgeRepository & RAG coordinator
│   ├── semantic_search.py                # Sub-3s multi-entity semantic search engine
│   ├── pipeline.py                       # MeetingIntelligencePipeline end-to-end coordinator
│   │
│   ├── llm/                              # LLM abstraction layer
│   │   ├── __init__.py                   # LLM module entry point
│   │   ├── service.py                    # Google Gemini client with exponential backoff retries
│   │   ├── prompts.py                    # Structured prompt templates
│   │   ├── validators.py                 # Input/Output validation & JSON sanitization
│   │   ├── schemas.py                    # Pydantic data schemas for LLM responses
│   │   └── exceptions.py                 # Custom exception hierarchy
│   │
│   ├── summarizer.py                     # Meeting summarizer & key decision extractor
│   ├── action_item_extractor.py          # Action item, deadline, and priority extractor
│   ├── participant_mapper.py             # Participant normalization & accountability mapper
│   │
│   ├── integrations/                     # Cloud platform integrations (Milestone 4)
│   │   ├── __init__.py                   # Integrations package exports
│   │   ├── zoom.py                       # Zoom OAuth, cloud recording browser, webhooks & ingestion
│   │   └── google_meet.py                # Google Meet / Drive recording ingestion & webhooks
│   │
│   ├── reports/                          # Document report exports (Milestone 4)
│   │   ├── __init__.py                   # Reports package exports
│   │   └── exporter.py                   # ReportLab PDF executive exporter & structured CSV exporter
│   │
│   └── ui/                               # Streamlit UI design system
│       ├── __init__.py                   # UI package initializer
│       ├── theme.py                      # CSS design tokens, typography & component styling
│       ├── components.py                 # Reusable KPI cards, badges, hero banners, headers
│       └── views/                        # Modular Streamlit views
│           ├── dashboard.py              # Main executive dashboard (Task 1)
│           ├── meeting_details.py        # Meeting details & analytics flow (Task 2)
│           ├── integrations_view.py      # Zoom & Google Meet ingestion manager (Tasks 4 & 5)
│           ├── auth_modal.py             # User authentication dialog & account switcher (Task 7)
│           ├── interview_analysis.py     # Live audio recording & transcript analysis
│           ├── transcript_view.py        # Dedicated transcript inspector & quality checks
│           ├── ai_insights.py            # LLM intelligence inspector
│           ├── knowledge_repository.py   # Vector repository browser & multi-entity search
│           ├── career_intelligence.py    # Career growth analytics & skill graphs
│           ├── interview_prep.py         # AI interview simulation & prep tool
│           ├── database_archive.py       # Cross-meeting relational record manager
│           └── settings_view.py          # System diagnostics, LLM health & configuration
│
├── tests/                                # 169 Automated Pytest Test Suite
│   ├── test_action_items.py              # Action item extraction & priority tests
│   ├── test_api.py                       # FastAPI REST API endpoints tests
│   ├── test_auth_security.py             # User authentication & multi-tenant isolation tests
│   ├── test_database.py                  # Database relational persistence & integrity tests
│   ├── test_e2e_integration.py           # Pipeline integration tests
│   ├── test_embeddings.py                # Dense vector embedding generator tests
│   ├── test_integrations.py              # Zoom & Google Meet cloud ingestion tests
│   ├── test_knowledge_repository.py      # Knowledge repository & bidirectional tracer tests
│   ├── test_llm_service.py               # Gemini LLM retry, ceiling, and fallback tests
│   ├── test_milestone4_e2e.py            # Complete Milestone 4 end-to-end test
│   ├── test_milestone4_performance_security.py # Sub-3s SLA, SQL injection, & security tests
│   ├── test_participant_mapping.py       # Participant mapping & canonical alias tests
│   ├── test_performance_edge_cases.py   # Large transcripts & stress tests
│   ├── test_pipeline.py                  # Pipeline execution stages tests
│   ├── test_reports_export.py            # PDF and CSV report export tests
│   ├── test_search_rag_validation.py     # RAG citation & question answering tests
│   ├── test_semantic_search.py           # Semantic search engine tests
│   ├── test_summarizer.py                # Meeting summarization tests
│   ├── test_transcript_validation.py     # Transcript validation tests
│   ├── test_transcription.py             # Whisper speech-to-text tests
│   ├── test_upload.py                    # File upload & MIME validation tests
│   ├── test_validation.py                # Input validation tests
│   └── test_vector_db.py                 # Vector similarity search & metadata filter tests
│
└── data/                                 # Persistent application storage
    ├── audio/                            # Stored audio files
    ├── transcripts/                      # JSON transcripts archive
    ├── summaries/                        # JSON intelligence summaries archive
    └── meeting_intelligence.db           # Relational SQLite database
```

---

## 🏛️ Milestone-by-Milestone Technical Breakdown

---

### 🎙️ Milestone 1 — Audio Processing, Whisper Transcription & Validation

#### Objective
Establish a rock-solid media processing foundation capable of accepting various audio/video containers, validating formatting, extracting clean audio, and performing accurate automated speech-to-text transcription with OpenAI Whisper.

#### Core Modules
1. **`src/audio_processor.py` (`AudioProcessor`)**:
   - Uses `ffmpeg-python` to extract audio streams from video containers (`.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`).
   - Converts audio to standard speech-recognition audio: **16,000 Hz, 16-bit Mono WAV**.
   - Calculates precise audio duration in seconds.
   - Manages temporary file lifecycle and cleanup.

2. **`src/transcriber.py` (`Transcriber`)**:
   - Interfaces with `openai-whisper` and `faster-whisper`.
   - Supports configurable model sizes (`tiny`, `base`, `small`, `medium`, `large`).
   - Emits structured transcript dictionary containing: `text`, `segments` (with start/end timestamps), `language`, and `duration`.

3. **`src/validator.py` (`FileValidator`, `TranscriptValidator`)**:
   - **`FileValidator`**: Enforces allowable MIME types, supported extensions (`.wav`, `.mp3`, `.m4a`, `.mp4`, `.webm`, `.aac`, `.flac`), and maximum file size ceiling (500 MB).
   - **`TranscriptValidator`**: Validates character lengths, minimum word counts, detects empty/silent recordings, and flags low-quality speech transcripts.

4. **`src/transcript_manager.py` (`TranscriptManager`)**:
   - Persists speech-to-text outputs into timestamped JSON files under `data/transcripts/`.
   - Provides listing, metadata retrieval, and deletion operations.

---

### 🧠 Milestone 2 — LLM Intelligence, Action Item Extraction & Database Persistence

#### Objective
Convert raw unstructured transcripts into structured intelligence (executive summaries, key decisions, prioritized action items, and participant accountability) and persist them into a relational SQLite database.

#### Core Modules
1. **`src/llm/service.py` (`LLMService`)**:
   - Connects to Google Gemini (`gemini-1.5-flash` / `gemini-3.1-flash-lite`).
   - Implements exponential backoff retry policy (initial delay 2.0s, ceiling 30.0s, max 4 retries) to handle rate limits (`429`) and transient network issues.
   - Comprehensive prompt engineering in `src/llm/prompts.py`.
   - Robust JSON sanitization and schema validation in `src/llm/validators.py`.

2. **`src/summarizer.py` (`MeetingSummarizer`)**:
   - Synthesizes executive summaries capturing context, discussion points, and strategic outcomes.
   - Extracts explicit key decisions agreed upon during the meeting.
   - Provides rule-based `_heuristic_fallback` when external LLM APIs are offline.

3. **`src/action_item_extractor.py` (`ActionItemExtractor`)**:
   - Identifies actionable commitments and deliverables from transcript utterances.
   - Normalizes task attributes: `action`, `owner` (assignee), `deadline`, `priority` (`High`, `Medium`, `Low`), and `status` (`Pending`, `In Progress`, `Completed`, `Blocked`).

4. **`src/participant_mapper.py` (`ParticipantMapper`)**:
   - Resolves participant names into canonical representations (e.g., `"Dr. Ravi Kumar"`, `"Ravi"`, `"r.kumar"` -> `"Ravi Kumar"`).
   - Maps specific action items and commitments directly to their accountable owner.

5. **`src/database.py` (`DatabaseManager`)**:
   - SQLite relational persistence with foreign keys enabled (`PRAGMA foreign_keys = ON;`).
   - Transactional persistence in `save_meeting_intelligence()` creating meeting records and child entities (`summaries`, `decisions`, `action_items`, `participants`).
   - Integrity verification in `verify_database_integrity()` detecting orphaned records and checking 100% bidirectional linkages.

---

### ⚡ Milestone 3 — Vector Embeddings, Semantic Search & Grounded RAG

#### Objective
Index meeting records into dense vector embeddings, build an in-memory/SQLite vector database engine, execute sub-3-second semantic search, and synthesize grounded answers with explicit citations.

#### Core Modules
1. **`src/embeddings.py` (`EmbeddingGenerator`)**:
   - Generates normalized dense vector embeddings for meeting entities:
     - `transcript_section`: Sliding window text chunks with speaker attribution.
     - `summary`: High-level executive summary vector.
     - `decision`: Individual key decision vectors.
     - `action_item`: Deliverable and task vectors.
   - Provides deterministic embeddings in sandbox mode and Gemini/Sentence-Transformer embeddings in connected mode.

2. **`src/vector_db.py` (`VectorDatabase`)**:
   - Computes cosine similarity between query vectors and stored embeddings.
   - Supports metadata filtering by `meeting_id`, `entity_type`, and date intervals.
   - Fast batch vector indexing with database persistence in `embeddings` table.

3. **`src/semantic_search.py` (`SemanticSearchEngine`)**:
   - Multi-entity search across metadata, transcripts, summaries, decisions, and participants.
   - Guarantees **sub-3-second latency SLA** (`sla_met: true`).
   - Computes relevance percentages, snippet highlights, and matched entity counts.

4. **`src/repository.py` (`MeetingKnowledgeRepository`)**:
   - Central coordinator connecting SQLite relational database, Vector Store, Semantic Search Engine, and LLM Service.
   - Executes RAG `ask(question, top_k)` returning synthesized answers grounded strictly in retrieved context with citations.
   - Bidirectional vector-to-meeting traceability ensuring vector records accurately point back to their parent meeting.

---

### 🚀 Milestone 4 — Dashboard, Integrations, Security & Deployment

#### 1. Streamlit Dashboard & Meeting Details (Tasks 1 & 2)
- **Main Dashboard (`src/ui/views/dashboard.py`)**:
  - KPI Cards: Total Persisted Meetings, Action Items (with pending count), Processed Transcripts, and Summary Archives.
  - Tab 1: Meeting Browser with date & keyword filters.
  - Tab 2: Action Items Tracker with status/assignee filters.
  - Tab 3: Embedded AI Assistant for RAG queries.
  - Tab 4: Team & Participant Directory.
  - Tab 5: Quick Audio/Video Upload & text ingestion.
- **Meeting Details Page (`src/ui/views/meeting_details.py`)**:
  - Full flow: Meeting Selection -> Metadata Overview -> Transcript Viewer -> Summary -> Key Decisions -> Action Items & Deadlines -> Participants -> Analytics Charts.
  - Interactive Action Item Status updates in database.

#### 2. Cloud Integrations (Tasks 4 & 5)
- **Zoom (`src/integrations/zoom.py`)**: Server-to-Server OAuth, cloud recording browser, deduplication, webhook handler (`POST /integrations/zoom/webhook`).
- **Google Meet (`src/integrations/google_meet.py`)**: Google Drive recordings ingestion, deduplication, auto Whisper & LLM pipeline execution.

#### 3. Reports & Exporters (Task 6)
- **ReportLab Exporter (`src/reports/exporter.py`)**:
  - `generate_meeting_pdf`: Executive PDF report with styled tables and metadata.
  - `generate_meeting_csv`: Clean tabular CSV report export.
  - REST endpoints: `GET /meetings/{id}/export?format=pdf` and `GET /meetings/{id}/export?format=csv`.

#### 4. Multi-Tenant User Authentication & Security (Task 7)
- **Auth Manager (`src/auth.py`)**: PBKDF2-HMAC-SHA256 password hashing, cryptographic salts, anti-tamper signed session tokens, and tenant data isolation in SQLite queries.
- Protected API endpoints returning `401 Unauthorized` for invalid or missing credentials.

#### 5. Deployment & Production Setup (Task 10)
- Multi-stage `Dockerfile` and `docker-compose.yml`.
- Unified launcher `run_app.py` supporting `--mode=both`, `--mode=api`, `--mode=streamlit`.

---

## 🗄️ Database Relational Schema

```sql
-- Users Table (Milestone 4 - Task 7)
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    role TEXT DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Meetings Table
CREATE TABLE IF NOT EXISTS meetings (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    original_filename TEXT,
    transcript_text TEXT NOT NULL,
    duration REAL DEFAULT 0,
    user_id TEXT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Summaries Table
CREATE TABLE IF NOT EXISTS summaries (
    id TEXT PRIMARY KEY,
    meeting_id TEXT NOT NULL,
    summary_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
);

-- Decisions Table
CREATE TABLE IF NOT EXISTS decisions (
    id TEXT PRIMARY KEY,
    meeting_id TEXT NOT NULL,
    decision_text TEXT NOT NULL,
    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
);

-- Action Items Table
CREATE TABLE IF NOT EXISTS action_items (
    id TEXT PRIMARY KEY,
    meeting_id TEXT NOT NULL,
    action TEXT NOT NULL,
    owner TEXT,
    deadline TEXT,
    priority TEXT DEFAULT 'Medium',
    status TEXT DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
);

-- Participants Table
CREATE TABLE IF NOT EXISTS participants (
    id TEXT PRIMARY KEY,
    meeting_id TEXT NOT NULL,
    name TEXT NOT NULL,
    canonical_name TEXT NOT NULL,
    role TEXT,
    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
);

-- Embeddings Table
CREATE TABLE IF NOT EXISTS embeddings (
    id TEXT PRIMARY KEY,
    meeting_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT,
    section_index INTEGER DEFAULT 0,
    text_content TEXT NOT NULL,
    embedding_vector TEXT NOT NULL,
    dimension INTEGER NOT NULL,
    model_name TEXT NOT NULL,
    metadata_json TEXT DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
);
```

---

## 🌐 FastAPI REST API Reference

| Endpoint | Method | Purpose | Authentication |
| :--- | :---: | :--- | :---: |
| `/health` | `GET` | System diagnostics & status | Public |
| `/auth/register` | `POST` | Register a new user | Public |
| `/auth/login` | `POST` | Authenticate & issue token | Public |
| `/auth/me` | `GET` | Current user session inspection | Bearer Token / API Key |
| `/meetings` | `GET` | List meetings with filters | Bearer Token / API Key |
| `/meetings/{id}` | `GET` | Retrieve complete meeting details | Bearer Token / API Key |
| `/meetings/{id}` | `DELETE`| Delete meeting & child records | Bearer Token / API Key |
| `/meetings/{id}/analytics`| `GET`| Compute meeting metrics & charts | Bearer Token / API Key |
| `/meetings/{id}/export` | `GET` | Export report as PDF or CSV | Bearer Token / API Key |
| `/search` | `POST`| Sub-3s semantic vector search | Bearer Token / API Key |
| `/ask` | `POST`| Grounded RAG Question Answering | Bearer Token / API Key |
| `/integrations/zoom/recordings` | `GET` | List Zoom cloud recordings | Bearer Token / API Key |
| `/integrations/zoom/import` | `POST` | Ingest Zoom recording into pipeline | Bearer Token / API Key |
| `/integrations/zoom/webhook` | `POST` | Zoom webhook receiver | Webhook / Secret |
| `/integrations/google-meet/recordings` | `GET` | List Google Meet Drive recordings | Bearer Token / API Key |
| `/integrations/google-meet/import` | `POST` | Ingest Google Meet recording | Bearer Token / API Key |
| `/integrations/google-meet/webhook` | `POST` | Google Drive push notification | Webhook |

---

## 🧪 Test Suite Results (169 / 169 Passing)

```powershell
============================= test session starts =============================
platform win32 -- Python 3.14.4, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\DELL\Desktop\AI\AI-Career-Intelligence-Platform
plugins: anyio-4.14.2
collected 169 items

tests\test_action_items.py .............                                 [  7%]
tests\test_api.py ........                                               [ 12%]
tests\test_auth_security.py .....                                        [ 15%]
tests\test_database.py ......                                            [ 18%]
tests\test_e2e_integration.py .                                          [ 19%]
tests\test_embeddings.py ..........                                      [ 25%]
tests\test_integrations.py ...                                           [ 27%]
tests\test_knowledge_repository.py .............                         [ 34%]
tests\test_llm_service.py .......................                        [ 48%]
tests\test_milestone4_e2e.py .                                           [ 49%]
tests\test_milestone4_performance_security.py ....                       [ 51%]
tests\test_participant_mapping.py .....                                  [ 54%]
tests\test_performance_edge_cases.py ........                            [ 59%]
tests\test_pipeline.py ..                                                [ 60%]
tests\test_reports_export.py ...                                         [ 62%]
tests\test_search_rag_validation.py .........                            [ 67%]
tests\test_semantic_search.py .......                                    [ 71%]
tests\test_summarizer.py .........                                       [ 76%]
tests\test_transcript_validation.py ........                             [ 81%]
tests\test_transcription.py ...                                          [ 83%]
tests\test_upload.py ......                                              [ 86%]
tests\test_validation.py .......                                         [ 91%]
tests\test_vector_db.py .........                                        [100%]

======================= 169 passed in 83.15s (0:01:23) ========================
```

---

## 🚀 Quick Launch Guide

1. **Start unified server (FastAPI + Streamlit)**:
   ```powershell
   python run_app.py --mode=both
   ```
2. **Access URL endpoints**:
   - Streamlit Dashboard: `http://localhost:8501`
   - FastAPI OpenAPI Docs: `http://localhost:8000/docs`
   - Health Check: `http://localhost:8000/health`
3. **Default Demo Credentials**:
   - Admin: `demo_user` / `DemoUser2026!`
   - Standard: `user2` / `User2Password!`
   - API Key: `career-intel-dev-key-2026`
