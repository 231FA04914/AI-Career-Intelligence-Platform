"""
AI Career Intelligence Platform - Main Application
Executive-Grade AI SaaS Interface for Audio Transcription, LLM Intelligence & Career Analytics.
"""

import os
import ssl
import sys
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st

# Load environment variables from the project root
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# Disable SSL verification for huggingface_hub if needed
os.environ['HF_HUB_DISABLE_SSL_VERIFY'] = '1'
ssl._create_default_https_context = ssl._create_unverified_context

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import Backend Services
from src.audio_processor import AudioProcessor
from src.transcriber import Transcriber
from src.validator import FileValidator, TranscriptValidator
from src.transcript_manager import TranscriptManager
from src.summary_manager import SummaryManager
from src.database import DatabaseManager
from src.embeddings import EmbeddingGenerator
from src.vector_db import VectorDatabase
from src.repository import MeetingKnowledgeRepository
from src.llm import LLMService, AuthenticationError
from src.summarizer import MeetingSummarizer
from src.action_item_extractor import ActionItemExtractor
from src.participant_mapper import ParticipantMapper
from src.pipeline import MeetingIntelligencePipeline

# Import UI System & Views
from src.ui.theme import apply_theme
from src.ui.components import render_sidebar_brand, render_system_status, render_footer
from src.ui.views.dashboard import render_dashboard_view
from src.ui.views.interview_analysis import render_interview_analysis_view
from src.ui.views.transcript_view import render_transcript_view
from src.ui.views.ai_insights import render_ai_insights_view
from src.ui.views.career_intelligence import render_career_intelligence_view
from src.ui.views.interview_prep import render_interview_prep_view
from src.ui.views.knowledge_repository import render_knowledge_repository_view
from src.ui.views.database_archive import render_database_archive_view
from src.ui.views.settings_view import render_settings_view


# Page Configuration
st.set_page_config(
    page_title="AI Career Intelligence",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)


def init_session_state():
    """Initialize default session state keys."""
    if "nav_page" not in st.session_state:
        st.session_state["nav_page"] = "Dashboard"
    if "active_transcript" not in st.session_state:
        st.session_state["active_transcript"] = ""
    if "active_source_name" not in st.session_state:
        st.session_state["active_source_name"] = "interview_transcript.txt"
    if "latest_summary" not in st.session_state:
        st.session_state["latest_summary"] = None
    if "extracted_actions_list" not in st.session_state:
        st.session_state["extracted_actions_list"] = []
    if "mapped_participants_list" not in st.session_state:
        st.session_state["mapped_participants_list"] = []


