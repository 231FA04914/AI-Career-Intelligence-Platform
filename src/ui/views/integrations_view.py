"""
Platform Integrations View (Milestone 4 - Tasks 4 & 5)
Provides management, browser, and automatic ingestion for Zoom and Google Meet cloud recordings.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Optional

from src.integrations.zoom import ZoomIntegration
from src.integrations.google_meet import GoogleMeetIntegration
from src.pipeline import MeetingIntelligencePipeline
from src.database import DatabaseManager
from src.ui.components import render_header, render_kpi_card, render_empty_state


def render_integrations_view(
    zoom_integration: ZoomIntegration,
    google_meet_integration: GoogleMeetIntegration,
    pipeline: MeetingIntelligencePipeline,
    db_manager: DatabaseManager,
    user_id: Optional[str] = None
):
    """Render Zoom and Google Meet Cloud Ingestion View."""
    render_header(
        title="Cloud Platform Integrations",
        subtitle="Automatically retrieve, transcribe, and index recordings from Zoom and Google Meet into the Meeting Knowledge Repository.",
        badge_text="Milestone 4: Cloud Recording Integrations",
        badge_color="#0284c7"
    )

    zoom_configured = zoom_integration.is_configured()
    gmeet_configured = google_meet_integration.is_configured()

    # Top KPI Row
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_kpi_card("Zoom Service", "Active" if zoom_configured else "Sandbox Ready", "Cloud Recording API", "📹", "#e0f2fe")
    with k2:
        render_kpi_card("Google Meet", "Active" if gmeet_configured else "Sandbox Ready", "Drive Recordings API", "🎥", "#f0fdf4")
    with k3:
        render_kpi_card("Auto-Pipeline", "Enabled", "Whisper + LLM + Vectors", "⚡", "#fef3c7")
    with k4:
        render_kpi_card("Deduplication", "Active", "Prevents duplicate imports", "🛡️", "#faf5ff")

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    tab_zoom, tab_meet, tab_webhooks = st.tabs([
        "📹 Zoom Cloud Recordings",
        "🎥 Google Meet & Drive",
        "🔗 Webhook Listeners & Logs"
    ])

    # ----------------------------------------------------
    # TAB 1: Zoom Cloud Recordings (Task 4)
    # ----------------------------------------------------
    with tab_zoom:
        st.markdown("#### 📹 Zoom Cloud Recordings Ingestion")
        st.caption("Browse cloud recordings in your Zoom account and import them into the meeting intelligence repository.")

        col_z_sync, col_z_stat = st.columns([3, 1])
        with col_z_sync:
            st.info("💡 **Mode:** " + ("Production OAuth Connected" if zoom_configured else "Developer Sandbox Mode (High-Fidelity Mock Recordings)"))
        with col_z_stat:
            if st.button("🔄 Refresh Zoom Recordings", key="btn_sync_zoom", use_container_width=True):
                st.rerun()

        # Fetch recordings
        recordings = zoom_integration.list_recordings()

        if recordings:
            for rec in recordings:
                rec_id = str(rec.get("id") or rec.get("uuid"))
                topic = rec.get("topic") or "Zoom Meeting"
                start_t = str(rec.get("start_time") or "")[:19].replace("T", " ")
                dur = rec.get("duration", 0)
                is_dup = zoom_integration.is_duplicate_recording(rec_id, db_manager)

                with st.expander(f"📹 {topic} • {start_t} ({dur} mins) {' [ALREADY INDEXED]' if is_dup else ''}", expanded=not is_dup):
                    st.write(f"**Recording ID:** `{rec_id}` | **Duration:** {dur} minutes | **Files:** {len(rec.get('recording_files', []))}")
                    if rec.get("share_url"):
                        st.write(f"**Share URL:** [{rec.get('share_url')}]({rec.get('share_url')})")

                    if is_dup:
                        st.success("✅ This recording has already been indexed in the database.")
                    else:
                        if st.button(f"⚡ Ingest & Process '{topic}'", key=f"btn_import_zoom_{rec_id}", type="primary"):
                            with st.spinner("Processing recording through Whisper speech transcription, LLM extraction & vector embeddings..."):
                                res = zoom_integration.process_zoom_recording(
                                    recording_data=rec,
                                    pipeline=pipeline,
                                    db_manager=db_manager,
                                    user_id=user_id
                                )
                            if res.get("success"):
                                st.success(f"🎉 Successfully ingested '{topic}'! Meeting ID: `{res.get('meeting_id')}`")
                                st.session_state["selected_meeting_id"] = res.get("meeting_id")
                                if st.button("🔍 View in Meeting Details →", key=f"btn_view_zoom_res_{rec_id}"):
                                    st.session_state["nav_page"] = "Meeting Details"
                                    st.rerun()
                            else:
                                st.error(f"Ingestion failed: {res.get('message') or res.get('error')}")
        else:
            render_empty_state("No Zoom recordings found", "No cloud recordings were returned by the Zoom API.", "📹")

    # ----------------------------------------------------
    # TAB 2: Google Meet & Drive (Task 5)
    # ----------------------------------------------------
    with tab_meet:
        st.markdown("#### 🎥 Google Meet Recordings Ingestion")
        st.caption("Retrieve Google Meet recordings from Google Drive and process them through the end-to-end intelligence workflow.")

        col_g_sync, col_g_stat = st.columns([3, 1])
        with col_g_sync:
            st.info("💡 **Mode:** " + ("Google Service Account Connected" if gmeet_configured else "Developer Sandbox Mode (High-Fidelity Mock Recordings)"))
        with col_g_stat:
            if st.button("🔄 Refresh Meet Recordings", key="btn_sync_meet", use_container_width=True):
                st.rerun()

        # Fetch Google Meet files
        meet_recs = google_meet_integration.list_recordings()

        if meet_recs:
            for rec in meet_recs:
                file_id = str(rec.get("id"))
                name = rec.get("name") or "Google Meet Session"
                created_t = str(rec.get("createdTime") or "")[:19].replace("T", " ")
                is_dup = google_meet_integration.is_duplicate_recording(file_id, db_manager)

                with st.expander(f"🎥 {name} • {created_t} {' [ALREADY INDEXED]' if is_dup else ''}", expanded=not is_dup):
                    st.write(f"**Drive File ID:** `{file_id}` | **Type:** `{rec.get('mimeType', 'video/mp4')}` | **Size:** {int(rec.get('size', 0)) // (1024*1024) if rec.get('size') else 0} MB")
                    if rec.get("webViewLink"):
                        st.write(f"**Drive Link:** [{rec.get('webViewLink')}]({rec.get('webViewLink')})")

                    if is_dup:
                        st.success("✅ This Google Meet recording is already indexed.")
                    else:
                        if st.button(f"⚡ Ingest & Process '{name}'", key=f"btn_import_meet_{file_id}", type="primary"):
                            with st.spinner("Executing Whisper speech transcription, LLM intelligence & vector generation..."):
                                res = google_meet_integration.process_google_meet_recording(
                                    recording_data=rec,
                                    pipeline=pipeline,
                                    db_manager=db_manager,
                                    user_id=user_id
                                )
                            if res.get("success"):
                                st.success(f"🎉 Successfully ingested '{name}'! Meeting ID: `{res.get('meeting_id')}`")
                                st.session_state["selected_meeting_id"] = res.get("meeting_id")
                                if st.button("🔍 View in Meeting Details →", key=f"btn_view_meet_res_{file_id}"):
                                    st.session_state["nav_page"] = "Meeting Details"
                                    st.rerun()
                            else:
                                st.error(f"Ingestion failed: {res.get('message') or res.get('error')}")
        else:
            render_empty_state("No Google Meet recordings found", "No recordings located in Google Drive.", "🎥")

    # ----------------------------------------------------
    # TAB 3: Webhook Listeners & Logs
    # ----------------------------------------------------
    with tab_webhooks:
        st.markdown("#### 🔗 Real-Time Webhook Configuration")
        st.markdown("""
        <div class="ui-card">
            <div style="font-weight: 700; font-size: 14px; margin-bottom: 6px;">Configured Webhook Endpoints:</div>
            <div style="margin-bottom: 8px;"><strong>Zoom Webhook URL:</strong> <code>POST http://localhost:8000/integrations/zoom/webhook</code></div>
            <div style="margin-bottom: 8px;"><strong>Google Meet Webhook URL:</strong> <code>POST http://localhost:8000/integrations/google-meet/webhook</code></div>
            <div style="font-size: 12px; color: #64748b;">Supported events: <code>meeting.recording_completed</code>, <code>endpoint.url_validation</code>, <code>drive.files.create</code></div>
        </div>
        """, unsafe_allow_html=True)
