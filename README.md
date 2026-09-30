# AI Career Intelligence Platform - Enterprise Edition (v4.0)

An executive-grade AI SaaS platform for audio & video transcription, LLM meeting intelligence, multi-tenant security, Zoom & Google Meet integrations, dense vector RAG search, and automated executive report exports (PDF/CSV).

---

## 🚀 Key Capabilities (Milestones 1 - 4)

- **🎙️ Speech Transcription (Milestone 1)**: Whisper & Faster-Whisper audio/video processing, validation, and storage.
- **🧠 LLM Intelligence (Milestone 2)**: Gemini LLM extraction for executive summaries, key decisions, prioritized action items, and participant responsibility mapping with SQLite relational persistence.
- **⚡ Vector Knowledge Repository & RAG (Milestone 3)**: Dense vector embeddings, cosine similarity vector search, metadata filtering, sub-3-second SLA, and grounded citations.
- **📊 Executive Dashboard & Analytics (Milestone 4 - Tasks 1 & 2)**: Full Streamlit dashboard, meeting details & analytics view with speaking distribution and timeline metrics.
- **🧠 RAG Search & AI Assistant (Milestone 4 - Task 3)**: Natural-language query interface returning synthesized grounded answers with source citations.
- **📹 Zoom Cloud Integration (Milestone 4 - Task 4)**: Server-to-Server OAuth, cloud recording browser, duplicate detection, and automated pipeline ingestion.
- **🎥 Google Meet Integration (Milestone 4 - Task 5)**: Google Drive recordings ingestion, Whisper transcription, and knowledge repository indexing.
- **📄 Reports & Exports (Milestone 4 - Task 6)**: Executive PDF report generation via ReportLab and structured CSV exports.
- **🔐 Multi-Tenant Authentication & Security (Milestone 4 - Task 7)**: PBKDF2-HMAC-SHA256 password hashing, signed session tokens, user-specific data isolation, and unauthorized access rejection.
- **🚀 Production Deployment (Milestone 4 - Task 10)**: Docker multi-stage containerization, Docker Compose, and unified launcher.

---

## 📁 System Architecture

```
AI-Career-Intelligence-Platform/
├── app.py                          # Streamlit UI application & view router
├── run_app.py                      # Unified launcher (API + Streamlit)
├── Dockerfile                      # Production multi-stage Docker build
├── docker-compose.yml              # Container orchestration
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variable documentation
├── src/
│   ├── auth.py                    # PBKDF2 hashing, session tokens & tenant isolation
│   ├── api.py                     # FastAPI REST API layer & OpenAPI documentation
│   ├── database.py                # SQLite relational persistence & user management
│   ├── embeddings.py              # Dense vector embedding generator
│   ├── vector_db.py               # Vector similarity search engine
│   ├── repository.py              # Knowledge repository coordinator & RAG
│   ├── semantic_search.py         # Sub-3s multi-entity search engine
│   ├── pipeline.py                # End-to-end processing pipeline
│   ├── transcriber.py             # Whisper speech-to-text engine
│   ├── summarizer.py              # LLM executive summarizer
│   ├── action_item_extractor.py   # Action item & priority extractor
│   ├── participant_mapper.py      # Participant mapping & accountability
│   ├── integrations/              # Cloud platform integrations
│   │   ├── zoom.py                # Zoom cloud recordings integration & webhooks
│   │   └── google_meet.py         # Google Meet / Drive recordings integration
│   ├── reports/                   # Document exports
│   │   └── exporter.py            # Executive PDF (ReportLab) & CSV exporter
│   └── ui/                        # Modern SaaS Streamlit design system
│       ├── theme.py               # CSS design tokens & component styling
│       ├── components.py          # KPI cards, badges, banners, headers
│       └── views/                 # Modular application views
│           ├── dashboard.py       # Main executive dashboard
│           ├── meeting_details.py # Complete meeting details & analytics
│           ├── integrations_view.py # Zoom & Google Meet ingestion
│           └── auth_modal.py      # User login, registration & switcher
└── tests/                         # 169+ automated pytest unit & E2E test suite
```

---

## 🛠️ Quickstart Installation

### 1. Prerequisites
- **Python 3.9+** (Tested on Python 3.11 / 3.14)
- **FFmpeg** installed and on your system PATH

### 2. Setup Virtual Environment & Install
```powershell
cd AI-Career-Intelligence-Platform
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Environment Variables
```powershell
copy .env.example .env
```
Edit `.env` and set your `LLM_API_KEY` (Gemini API key). If running offline, sandbox fallbacks will engage automatically.

### 4. Run the Full Platform (API + Streamlit UI)
```powershell
python run_app.py --mode=both
```
- **Streamlit Dashboard**: [http://localhost:8501](http://localhost:8501)
- **FastAPI Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **API Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 🐳 Docker Deployment

To launch the complete application with Docker and Docker Compose:
```bash
docker compose up --build
```

---

## 🧪 Running Automated Tests

Run the complete test suite (169 tests covering authentication, integrations, RAG, database, pipeline, exports, and performance):
```powershell
pytest tests/
```

---

## 🔐 Default Demo Accounts

For instant evaluation in the Streamlit UI or API:
- **Admin User**: `demo_user` / `DemoUser2026!`
- **Standard User**: `user2` / `User2Password!`
- **Developer API Key**: `career-intel-dev-key-2026`
