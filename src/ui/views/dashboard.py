"""
Dashboard View - AI Career Intelligence Platform
Provides executive overview, real statistics from database, quick actions, and recent activity.
"""

import streamlit as st
from pathlib import Path
from src.ui.components import render_header, render_hero_banner, render_kpi_card, render_empty_state


def render_dashboard_view(db_manager, transcript_manager, summary_manager):
    """Render the executive SaaS dashboard."""
    render_header(
        title="AI Career Intelligence Dashboard",
        subtitle="Understand your interview performance and turn conversations into actionable career insights.",
        badge_text="System Active",
        badge_color="#10b981"
    )

    # Hero Banner
    render_hero_banner(
        title="Turn Every Interview Into Career Intelligence",
        subtitle="Upload your interview recordings or transcripts to automatically extract executive summaries, key decisions, prioritized action items, and participant commitments.",
        badge_text="Analyze • Understand • Improve • Prepare • Grow"
    )

    # Fetch real statistics from database and managers
    db_meetings = db_manager.get_all_meetings() if db_manager else []
    db_actions = db_manager.get_all_action_items() if db_manager else []
    saved_transcripts = transcript_manager.list_transcripts() if transcript_manager else []
    saved_summaries = summary_manager.list_summaries() if summary_manager else []

    total_meetings = len(db_meetings)
    total_actions = len(db_actions)
    total_transcripts = len(saved_transcripts)
    total_summaries = len(saved_summaries)

    # Metric Cards Row
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        render_kpi_card(
            title="Persisted Meetings",
            value=total_meetings,
            subtitle="Saved in Database",
            icon="📁",
            icon_bg="#eef2ff"
        )
    with m2:
        render_kpi_card(
            title="Action Items",
            value=total_actions,
            subtitle="Tracked Commitments",
            icon="⚡",
            icon_bg="#fef3c7"
        )
    with m3:
        render_kpi_card(
            title="Transcripts",
            value=total_transcripts,
            subtitle="Processed Audio & Text",
            icon="🎙️",
            icon_bg="#f0fdf4"
        )
    with m4:
        render_kpi_card(
            title="Summary Archives",
            value=total_summaries,
            subtitle="JSON Intelligence Files",
            icon="📑",
            icon_bg="#fdf4ff"
        )

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # Quick Action Cards & Navigation Shortcuts
    st.markdown("#### ⚡ Quick Actions")
    col_act1, col_act2, col_act3, col_act4 = st.columns(4)

    with col_act1:
        with st.container():
            st.markdown("""
            <div class="ui-card" style="min-height: 165px;">
                <div style="font-size: 24px; margin-bottom: 8px;">🎤</div>
                <div style="font-weight: 700; font-size: 15px; color: #0f172a; margin-bottom: 4px;">Analyze Interview</div>
                <div style="font-size: 13px; color: #64748b; margin-bottom: 12px;">Upload recording or paste transcript to run AI Whisper & Gemini intelligence.</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Start Analysis →", key="dash_btn_analyze", type="primary", use_container_width=True):
                st.session_state["nav_page"] = "Interview Analysis"
                st.rerun()

    with col_act2:
        with st.container():
            st.markdown("""
            <div class="ui-card" style="min-height: 165px;">
                <div style="font-size: 24px; margin-bottom: 8px;">🧠</div>
                <div style="font-weight: 700; font-size: 15px; color: #0f172a; margin-bottom: 4px;">AI Search & Repo</div>
                <div style="font-size: 13px; color: #64748b; margin-bottom: 12px;">Search historical meeting knowledge, decisions, participants & deadlines.</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Search Knowledge →", key="dash_btn_search_repo", use_container_width=True):
                st.session_state["nav_page"] = "Knowledge Repository"
                st.rerun()

    with col_act3:
        with st.container():
            st.markdown("""
            <div class="ui-card" style="min-height: 165px;">
                <div style="font-size: 24px; margin-bottom: 8px;">📝</div>
                <div style="font-weight: 700; font-size: 15px; color: #0f172a; margin-bottom: 4px;">Transcript Workspace</div>
                <div style="font-size: 13px; color: #64748b; margin-bottom: 12px;">View, inspect quality metrics, and search through speech-to-text transcripts.</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Open Transcripts →", key="dash_btn_transcripts", use_container_width=True):
                st.session_state["nav_page"] = "Transcript Workspace"
                st.rerun()

    with col_act4:
        with st.container():
            st.markdown("""
            <div class="ui-card" style="min-height: 165px;">
                <div style="font-size: 24px; margin-bottom: 8px;">🗄️</div>
                <div style="font-weight: 700; font-size: 15px; color: #0f172a; margin-bottom: 4px;">Database Archive</div>
                <div style="font-size: 13px; color: #64748b; margin-bottom: 12px;">Manage relational database records, query cross-meeting tasks, and export.</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("View Database →", key="dash_btn_database", use_container_width=True):
                st.session_state["nav_page"] = "Database & Archive"
                st.rerun()

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # Recent Activity & Meetings Section
    col_hist1, col_hist2 = st.columns([3, 2])

    with col_hist1:
        st.markdown("#### 🕒 Recent Persisted Meetings")
        if db_meetings:
            for m in db_meetings[:4]:
                with st.expander(f"📁 {m['title']} • {m['created_at'][:10]}"):
                    st.write(f"**Original File:** `{m.get('original_filename') or 'Pasted Transcript'}` | **Duration:** {m.get('duration', 0):.1f}s")
                    if m.get("summary"):
                        st.markdown(f"**Summary:** {m['summary'][:220]}...")
                    if st.button(f"🔍 View Full Insights in Workspace", key=f"dash_open_m_{m['id']}"):
                        full_m = db_manager.get_meeting(m['id'])
                        if full_m:
                            st.session_state["active_transcript"] = full_m.get("transcript_text", "")
                            st.session_state["active_source_name"] = full_m.get("title", "Meeting")
                            st.session_state["latest_summary"] = {
                                "summary": full_m.get("summary", ""),
                                "key_decisions": full_m.get("decisions", []),
                                "action_items": full_m.get("action_items", [])
                            }
                            st.session_state["extracted_actions_list"] = full_m.get("action_items", [])
                            st.session_state["mapped_participants_list"] = full_m.get("participants", [])
                            st.session_state["nav_page"] = "AI Insights"
                            st.rerun()
        else:
            render_empty_state(
                title="No meetings saved in database yet",
                description="Process an audio/video recording or paste a transcript to persist meeting intelligence.",
                icon="🗄️"
            )

    with col_hist2:
        st.markdown("#### 🗺️ Intelligence Workflow")
        st.markdown("""
        <div class="ui-card" style="background: #ffffff;">
            <div style="display: flex; flex-direction: column; gap: 14px;">
                <div style="display: flex; gap: 12px; align-items: flex-start;">
                    <div style="background: #eef2ff; color: #4f46e5; width: 26px; height: 26px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 12px;">1</div>
                    <div>
                        <div style="font-weight: 700; font-size: 13.5px; color: #0f172a;">Input & Transcribe</div>
                        <div style="font-size: 12px; color: #64748b;">Upload recording or paste text with Whisper speech engine.</div>
                    </div>
                </div>
                <div style="display: flex; gap: 12px; align-items: flex-start;">
                    <div style="background: #eef2ff; color: #4f46e5; width: 26px; height: 26px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 12px;">2</div>
                    <div>
                        <div style="font-weight: 700; font-size: 13.5px; color: #0f172a;">AI Analysis & Extraction</div>
                        <div style="font-size: 12px; color: #64748b;">Gemini extracts executive summaries, decisions, & tasks.</div>
                    </div>
                </div>
                <div style="display: flex; gap: 12px; align-items: flex-start;">
                    <div style="background: #eef2ff; color: #4f46e5; width: 26px; height: 26px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 12px;">3</div>
                    <div>
                        <div style="font-weight: 700; font-size: 13.5px; color: #0f172a;">Map Responsibilities</div>
                        <div style="font-size: 12px; color: #64748b;">Track participant commitments and assignees.</div>
                    </div>
                </div>
                <div style="display: flex; gap: 12px; align-items: flex-start;">
                    <div style="background: #eef2ff; color: #4f46e5; width: 26px; height: 26px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 12px;">4</div>
                    <div>
                        <div style="font-weight: 700; font-size: 13.5px; color: #0f172a;">Persist & Manage</div>
                        <div style="font-size: 12px; color: #64748b;">SQLite relational storage with multi-format export.</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
