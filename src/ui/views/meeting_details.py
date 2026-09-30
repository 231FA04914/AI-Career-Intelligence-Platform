"""
Meeting Details & Analytics View (Milestone 4 - Task 2)
Flow:
Meeting Selection -> Meeting Details -> Transcript -> Summary -> Decisions -> Action Items -> Responsibilities -> Deadlines -> Participants -> Analytics.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, Any, List

from src.database import DatabaseManager
from src.reports.exporter import generate_meeting_pdf, generate_meeting_csv
from src.ui.components import (
    render_header,
    render_kpi_card,
    render_empty_state,
    render_priority_badge,
    render_status_badge
)


def render_meeting_details_view(db_manager: DatabaseManager, user_id: Optional[str] = None):
    """
    Render the comprehensive Meeting Details & Analytics Page.
    """
    render_header(
        title="Meeting Details & Executive Analytics",
        subtitle="Deep dive into transcripts, summaries, decisions, assigned responsibilities, deadlines, and contribution analytics.",
        badge_text="Milestone 4: Meeting Intelligence Details",
        badge_color="#4f46e5"
    )

    # 1. Fetch accessible meetings
    meetings = db_manager.get_all_meetings(user_id=user_id)

    if not meetings:
        render_empty_state(
            title="No meetings found in database",
            description="Process an audio recording or paste a transcript to view meeting details.",
            icon="📁"
        )
        return

    # 2. Meeting Selection Dropdown & Quick Search
    st.markdown("### 🎯 Select Meeting")
    
    # Check if a specific meeting was pre-selected in session state
    preselected_id = st.session_state.get("selected_meeting_id")
    meeting_options = {
        m["id"]: f"{m.get('title', 'Untitled')} (ID: {m['id']}) • {str(m.get('created_at', ''))[:10]}"
        for m in meetings
    }

    selected_index = 0
    if preselected_id and preselected_id in meeting_options:
        selected_index = list(meeting_options.keys()).index(preselected_id)

    col_sel, col_exp = st.columns([3, 1])
    with col_sel:
        chosen_meeting_id = st.selectbox(
            "Select Meeting:",
            options=list(meeting_options.keys()),
            format_func=lambda mid: meeting_options[mid],
            index=selected_index,
            key="details_meeting_selector"
        )

    # Fetch complete details for the selected meeting
    meeting = db_manager.get_meeting(chosen_meeting_id, user_id=user_id)
    if not meeting:
        st.error("Could not retrieve details for the selected meeting.")
        return

    # Update session state
    st.session_state["selected_meeting_id"] = chosen_meeting_id

    # Export Buttons
    with col_exp:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            pdf_data = generate_meeting_pdf(meeting)
            st.download_button(
                label="📄 PDF",
                data=pdf_data,
                file_name=f"Report_{chosen_meeting_id}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        with btn_col2:
            csv_data = generate_meeting_csv(meeting)
            st.download_button(
                label="📊 CSV",
                data=csv_data,
                file_name=f"Report_{chosen_meeting_id}.csv",
                mime="text/csv",
                use_container_width=True
            )

    st.markdown("---")

    # 3. Meeting Information & Overview KPIs
    created_at = meeting.get("created_at") or "Unknown"
    duration_s = float(meeting.get("duration") or 0.0)
    dur_formatted = f"{int(duration_s // 60)}m {int(duration_s % 60)}s" if duration_s else "N/A"
    orig_file = meeting.get("original_filename") or "Manual / Transcript Upload"
    action_items = meeting.get("action_items") or []
    decisions = meeting.get("decisions") or []
    participants = meeting.get("participants") or []
    transcript_text = meeting.get("transcript") or meeting.get("transcript_text") or ""
    summary_text = meeting.get("summary") or ""

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        render_kpi_card("Meeting Date", created_at[:10] if created_at else "N/A", "Recorded session", "📅", "#eef2ff")
    with k2:
        render_kpi_card("Duration", dur_formatted, "Total recording length", "⏱️", "#ecfdf5")
    with k3:
        render_kpi_card("Action Items", len(action_items), "Tracked commitments", "⚡", "#fef3c7")
    with k4:
        render_kpi_card("Key Decisions", len(decisions), "Strategic alignments", "🎯", "#fdf4ff")
    with k5:
        render_kpi_card("Participants", len(participants), "Identified contributors", "👥", "#f0fdf4")

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # 4. Sequential Flow Tabs:
    # Meeting Selection -> Meeting Details -> Transcript -> Summary -> Decisions -> Action Items -> Analytics
    t_overview, t_transcript, t_summary, t_decisions, t_actions, t_participants, t_analytics = st.tabs([
        "📋 Meeting Details",
        "🎙️ Transcript",
        "📑 Summary",
        "🎯 Decisions",
        "⚡ Action Items & Deadlines",
        "👥 Participants",
        "📊 Meeting Analytics"
    ])

    # Tab 1: Meeting Details Overview
    with t_overview:
        st.markdown(f"#### 📌 {meeting.get('title', 'Meeting Overview')}")
        st.markdown(f"""
        <div class="ui-card">
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px;">
                <div><strong>Meeting ID:</strong> <code>{meeting['id']}</code></div>
                <div><strong>Source File:</strong> <code>{orig_file}</code></div>
                <div><strong>Recorded On:</strong> {created_at}</div>
                <div><strong>Owner / Tenant:</strong> {meeting.get('user_id') or 'Shared / Default'}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        st.markdown("##### 💡 Executive Summary Preview")
        st.info(summary_text or "No executive summary available.")

    # Tab 2: Transcript Viewer
    with t_transcript:
        st.markdown("#### 🎙️ Full Meeting Transcript")
        col_t_search, col_t_copy = st.columns([3, 1])
        with col_t_search:
            t_search = st.text_input("🔍 Search within transcript:", placeholder="Type keywords...", key="t_search_box")
        with col_t_copy:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            word_count = len(transcript_text.split())
            st.caption(f"**Word Count:** {word_count} words")

        if t_search and t_search.strip():
            matched_lines = [l for l in transcript_text.split('\n') if t_search.lower() in l.lower()]
            st.markdown(f"**Search matches ({len(matched_lines)}):**")
            for ml in matched_lines[:10]:
                st.markdown(f"- ...{ml.strip()}...")
            st.markdown("---")

        st.text_area(
            "Transcript Text",
            value=transcript_text,
            height=380,
            disabled=True,
            label_visibility="collapsed"
        )

    # Tab 3: Summary Viewer
    with t_summary:
        st.markdown("#### 📑 Executive Intelligence Summary")
        if summary_text:
            st.markdown(f"""
            <div class="ui-card" style="font-size: 15px; line-height: 1.6; color: #1e293b; background: #faf5ff; border: 1px solid #e9d5ff;">
                {summary_text.replace(chr(10), '<br/><br/>')}
            </div>
            """, unsafe_allow_html=True)
        else:
            render_empty_state("No summary available", "Summary generation was not completed for this session.", "📑")

    # Tab 4: Key Decisions Viewer
    with t_decisions:
        st.markdown("#### 🎯 Key Decisions Agreed Upon")
        if decisions:
            for idx, dec in enumerate(decisions, 1):
                st.markdown(f"""
                <div class="ui-card" style="margin-bottom: 8px; border-left: 4px solid #10b981;">
                    <div style="font-weight: 700; color: #065f46; font-size: 13px;">Decision #{idx}</div>
                    <div style="font-size: 14.5px; color: #1e293b; margin-top: 4px;">{dec}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            render_empty_state("No decisions recorded", "No formal decisions were extracted from this conversation.", "🎯")

    # Tab 5: Action Items, Responsibilities & Deadlines
    with t_actions:
        st.markdown("#### ⚡ Action Items, Responsibilities & Deadlines")
        if action_items:
            # Table visualization
            table_rows = []
            for a in action_items:
                table_rows.append({
                    "Action Item": a.get("action", ""),
                    "Assignee": a.get("owner") or "Unassigned",
                    "Deadline": a.get("deadline") or "None",
                    "Priority": a.get("priority") or "Medium",
                    "Status": a.get("status") or "Pending"
                })
            df = pd.DataFrame(table_rows)
            st.dataframe(df, use_container_width=True)

            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            st.markdown("##### 📅 Action Item Cards & Status Management")
            for item in action_items:
                with st.container():
                    a_id = item.get("id") or item.get("action")[:10]
                    c_act1, c_act2, c_act3, c_act4 = st.columns([3, 1, 1, 1])
                    with c_act1:
                        st.markdown(f"**{item.get('action')}**")
                        st.caption(f"👤 Assigned to: **{item.get('owner') or 'Unassigned'}**")
                    with c_act2:
                        st.markdown(f"⏰ `{item.get('deadline') or 'No deadline'}`")
                    with c_act3:
                        render_priority_badge(item.get("priority") or "Medium")
                    with c_act4:
                        curr_status = item.get("status") or "Pending"
                        status_opts = ["Pending", "In Progress", "Completed"]
                        stat_idx = status_opts.index(curr_status) if curr_status in status_opts else 0
                        new_stat = st.selectbox(
                            "Status",
                            options=status_opts,
                            index=stat_idx,
                            key=f"act_status_{a_id}",
                            label_visibility="collapsed"
                        )
                        if new_stat != curr_status and item.get("id"):
                            db_manager.update_action_item_status(item["id"], new_stat)
                            st.rerun()
                    st.divider()
        else:
            render_empty_state("No action items found", "No deliverables were extracted for this meeting.", "⚡")

    # Tab 6: Participants & Roles
    with t_participants:
        st.markdown("#### 👥 Meeting Participants & Roles")
        if participants:
            cols = st.columns(len(participants) if len(participants) <= 3 else 3)
            for idx, p in enumerate(participants):
                col_target = cols[idx % len(cols)]
                with col_target:
                    name = p.get("name") if isinstance(p, dict) else str(p)
                    canon = p.get("canonical_name", name) if isinstance(p, dict) else name
                    role = p.get("role") or "Participant" if isinstance(p, dict) else "Participant"
                    st.markdown(f"""
                    <div class="ui-card" style="text-align: center; margin-bottom: 12px;">
                        <div style="font-size: 32px; margin-bottom: 6px;">👤</div>
                        <div style="font-weight: 700; font-size: 15px; color: #0f172a;">{name}</div>
                        <div style="font-size: 12px; color: #64748b; margin-bottom: 6px;">Alias: {canon}</div>
                        <div style="background: #eef2ff; color: #4f46e5; padding: 3px 8px; border-radius: 6px; font-size: 12px; display: inline-block;">{role}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            render_empty_state("No participants mapped", "No individual participant profiles were identified.", "👥")

    # Tab 7: Meeting Analytics
    with t_analytics:
        st.markdown("#### 📊 Meeting Intelligence Analytics")
        an_col1, an_col2 = st.columns(2)

        with an_col1:
            st.markdown("##### 📈 Action Item Priority Distribution")
            prio_counts = {"High": 0, "Medium": 0, "Low": 0}
            for a in action_items:
                p = a.get("priority") or "Medium"
                prio_counts[p] = prio_counts.get(p, 0) + 1
            prio_df = pd.DataFrame(list(prio_counts.items()), columns=["Priority", "Count"])
            st.bar_chart(prio_df.set_index("Priority"), color="#4f46e5")

        with an_col2:
            st.markdown("##### 👥 Participant Workload Breakdown")
            workload = {}
            for a in action_items:
                owner = a.get("owner") or "Unassigned"
                workload[owner] = workload.get(owner, 0) + 1
            if workload:
                work_df = pd.DataFrame(list(workload.items()), columns=["Assignee", "Tasks"])
                st.bar_chart(work_df.set_index("Assignee"), color="#10b981")
            else:
                st.caption("No task assignments to chart.")

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        st.markdown("##### ⏱️ Engagement & Meeting Density Summary")
        d1, d2, d3 = st.columns(3)
        with d1:
            st.metric("Total Duration", f"{duration_s:.1f}s")
        with d2:
            rate = f"{(len(action_items) / (duration_s / 60)):.2f} / min" if duration_s > 0 else "N/A"
            st.metric("Task Density", rate)
        with d3:
            dec_rate = f"{(len(decisions) / (duration_s / 60)):.2f} / min" if duration_s > 0 else "N/A"
            st.metric("Decision Density", dec_rate)
