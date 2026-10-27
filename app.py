
"""
AI Career Intelligence Platform - Main Application
Milestone 4: Dashboard, Authentication, Meeting Intelligence and RAG
"""

import os
import ssl
import sys
from pathlib import Path

from dotenv import load_dotenv
import streamlit as st

# ----------------------------------------------------
# ENVIRONMENT CONFIGURATION
# ----------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

os.environ["HF_HUB_DISABLE_SSL_VERIFY"] = "1"
ssl._create_default_https_context = ssl._create_unverified_context

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# ----------------------------------------------------
# BACKEND IMPORTS
# ----------------------------------------------------
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
from src.auth import AuthManager
from src.integrations.zoom import ZoomIntegration
from src.integrations.google_meet import GoogleMeetIntegration

# ----------------------------------------------------
# UI IMPORTS
# ----------------------------------------------------
from src.ui.theme import apply_theme
from src.ui.components import (
    render_sidebar_brand,
    render_system_status,
    render_footer,
)
from src.ui.views.dashboard import render_dashboard_view
from src.ui.views.meeting_details import render_meeting_details_view
from src.ui.views.integrations_view import render_integrations_view
from src.ui.views.auth_modal import (
    render_auth_sidebar_widget,
    render_auth_dialog,
    render_login_view,
)
from src.ui.views.interview_analysis import render_interview_analysis_view
from src.ui.views.transcript_view import render_transcript_view
from src.ui.views.ai_insights import render_ai_insights_view
from src.ui.views.career_intelligence import render_career_intelligence_view
from src.ui.views.interview_prep import render_interview_prep_view
from src.ui.views.knowledge_repository import render_knowledge_repository_view
from src.ui.views.database_archive import render_database_archive_view
from src.ui.views.settings_view import render_settings_view

