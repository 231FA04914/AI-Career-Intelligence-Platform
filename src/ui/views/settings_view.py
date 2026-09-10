"""
Settings & System Health View - AI Career Intelligence Platform
Provides diagnostics, model configurations, and system health status safely without exposing secrets.
"""

import os
import streamlit as st
from pathlib import Path
from src.ui.components import render_header, render_kpi_card


def render_settings_view(llm_service, transcriber, db_manager):
    """Render the Settings and System Health dashboard."""
    render_header(
        title="Settings & System Health",
        subtitle="Review platform configuration, AI model parameters, and database connectivity.",
        badge_text="Diagnostics",
        badge_color="#4f46e5"
    )

    # Health Overview Cards
    ai_status = "Connected" if (llm_service and os.getenv("LLM_API_KEY")) else "Not Configured"
    whisper_status = "Ready (base)" if transcriber else "Available"
    db_status = "Online" if db_manager else "Offline"

    c1, c2, c3 = st.columns(3)
    with c1:
        render_kpi_card("LLM Service", ai_status, "Google Gemini Engine", "🧠", "#eef2ff")
    with c2:
        render_kpi_card("Whisper Engine", whisper_status, "Speech Transcription", "🎙️", "#f0fdf4")
    with c3:
        render_kpi_card("SQLite Database", db_status, "Relational Store", "🗄️", "#fef3c7")

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # Detailed Configuration Sections
    col_cfg1, col_cfg2 = st.columns(2)

    with col_cfg1:
        st.markdown("#### 🧠 AI Model Configuration")
        with st.container():
            st.markdown("""
            <div class="ui-card">
                <div style="display: flex; flex-direction: column; gap: 12px;">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #64748b; font-size: 13px;">Provider:</span>
                        <strong style="color: #0f172a; font-size: 13px;">Google Gemini</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #64748b; font-size: 13px;">Model:</span>
                        <strong style="color: #0f172a; font-size: 13px;">gemini-3.6-flash</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #64748b; font-size: 13px;">API Key Status:</span>
                        <span style="background: #ecfdf5; color: #15803d; padding: 2px 8px; border-radius: 9999px; font-size: 11px; font-weight: 700;">● Configured & Active</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #64748b; font-size: 13px;">Structured Output:</span>
                        <strong style="color: #0f172a; font-size: 13px;">JSON Mode (Strict)</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #64748b; font-size: 13px;">Max Tokens:</span>
                        <strong style="color: #0f172a; font-size: 13px;">4,000 tokens</strong>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col_cfg2:
        st.markdown("#### 🎙️ Speech & Audio Configuration")
        with st.container():
            st.markdown("""
            <div class="ui-card">
                <div style="display: flex; flex-direction: column; gap: 12px;">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #64748b; font-size: 13px;">Transcription Model:</span>
                        <strong style="color: #0f172a; font-size: 13px;">OpenAI Whisper (Base)</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #64748b; font-size: 13px;">Audio Preprocessor:</span>
                        <strong style="color: #0f172a; font-size: 13px;">FFmpeg (16kHz Mono WAV)</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #64748b; font-size: 13px;">Supported Audio Formats:</span>
                        <strong style="color: #0f172a; font-size: 13px;">.mp3, .wav, .m4a</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #64748b; font-size: 13px;">Supported Video Formats:</span>
                        <strong style="color: #0f172a; font-size: 13px;">.mp4, .webm</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #64748b; font-size: 13px;">Maximum File Size:</span>
                        <strong style="color: #0f172a; font-size: 13px;">500 MB</strong>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # Section 3: Database & Storage Diagnostics
    st.markdown("#### 🗄️ Storage & Database Diagnostics")
    db_meetings_cnt = len(db_manager.get_all_meetings()) if db_manager else 0
    db_actions_cnt = len(db_manager.get_all_action_items()) if db_manager else 0

    st.markdown(f"""
    <div class="ui-card">
        <div style="display: flex; flex-direction: column; gap: 10px;">
            <div style="display: flex; justify-content: space-between;">
                <span style="color: #64748b; font-size: 13px;">Database File Path:</span>
                <code style="background: #f1f5f9; padding: 2px 8px; border-radius: 6px; font-size: 12px;">data/meeting_intelligence.db</code>
            </div>
            <div style="display: flex; justify-content: space-between;">
                <span style="color: #64748b; font-size: 13px;">Relational Tables:</span>
                <strong style="color: #0f172a; font-size: 13px;">meetings, summaries, decisions, action_items, participants</strong>
            </div>
            <div style="display: flex; justify-content: space-between;">
                <span style="color: #64748b; font-size: 13px;">Persisted Meeting Records:</span>
                <strong style="color: #0f172a; font-size: 13px;">{db_meetings_cnt} meetings</strong>
            </div>
            <div style="display: flex; justify-content: space-between;">
                <span style="color: #64748b; font-size: 13px;">Tracked Action Items:</span>
                <strong style="color: #0f172a; font-size: 13px;">{db_actions_cnt} action items</strong>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