def main():
    """Main application lifecycle and routing."""
    # Apply modern SaaS CSS theme
    apply_theme()
    init_session_state()

    # Initialize backend components
    audio_processor = AudioProcessor(use_temp=True)
    transcriber = Transcriber(model_size="base")
    file_validator = FileValidator()
    transcript_validator = TranscriptValidator()
    transcript_manager = TranscriptManager()
    summary_manager = SummaryManager()
    db_manager = DatabaseManager()
    embedder = EmbeddingGenerator()
    vector_db = VectorDatabase(db_manager=db_manager, embedding_generator=embedder)

    # Initialize AI LLM Pipeline components
    try:
        llm_service = LLMService()
        meeting_summarizer = MeetingSummarizer(llm_service=llm_service)
        action_extractor = ActionItemExtractor(llm_service=llm_service)
        participant_mapper = ParticipantMapper(llm_service=llm_service)
        pipeline = MeetingIntelligencePipeline(
            audio_processor=audio_processor,
            transcriber=transcriber,
            llm_service=llm_service,
            db_manager=db_manager,
            embedding_generator=embedder
        )
        repository = MeetingKnowledgeRepository(
            db_manager=db_manager,
            llm_service=llm_service,
            embedding_generator=embedder,
            vector_db=vector_db
        )
        ai_ready = True
    except AuthenticationError:
        llm_service = None
        meeting_summarizer = None
        action_extractor = None
        participant_mapper = None
        pipeline = None
        repository = MeetingKnowledgeRepository(db_manager=db_manager, llm_service=None, embedding_generator=embedder, vector_db=vector_db)
        ai_ready = False
    except Exception:
        llm_service = None
        meeting_summarizer = None
        action_extractor = None
        participant_mapper = None
        pipeline = None
        repository = MeetingKnowledgeRepository(db_manager=db_manager, llm_service=None, embedding_generator=embedder, vector_db=vector_db)
        ai_ready = False

    # ----------------------------------------------------
    # SIDEBAR NAVIGATION
    # ----------------------------------------------------
    render_sidebar_brand()

    st.sidebar.markdown('<div class="nav-header">Main Navigation</div>', unsafe_allow_html=True)

    nav_options = [
        "🏠 Dashboard",
        "🎤 Interview Analysis",
        "📝 Transcript Workspace",
        "🧠 AI Insights",
        "🔍 Knowledge Repository",
        "📊 Career Intelligence",
        "🎯 Interview Preparation",
        "🗄️ Database & Archive",
        "⚙️ Settings & Health"
    ]

    # Map current state to nav options
    page_to_option = {
        "Dashboard": "🏠 Dashboard",
        "Interview Analysis": "🎤 Interview Analysis",
        "Transcript Workspace": "📝 Transcript Workspace",
        "AI Insights": "🧠 AI Insights",
        "Knowledge Repository": "🔍 Knowledge Repository",
        "Career Intelligence": "📊 Career Intelligence",
        "Interview Preparation": "🎯 Interview Preparation",
        "Database & Archive": "🗄️ Database & Archive",
        "Settings & Health": "⚙️ Settings & Health"
    }
    option_to_page = {v: k for k, v in page_to_option.items()}

    current_idx = 0
    if st.session_state["nav_page"] in page_to_option:
        current_idx = nav_options.index(page_to_option[st.session_state["nav_page"]])

    selected_option = st.sidebar.radio(
        "Navigation",
        options=nav_options,
        index=current_idx,
        label_visibility="collapsed"
    )

    # Sync navigation state
    selected_page = option_to_page[selected_option]
    if selected_page != st.session_state["nav_page"]:
        st.session_state["nav_page"] = selected_page
        st.rerun()

    # Sidebar Quick Stats / Status
    render_system_status(
        ai_ready=ai_ready,
        whisper_ready=True,
        db_ready=db_manager is not None
    )

    # ----------------------------------------------------
    # PAGE ROUTER
    # ----------------------------------------------------
    current_page = st.session_state["nav_page"]

    if current_page == "Dashboard":
        render_dashboard_view(
            db_manager=db_manager,
            transcript_manager=transcript_manager,
            summary_manager=summary_manager
        )

    elif current_page == "Interview Analysis":
        render_interview_analysis_view(
            audio_processor=audio_processor,
            transcriber=transcriber,
            file_validator=file_validator,
            transcript_validator=transcript_validator,
            transcript_manager=transcript_manager,
            meeting_summarizer=meeting_summarizer,
            action_extractor=action_extractor,
            participant_mapper=participant_mapper,
            pipeline=pipeline,
            db_manager=db_manager
        )

    elif current_page == "Transcript Workspace":
        render_transcript_view(
            transcript_manager=transcript_manager,
            transcript_validator=transcript_validator,
            meeting_summarizer=meeting_summarizer,
            action_extractor=action_extractor,
            participant_mapper=participant_mapper
        )

    elif current_page == "AI Insights":
        render_ai_insights_view(
            meeting_summarizer=meeting_summarizer,
            summary_manager=summary_manager,
            action_extractor=action_extractor,
            participant_mapper=participant_mapper,
            db_manager=db_manager
        )

    elif current_page == "Knowledge Repository":
        render_knowledge_repository_view(
            repository=repository,
            db_manager=db_manager
        )

    elif current_page == "Career Intelligence":
        render_career_intelligence_view()

    elif current_page == "Interview Preparation":
        render_interview_prep_view(
            db_manager=db_manager,
            llm_service=llm_service
        )

    elif current_page == "Database & Archive":
        render_database_archive_view(
            db_manager=db_manager,
            summary_manager=summary_manager,
            meeting_summarizer=meeting_summarizer
        )

    elif current_page == "Settings & Health":
        render_settings_view(
            llm_service=llm_service,
            transcriber=transcriber,
            db_manager=db_manager
        )

    # Global Footer
    render_footer()


if __name__ == "__main__":
    main()