# ----------------------------------------------------
# PAGE CONFIGURATION
# ----------------------------------------------------
st.set_page_config(
    page_title="AI Career Intelligence",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ----------------------------------------------------
# SESSION STATE
# ----------------------------------------------------
def init_session_state():
    """Initialize default session state keys."""

    defaults = {
        "nav_page": "Dashboard",
        "active_transcript": "",
        "active_source_name": "interview_transcript.txt",
        "latest_summary": None,
        "extracted_actions_list": [],
        "mapped_participants_list": [],
        "selected_meeting_id": None,
        "show_auth_modal": False,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ----------------------------------------------------
# SIDEBAR READABILITY FIX
# ----------------------------------------------------
def apply_sidebar_readability_fix():
    """Improve navigation contrast on the light sidebar."""

    st.markdown(
        """
        <style>
        /* Light sidebar background */
        [data-testid="stSidebar"] {
            background-color: #FFFFFF !important;
        }

        /* Sidebar headings */
        [data-testid="stSidebar"] .nav-header {
            color: #64748B !important;
            font-size: 0.78rem !important;
            font-weight: 800 !important;
            letter-spacing: 0.08em !important;
            text-transform: uppercase !important;
        }

        /* Navigation labels: dark, readable text */
        [data-testid="stSidebar"] [data-testid="stRadio"] label {
            color: #1E293B !important;
            font-weight: 600 !important;
            border-radius: 9px !important;
        }

        [data-testid="stSidebar"] [data-testid="stRadio"] label p,
        [data-testid="stSidebar"] [data-testid="stRadio"] label span,
        [data-testid="stSidebar"] [data-testid="stRadio"] label div {
            color: #1E293B !important;
        }

        /* Navigation hover effect */
        [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
            background-color: #EEF2FF !important;
        }

        /* Selected navigation item */
        [data-testid="stSidebar"]
        [data-testid="stRadio"] label:has(input:checked) {
            background-color: #E0E7FF !important;
            color: #3730A3 !important;
        }

        [data-testid="stSidebar"]
        [data-testid="stRadio"] label:has(input:checked) p,
        [data-testid="stSidebar"]
        [data-testid="stRadio"] label:has(input:checked) span {
            color: #3730A3 !important;
            font-weight: 700 !important;
        }

        /* Sidebar input labels */
        [data-testid="stSidebar"] label {
            color: #1E293B;
        }

        /* Main dashboard typography */
        .stApp h1,
        .stApp h2,
        .stApp h3 {
            font-weight: 700;
        }

        /* Keep the main content from being clipped horizontally */
        [data-testid="stMainBlockContainer"] {
            padding-top: 2rem;
        }

        /* Responsive sidebar width */
        @media (min-width: 768px) {
            [data-testid="stSidebar"] {
                min-width: 270px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ----------------------------------------------------
# MAIN APPLICATION
# ----------------------------------------------------
def main():
    """Initialize services and route application pages."""

    # Apply existing theme first, then navigation contrast overrides.
    apply_theme()
    apply_sidebar_readability_fix()
    # Fix headings across all pages
    st.markdown("""
    <style>
    [data-testid="stMain"] h1,
    [data-testid="stMain"] h2,
    [data-testid="stMain"] h3 {
        color: #F8FAFC !important;
        background: transparent !important;
        -webkit-text-fill-color: #F8FAFC !important;
        text-shadow: none !important;
    }
    
    [data-testid="stMain"] {
        color: #F8FAFC;
    }
    </style>
    """, unsafe_allow_html=True)
    init_session_state()

    # ------------------------------------------------
    # INITIALIZE BACKEND SERVICES
    # ------------------------------------------------
    audio_processor = AudioProcessor(use_temp=True)
    transcriber = Transcriber(model_size="base")
    file_validator = FileValidator()
    transcript_validator = TranscriptValidator()
    transcript_manager = TranscriptManager()
    summary_manager = SummaryManager()

    db_manager = DatabaseManager()
    embedder = EmbeddingGenerator()

    vector_db = VectorDatabase(
        db_manager=db_manager,
        embedding_generator=embedder,
    )

    auth_manager = AuthManager(db_manager=db_manager)
    zoom_integration = ZoomIntegration()
    google_meet_integration = GoogleMeetIntegration()

    # ------------------------------------------------
    # INITIALIZE AI SERVICES
    # ------------------------------------------------
    try:
        llm_service = LLMService()

        meeting_summarizer = MeetingSummarizer(
            llm_service=llm_service
        )
        action_extractor = ActionItemExtractor(
            llm_service=llm_service
        )
        participant_mapper = ParticipantMapper(
            llm_service=llm_service
        )

        pipeline = MeetingIntelligencePipeline(
            audio_processor=audio_processor,
            transcriber=transcriber,
            llm_service=llm_service,
            db_manager=db_manager,
            embedding_generator=embedder,
        )

        repository = MeetingKnowledgeRepository(
            db_manager=db_manager,
            llm_service=llm_service,
            embedding_generator=embedder,
            vector_db=vector_db,
        )

        ai_ready = True

    except AuthenticationError:
        llm_service = None
        meeting_summarizer = None
        action_extractor = None
        participant_mapper = None
        pipeline = None

        repository = MeetingKnowledgeRepository(
            db_manager=db_manager,
            llm_service=None,
            embedding_generator=embedder,
            vector_db=vector_db,
        )

        ai_ready = False

    except Exception as exc:
        # Keep the rest of the application available if AI
        # initialization fails. Check server logs for details.
        print(f"AI service initialization failed: {exc}")

        llm_service = None
        meeting_summarizer = None
        action_extractor = None
        participant_mapper = None
        pipeline = None

        repository = MeetingKnowledgeRepository(
            db_manager=db_manager,
            llm_service=None,
            embedding_generator=embedder,
            vector_db=vector_db,
        )

        ai_ready = False

    # ------------------------------------------------
    # SIDEBAR BRAND AND AUTHENTICATION
    # ------------------------------------------------
    render_sidebar_brand()

    current_user = render_auth_sidebar_widget(auth_manager)

    user_id = (
        (current_user.get("user_id") or current_user.get("id"))
        if current_user
        else None
    )

    render_auth_dialog(auth_manager)

    # ------------------------------------------------
    # LOGIN ACCESS CONTROL
    # ------------------------------------------------
    if not current_user:
        st.sidebar.markdown(
            '<div class="nav-header">Platform Security</div>',
            unsafe_allow_html=True,
        )

        st.sidebar.info(
            "🔒 Main Navigation is locked. Please sign in "
            "or use a demo account to unlock all modules."
        )

        render_system_status(
            ai_ready=ai_ready,
            whisper_ready=True,
            db_ready=db_manager is not None,
        )

        render_login_view(auth_manager)
        render_footer()
        return

    # ------------------------------------------------
    # SIDEBAR NAVIGATION
    # ------------------------------------------------
    st.sidebar.markdown(
        '<div class="nav-header">Main Navigation</div>',
        unsafe_allow_html=True,
    )

    page_to_option = {
        "Dashboard": "🏠 Dashboard",
        "Meeting Details": "📋 Meeting Details & Analytics",
        "Interview Analysis": "🎤 Interview Analysis",
        "Transcript Workspace": "📝 Transcript Workspace",
        "AI Insights": "🧠 AI Insights",
        "Knowledge Repository": "🔍 Knowledge Repository & RAG",
        "Platform Integrations": "☁️ Cloud Platform Integrations",
        "Career Intelligence": "📊 Career Intelligence",
        "Interview Preparation": "🎯 Interview Preparation",
        "Database & Archive": "🗄️ Database & Archive",
        "Settings & Health": "⚙️ Settings & Health",
    }

    nav_options = list(page_to_option.values())
    option_to_page = {
        option: page for page, option in page_to_option.items()
    }

    current_page = st.session_state["nav_page"]

    if current_page not in page_to_option:
        current_page = "Dashboard"
        st.session_state["nav_page"] = current_page

    current_idx = nav_options.index(
        page_to_option[current_page]
    )

    selected_option = st.sidebar.radio(
        "Navigation",
        options=nav_options,
        index=current_idx,
        label_visibility="collapsed",
        key="main_navigation_radio",
    )

    selected_page = option_to_page[selected_option]

    if selected_page != st.session_state["nav_page"]:
        st.session_state["nav_page"] = selected_page
        st.rerun()

    # ------------------------------------------------
    # SYSTEM STATUS
    # ------------------------------------------------
    render_system_status(
        ai_ready=ai_ready,
        whisper_ready=True,
        db_ready=db_manager is not None,
    )

    # ------------------------------------------------
    # PAGE ROUTING
    # ------------------------------------------------
    current_page = st.session_state["nav_page"]

    if current_page == "Dashboard":
        render_dashboard_view(
            db_manager=db_manager,
            transcript_manager=transcript_manager,
            summary_manager=summary_manager,
            repository=repository,
            pipeline=pipeline,
            user_info=current_user,
        )

    elif current_page == "Meeting Details":
        render_meeting_details_view(
            db_manager=db_manager,
            user_id=user_id,
        )

    elif current_page == "Platform Integrations":
        render_integrations_view(
            zoom_integration=zoom_integration,
            google_meet_integration=google_meet_integration,
            pipeline=pipeline,
            db_manager=db_manager,
            user_id=user_id,
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
            db_manager=db_manager,
        )

    elif current_page == "Transcript Workspace":
        render_transcript_view(
            transcript_manager=transcript_manager,
            transcript_validator=transcript_validator,
            meeting_summarizer=meeting_summarizer,
            action_extractor=action_extractor,
            participant_mapper=participant_mapper,
        )

    elif current_page == "AI Insights":
        render_ai_insights_view(
            meeting_summarizer=meeting_summarizer,
            summary_manager=summary_manager,
            action_extractor=action_extractor,
            participant_mapper=participant_mapper,
            db_manager=db_manager,
        )

    elif current_page == "Knowledge Repository":
        render_knowledge_repository_view(
            repository=repository,
            db_manager=db_manager,
        )

    elif current_page == "Career Intelligence":
        render_career_intelligence_view()

    elif current_page == "Interview Preparation":
        render_interview_prep_view(
            db_manager=db_manager,
            llm_service=llm_service,
        )

    elif current_page == "Database & Archive":
        render_database_archive_view(
            db_manager=db_manager,
            summary_manager=summary_manager,
            meeting_summarizer=meeting_summarizer,
        )

    elif current_page == "Settings & Health":
        render_settings_view(
            llm_service=llm_service,
            transcriber=transcriber,
            db_manager=db_manager,
        )

    # ------------------------------------------------
    # GLOBAL FOOTER
    # ------------------------------------------------
    render_footer()


if __name__ == "__main__":
    main()
