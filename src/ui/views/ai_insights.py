"""
AI Insights View - AI Career Intelligence Platform
Comprehensive presentation of Executive Summary, Key Decisions, Action Items, and Responsibility Matrix.
"""

import streamlit as st
import json
from pathlib import Path
from src.ui.components import (
    render_header,
    render_empty_state,
    render_kpi_card,
    render_priority_badge,
    render_status_badge
)
from src.action_item_extractor import ExtractedActionItem
from src.participant_mapper import Participant


def render_ai_insights_view(
    meeting_summarizer,
    summary_manager,
    action_extractor,
    participant_mapper,
    db_manager
):
    """Render the AI Insights view."""
    render_header(
        title="AI Interview Intelligence",
        subtitle="Your conversation, transformed into actionable executive intelligence, tasks, and responsibility mappings.",
        badge_text="Intelligence Ready",
        badge_color="#7c3aed"
    )

    if "latest_summary" not in st.session_state or not st.session_state["latest_summary"]:
        render_empty_state(
            title="No AI Insights Generated Yet",
            description="Run an analysis on an audio/video recording or meeting transcript to generate executive summaries, decisions, and action items.",
            icon="🧠"
        )
        col_c1, col_c2, col_c3 = st.columns([1, 2, 1])
        with col_c2:
            if st.button("🚀 Start Interview Analysis →", type="primary", use_container_width=True):
                st.session_state["nav_page"] = "Interview Analysis"
                st.rerun()
        return

    summary_data = st.session_state["latest_summary"]
    source_name = st.session_state.get("active_source_name", "meeting_transcript")
    active_transcript = st.session_state.get("active_transcript", "")

    # Top Toolbar: Persistence & Multi-Format Exports
    col_t_title, col_t_db = st.columns([3, 2])
    with col_t_title:
        st.markdown(f"##### 📄 Analysis for: `{source_name}`")
    with col_t_db:
        if st.button("🗄️ Save Entire Meeting to Database (Task 5)", type="primary", use_container_width=True):
            current_actions = st.session_state.get("extracted_actions_list", summary_data.get("action_items", []))
            current_parts = st.session_state.get("mapped_participants_list", [])
            if not current_parts and summary_data.get("participants"):
                current_parts = [{"name": p, "canonical_name": p, "role": None} for p in summary_data["participants"]]

            saved_m_id = db_manager.save_meeting_intelligence(
                title=Path(source_name).stem.replace('_', ' ').title(),
                transcript_text=active_transcript,
                summary_text=summary_data.get("summary", ""),
                decisions=summary_data.get("key_decisions") or summary_data.get("decisions") or [],
                action_items=current_actions,
                participants=current_parts,
                original_filename=source_name
            )
            st.success(f"✅ Successfully persisted to SQLite Database! (Meeting ID: `{saved_m_id}`)")
            st.rerun()

    st.markdown("---")

    # Section 1: Executive Summary & Key Decisions
    col_sum1, col_sum2 = st.columns([3, 2])

    with col_sum1:
        st.markdown("#### 📋 Executive Summary")
        summary_text = summary_data.get("summary", "No executive summary available.")
        st.markdown(f"""
        <div class="ui-card" style="background: #ffffff; border-left: 4px solid #4f46e5; font-size: 15px; line-height: 1.6; color: #1e293b;">
            {summary_text}
        </div>
        """, unsafe_allow_html=True)

    with col_sum2:
        st.markdown("#### 🎯 Key Decisions")
        decisions = summary_data.get("key_decisions") or summary_data.get("decisions") or []
        if decisions:
            dec_items = "".join([f'<li style="margin-bottom: 8px; color: #1e293b;"><strong>{d}</strong></li>' for d in decisions])
            st.markdown(f"""
            <div class="ui-card" style="background: #ffffff; border-left: 4px solid #10b981;">
                <ul style="padding-left: 20px; margin: 0;">{dec_items}</ul>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("No explicit key decisions recorded in this conversation.")

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Section 2: Action Items Management Engine (Milestone 2 - Task 3)
    st.markdown("---")
    st.markdown("### ⚡ Action Items & Task Tracker")
    st.caption("High-precision task management tracking Assigned Participant, Deadline, Priority level, and Status.")

    raw_actions = st.session_state.get("extracted_actions_list", [])
    if raw_actions:
        action_objs = [ExtractedActionItem(**d) if isinstance(d, dict) else d for d in raw_actions]

        # Action KPI Metrics
        metrics = action_extractor.get_metrics(action_objs)
        m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
        with m_col1:
            render_kpi_card("Total Tasks", metrics["total"], "All Extracted", "⚡", "#eef2ff")
        with m_col2:
            render_kpi_card("High Priority", metrics["high_priority"], "Urgent", "🔥", "#fee2e2")
        with m_col3:
            render_kpi_card("Pending", metrics["pending"], "To Do", "⏳", "#f1f5f9")
        with m_col4:
            render_kpi_card("In Progress", metrics["in_progress"], "Active", "🚧", "#ede9fe")
        with m_col5:
            render_kpi_card("Completed", metrics["completed"], "Finished", "✅", "#dcfce7")

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

        # Filter & Search Controls
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)
        all_assignees = ["All", "Unassigned"] + sorted(list({i.owner for i in action_objs if i.owner}))

        with f_col1:
            sel_assignee = st.selectbox("Filter by Assignee:", all_assignees, key="ins_filter_assignee")
        with f_col2:
            sel_priority = st.selectbox("Filter by Priority:", ["All", "High", "Medium", "Low"], key="ins_filter_priority")
        with f_col3:
            sel_status = st.selectbox("Filter by Status:", ["All", "Pending", "In Progress", "Completed", "Blocked"], key="ins_filter_status")
        with f_col4:
            sel_sort = st.selectbox("Sort by:", ["Priority", "Deadline", "Assignee", "Status"], key="ins_sort_actions")

        search_query = st.text_input("🔍 Search tasks:", placeholder="Search by task description or assignee...", key="ins_search_tasks")

        # Apply filtering and sorting
        filtered_items = action_extractor.filter_items(
            action_objs,
            assignee=sel_assignee,
            priority=sel_priority,
            status=sel_status,
            search_query=search_query
        )
        sorted_items = action_extractor.sort_items(filtered_items, sort_by=sel_sort.lower())

        st.markdown(f"**Showing {len(sorted_items)} of {len(action_objs)} action items:**")

        # Task Items List
        for idx, item in enumerate(sorted_items):
            with st.container():
                c_desc, c_stat, c_del = st.columns([4, 2, 1])
                with c_desc:
                    p_badge = render_priority_badge(item.priority)
                    st.markdown(f"**{idx+1}. {item.action}** {p_badge}", unsafe_allow_html=True)
                    assignee_str = f"👤 **{item.assignee_display}**"
                    deadline_str = f"📅 Due: **{item.deadline_display}**"
                    st.caption(f"{assignee_str} • {deadline_str}")

                with c_stat:
                    current_idx = ["Pending", "In Progress", "Completed", "Blocked"].index(item.status) if item.status in ["Pending", "In Progress", "Completed", "Blocked"] else 0
                    new_status = st.selectbox(
                        "Status",
                        ["Pending", "In Progress", "Completed", "Blocked"],
                        index=current_idx,
                        key=f"ins_status_{item.id}_{idx}",
                        label_visibility="collapsed"
                    )
                    if new_status != item.status:
                        for s_dict in st.session_state["extracted_actions_list"]:
                            if s_dict["id"] == item.id:
                                s_dict["status"] = new_status
                        st.rerun()

                with c_del:
                    if st.button("🗑️", key=f"ins_del_{item.id}_{idx}", help="Remove task"):
                        st.session_state["extracted_actions_list"] = [s for s in st.session_state["extracted_actions_list"] if s["id"] != item.id]
                        st.rerun()

                st.markdown("<div style='border-bottom: 1px solid #f1f5f9; margin: 8px 0;'></div>", unsafe_allow_html=True)

    else:
        st.info("No action items extracted. Click 'Extract Action Items' or run analysis.")

    # Section 3: Participant & Responsibility Mapping (Milestone 2 - Task 4)
    st.markdown("---")
    st.markdown("### 👥 Participant & Responsibility Mapping")

    raw_parts = st.session_state.get("mapped_participants_list", [])
    if raw_parts:
        part_objs = [Participant(**d) if isinstance(d, dict) else d for d in raw_parts]
        matrix_md = participant_mapper.to_matrix_markdown(part_objs)
        st.markdown(matrix_md, unsafe_allow_html=True)

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        st.markdown("##### 👤 Individual Participant Commitments")
        for p in part_objs:
            with st.expander(f"👤 {p.canonical_name} ({p.total_tasks} Assigned Commitments)"):
                st.write(f"**Status:** `{'Identified Attendee' if p.is_known else 'Unassigned/Open'}`")
                if p.responsibilities:
                    for r in p.responsibilities:
                        d_info = f" • 📅 Due: **{r.get('deadline')}**" if r.get('deadline') else ""
                        p_info = f" • 🏷️ Priority: `{r.get('priority')}`" if r.get('priority') else ""
                        st.markdown(f"- **{r.get('action')}**{d_info}{p_info}")
                else:
                    st.markdown("_No specific follow-up tasks assigned._")
    else:
        st.info("No participant mapping available yet.")

    # Section 4: Multi-Format Export Toolbar
    st.markdown("---")
    st.markdown("#### 📥 Export Intelligence Reports")
    exp1, exp2, exp3, exp4 = st.columns(4)

    md_content = meeting_summarizer.format_markdown(summary_data)
    txt_content = meeting_summarizer.format_plain_text(summary_data)
    json_content = meeting_summarizer.export_summary(summary_data, "json")
    csv_content = action_extractor.to_csv(action_objs) if raw_actions else ""

    with exp1:
        st.download_button(
            label="📥 Download Markdown (.md)",
            data=md_content,
            file_name=f"summary_{Path(source_name).stem}.md",
            mime="text/markdown",
            use_container_width=True
        )
    with exp2:
        st.download_button(
            label="📥 Download Text (.txt)",
            data=txt_content,
            file_name=f"summary_{Path(source_name).stem}.txt",
            mime="text/plain",
            use_container_width=True
        )
    with exp3:
        st.download_button(
            label="📥 Download Tasks CSV (.csv)",
            data=csv_content,
            file_name=f"action_items_{Path(source_name).stem}.csv",
            mime="text/csv",
            use_container_width=True
        )
    with exp4:
        st.download_button(
            label="📥 Download JSON (.json)",
            data=json_content,
            file_name=f"summary_{Path(source_name).stem}.json",
            mime="application/json",
            use_container_width=True
        )
