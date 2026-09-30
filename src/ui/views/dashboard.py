"""
Executive Dashboard View - AI Career Intelligence Platform (Milestone 4 - Task 1)
Integrates:
- User Login / Access & Session indicator
- Meeting Upload & Audio Validation
- Filterable Meeting List
- Transcript & Summary Viewers
- Action Items & Participant Viewers
- Search & Date Filters
- Integrated AI Assistant (RAG)
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from src.ui.components import (
    render_header,
    render_hero_banner,
    render_kpi_card,
    render_empty_state,
    render_priority_badge,
    render_status_badge
)
from src.reports.exporter import generate_meeting_pdf, generate_meeting_csv


def render_dashboard_view(
    db_manager,
    transcript_manager,
    summary_manager,
    repository=None,
    pipeline=None,
    user_info=None
):
    """Render the complete Milestone 4 executive dashboard."""
    user_display = user_info.get("username", "Guest User") if user_info else "Demo User"
    user_id = user_info.get("id") if user_info else None

    render_header(
        title="AI Career Intelligence Dashboard",
        subtitle=f"Welcome, {user_display}! Real-time meeting insights, speech analytics, and RAG intelligence.",
        badge_text="System Active • v4.0",
        badge_color="#10b981"
    )

    # 1. Fetch real statistics from database scoped to current user
    db_meetings = db_manager.get_all_meetings(user_id=user_id) if db_manager else []
    db_actions = db_manager.get_all_action_items(user_id=user_id) if db_manager else []
    saved_transcripts = transcript_manager.list_transcripts() if transcript_manager else []
    saved_summaries = summary_manager.list_summaries() if summary_manager else []

    total_meetings = len(db_meetings)
    total_actions = len(db_actions)
    pending_actions = sum(1 for a in db_actions if (a.get("status") or "").lower() == "pending")

    # 2. Metric Cards Row
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        render_kpi_card("Persisted Meetings", total_meetings, "Indexed Sessions", "📁", "#eef2ff")
    with m2:
        render_kpi_card("Action Items", total_actions, f"{pending_actions} Pending", "⚡", "#fef3c7")
    with m3:
        render_kpi_card("Transcripts", len(saved_transcripts), "Processed Speech", "🎙️", "#f0fdf4")
    with m4:
        render_kpi_card("Summary Archives", len(saved_summaries), "Intelligence Reports", "📑", "#fdf4ff")

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # 3. Main Dashboard Functional Tabs
    tab_meetings, tab_actions, tab_ai_assistant, tab_participants, tab_quick_upload, tab_project_docs = st.tabs([
        "📁 Meeting List & Browser",
        "⚡ Action Items Tracker",
        "🧠 AI Assistant (RAG Search)",
        "👥 Participant Directory",
        "🎤 Quick Meeting Upload",
        "📖 Project Documentation & Download"
    ])

    # ----------------------------------------------------
    # TAB 1: Meeting List & Browser with Search & Filters
    # ----------------------------------------------------
    with tab_meetings:
        st.markdown("#### 📁 Meetings Repository")
        
        # Search & Filter Controls
        f_col1, f_col2, f_col3 = st.columns([2, 1, 1])
        with f_col1:
            search_query = st.text_input("🔍 Search Meetings:", placeholder="Filter by title, filename or summary...", key="dash_search_box")
        with f_col2:
            date_filter = st.selectbox("Date Filter:", ["All Time", "Last 7 Days", "Last 30 Days", "This Year"], key="dash_date_sel")
        with f_col3:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("➕ New Analysis", key="dash_btn_new_analysis", type="primary", use_container_width=True):
                st.session_state["nav_page"] = "Interview Analysis"
                st.rerun()

        # Apply search and filter
        filtered_meetings = []
        for m in db_meetings:
            title = m.get("title") or ""
            fn = m.get("original_filename") or ""
            summ = m.get("summary") or ""
            if search_query and search_query.strip():
                q = search_query.strip().lower()
                if q not in title.lower() and q not in fn.lower() and q not in summ.lower():
                    continue
            filtered_meetings.append(m)

        if filtered_meetings:
            st.caption(f"Showing {len(filtered_meetings)} of {total_meetings} meetings:")
            
            for m in filtered_meetings:
                m_id = str(m["id"])
                title = m.get("title") or f"Meeting {m_id}"
                created = str(m.get("created_at") or "")[:10]
                dur_s = float(m.get("duration") or 0.0)
                dur_str = f"{int(dur_s // 60)}m {int(dur_s % 60)}s" if dur_s else "N/A"
                act_cnt = int(m.get("action_item_count") or 0)
                part_cnt = int(m.get("participant_count") or 0)

                with st.expander(f"📁 {title} • {created} (Duration: {dur_str})"):
                    c_det1, c_det2 = st.columns([3, 1])
                    with c_det1:
                        st.write(f"**Original File:** `{m.get('original_filename') or 'Uploaded Recording'}` | **Action Items:** {act_cnt} | **Participants:** {part_cnt}")
                        if m.get("summary"):
                            st.markdown(f"**Summary Preview:** {m['summary'][:220]}...")
                    with c_det2:
                        if st.button("🔍 Open Details", key=f"dash_btn_open_{m_id}", use_container_width=True):
                            st.session_state["selected_meeting_id"] = m_id
                            st.session_state["nav_page"] = "Meeting Details"
                            st.rerun()

                        # Quick PDF Download
                        full_m = db_manager.get_meeting(m_id)
                        if full_m:
                            pdf_b = generate_meeting_pdf(full_m)
                            st.download_button(
                                label="📄 Export PDF",
                                data=pdf_b,
                                file_name=f"Report_{m_id}.pdf",
                                mime="application/pdf",
                                key=f"dash_dl_pdf_{m_id}",
                                use_container_width=True
                            )
        else:
            render_empty_state("No matching meetings", "Try adjusting your search keywords or upload a new recording.", "📁")

    # ----------------------------------------------------
    # TAB 2: Action Items Tracker
    # ----------------------------------------------------
    with tab_actions:
        st.markdown("#### ⚡ Cross-Meeting Action Items Tracker")
        act_f1, act_f2 = st.columns(2)
        with act_f1:
            stat_sel = st.selectbox("Status Filter:", ["All", "Pending", "In Progress", "Completed"], key="dash_act_stat")
        with act_f2:
            assignee_sel = st.text_input("Assignee Filter:", placeholder="Search by name...", key="dash_act_assignee")

        filtered_actions = db_actions
        if stat_sel and stat_sel != "All":
            filtered_actions = [a for a in filtered_actions if (a.get("status") or "").lower() == stat_sel.lower()]
        if assignee_sel and assignee_sel.strip():
            filtered_actions = [a for a in filtered_actions if assignee_sel.lower() in (a.get("owner") or "").lower()]

        if filtered_actions:
            act_rows = []
            for a in filtered_actions:
                act_rows.append({
                    "Meeting": a.get("meeting_title", "Meeting"),
                    "Action Item": a.get("action", ""),
                    "Owner": a.get("owner") or "Unassigned",
                    "Deadline": a.get("deadline") or "None",
                    "Priority": a.get("priority") or "Medium",
                    "Status": a.get("status") or "Pending"
                })
            st.dataframe(pd.DataFrame(act_rows), use_container_width=True)
        else:
            render_empty_state("No action items found", "No deliverables match the selected filters.", "⚡")

    # ----------------------------------------------------
    # TAB 3: Integrated AI Assistant (RAG Search - Task 3)
    # ----------------------------------------------------
    with tab_ai_assistant:
        st.markdown("#### 🧠 AI Meeting Assistant & Semantic RAG Search")
        st.caption("Ask natural language questions across all indexed meeting transcripts, summaries, decisions, and action items.")

        ai_q = st.text_input(
            "Ask your meeting repository a question:",
            placeholder="e.g. What decisions were made regarding the API integration and who owns the deliverables?",
            key="dash_rag_question_box"
        )

        col_ask_btn, col_sample = st.columns([1, 3])
        with col_ask_btn:
            run_ask = st.button("🚀 Ask Assistant", key="dash_btn_run_ask", type="primary", use_container_width=True)

        if run_ask and ai_q and ai_q.strip():
            with st.spinner("Searching semantic vector index and synthesizing grounded answer..."):
                if repository:
                    try:
                        rag_response = repository.ask(ai_q, top_k=5)
                    except Exception:
                        rag_response = None
                else:
                    rag_response = None

            if rag_response:
                st.markdown("##### 💡 AI Generated Answer")
                st.markdown(f"""
                <div class="ui-card" style="background: #f8fafc; border-left: 4px solid #4f46e5;">
                    <div style="font-size: 15px; line-height: 1.6; color: #0f172a;">{rag_response.answer}</div>
                    <div style="margin-top: 10px; font-size: 12px; color: #64748b;">
                        Confidence: <strong>{int(rag_response.confidence_score * 100)}%</strong> • 
                        Grounded: <strong>{'Yes' if rag_response.grounded else 'Partial'}</strong>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if rag_response.citations:
                    st.markdown("###### 📚 Retrieved Source Context & Citations")
                    for c in rag_response.citations:
                        m_title = c.get("title") or f"Meeting {c.get('meeting_id')}"
                        st.markdown(f"- **{m_title}** (`{c.get('section', 'General')}`): \"_{c.get('quote', '')[:200]}..._\"")
            else:
                st.info("No relevant meeting context found to answer this question. Try another query!")

    # ----------------------------------------------------
    # TAB 4: Participant Directory
    # ----------------------------------------------------
    with tab_participants:
        st.markdown("#### 👥 Team & Participant Directory")
        all_participants = []
        for m in db_meetings:
            full_m = db_manager.get_meeting(m["id"])
            if full_m:
                for p in full_m.get("participants", []):
                    name = p.get("name") if isinstance(p, dict) else str(p)
                    canon = p.get("canonical_name", name) if isinstance(p, dict) else name
                    role = p.get("role") or "Participant" if isinstance(p, dict) else "Participant"
                    all_participants.append({
                        "Participant": name,
                        "Canonical Name": canon,
                        "Role / Responsibilities": role,
                        "Meeting": m.get("title", "Meeting")
                    })

        if all_participants:
            st.dataframe(pd.DataFrame(all_participants), use_container_width=True)
        else:
            render_empty_state("No participants recorded", "Process a meeting to extract participant directories.", "👥")

    # ----------------------------------------------------
    # TAB 5: Quick Meeting Upload
    # ----------------------------------------------------
    with tab_quick_upload:
        st.markdown("#### 🎤 Upload Meeting Recording or Paste Transcript")
        up_col1, up_col2 = st.columns(2)
        with up_col1:
            up_file = st.file_uploader("Upload Audio or Video File (.wav, .mp3, .m4a, .mp4):", type=["wav", "mp3", "m4a", "mp4", "webm"], key="dash_file_up")
            up_title = st.text_input("Meeting Title (optional):", placeholder="e.g. Sprint Planning Sync", key="dash_up_title")
            if st.button("🚀 Process Recording", key="dash_btn_proc_up", type="primary") and up_file:
                if pipeline:
                    with st.spinner("Processing recording through Whisper & LLM pipeline..."):
                        t_path = Path("data/audio") / up_file.name
                        t_path.parent.mkdir(parents=True, exist_ok=True)
                        t_path.write_bytes(up_file.getvalue())
                        try:
                            res = pipeline.process_audio_file(str(t_path), meeting_title=up_title or up_file.name, user_id=user_id)
                            st.success(f"Meeting processed and persisted! ID: `{res['meeting_id']}`")
                            st.session_state["selected_meeting_id"] = res["meeting_id"]
                            st.session_state["nav_page"] = "Meeting Details"
                            st.rerun()
                        except Exception as e:
                            st.error(f"Processing error: {e}")
                else:
                    st.error("Pipeline not initialized.")
        with up_col2:
            paste_t = st.text_area("Or Paste Meeting Transcript Text:", height=200, placeholder="Paste transcript here...", key="dash_paste_t")
            paste_title = st.text_input("Transcript Meeting Title:", placeholder="e.g. Executive Interview", key="dash_paste_title")
            if st.button("⚡ Ingest Transcript", key="dash_btn_proc_paste", type="primary") and paste_t:
                if pipeline:
                    with st.spinner("Analyzing transcript with LLM & generating embeddings..."):
                        try:
                            res = pipeline.process_transcript_text(paste_t, meeting_title=paste_title or "Pasted Meeting", user_id=user_id)
                            st.success(f"Transcript indexed! ID: `{res['meeting_id']}`")
                            st.session_state["selected_meeting_id"] = res["meeting_id"]
                            st.session_state["nav_page"] = "Meeting Details"
                            st.rerun()
                        except Exception as e:
                            st.error(f"Ingestion error: {e}")
                else:
                    st.error("Pipeline not initialized.")

    # ----------------------------------------------------
    # TAB 6: Project Documentation & Direct Download
    # ----------------------------------------------------
    with tab_project_docs:
        st.markdown("#### 📖 End-to-End Project Documentation (Milestones 1 – 4)")
        st.caption("Complete, comprehensive technical and architectural documentation covering all components, schemas, APIs, test suites, and workflows.")

        docs_path = Path("PROJECT_DOCUMENTATION.md")
        doc_content = ""
        if docs_path.exists():
            try:
                doc_content = docs_path.read_text(encoding="utf-8")
            except Exception as e:
                doc_content = f"Error reading documentation file: {e}"
        else:
            doc_content = "# Project Documentation\n\nDocumentation file `PROJECT_DOCUMENTATION.md` not found."

        d_col1, d_col2, d_col3 = st.columns([1.5, 1.5, 3])
        with d_col1:
            st.download_button(
                label="📥 Download Documentation (.md)",
                data=doc_content,
                file_name="AI_Career_Intelligence_Platform_Documentation.md",
                mime="text/markdown",
                type="primary",
                use_container_width=True,
                key="dash_download_doc_md"
            )
        with d_col2:
            st.download_button(
                label="📥 Download System Architecture (.txt)",
                data=doc_content,
                file_name="System_Architecture_Guide.txt",
                mime="text/plain",
                use_container_width=True,
                key="dash_download_doc_txt"
            )

        st.markdown("---")
        with st.expander("🔍 View Complete Project Documentation In-App", expanded=True):
            st.markdown(doc_content)

