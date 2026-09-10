"""
Database Archive View - AI Career Intelligence Platform (Milestone 2 - Task 5)
Manages SQLite persisted meetings, cross-meeting action item tracker, and JSON summaries archive.
"""

import streamlit as st
from pathlib import Path
from src.ui.components import render_header, render_kpi_card, render_empty_state, render_priority_badge, render_status_badge


def render_database_archive_view(db_manager, summary_manager, meeting_summarizer):
    """Render the SQLite Database and Meeting Archive view."""
    render_header(
        title="Relational Database & Meeting Archive",
        subtitle="SQLite database repository storing complete meeting entities, summaries, decisions, action items, and participants.",
        badge_text="SQLite Connected",
        badge_color="#10b981"
    )

    db_meetings = db_manager.get_all_meetings() if db_manager else []
    all_db_actions = db_manager.get_all_action_items() if db_manager else []

    # KPI Metrics Header
    col_k1, col_k2 = st.columns(2)
    with col_k1:
        render_kpi_card(
            title="Total Persisted Meetings",
            value=len(db_meetings),
            subtitle="Meetings stored in SQLite",
            icon="🏛️",
            icon_bg="#eef2ff"
        )
    with col_k2:
        render_kpi_card(
            title="Total Stored Action Items",
            value=len(all_db_actions),
            subtitle="Tasks tracked across all meetings",
            icon="📋",
            icon_bg="#fef3c7"
        )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # 3 Main Archive Tabs
    tab_meetings, tab_actions, tab_json = st.tabs([
        "🏛️ Persisted Meetings Archive",
        "📋 Cross-Meeting Action Tracker",
        "📑 JSON Summaries Archive"
    ])

    # ----------------------------------------------------
    # TAB 1: Persisted Meetings Archive
    # ----------------------------------------------------
    with tab_meetings:
        st.markdown("##### 📁 Saved Meeting Records")
        st.caption("Expand any meeting record to view executive summaries, key decisions, extracted tasks, and mapped attendees.")

        if db_meetings:
            for m in db_meetings:
                with st.expander(f"📁 {m['title']} (ID: {m['id']}) • {m['created_at'][:19]}"):
                    full_m = db_manager.get_meeting(m['id'])
                    if full_m:
                        st.write(f"📄 **Original File:** `{full_m.get('original_filename') or 'Pasted Transcript'}` | ⏱️ **Duration:** `{full_m.get('duration', 0):.1f}s`")

                        # Summary
                        st.markdown("###### 📄 Executive Summary")
                        st.write(full_m.get("summary") or "_No summary available._")

                        # Key Decisions
                        if full_m.get("decisions"):
                            st.markdown("###### 🎯 Key Decisions")
                            for dec in full_m["decisions"]:
                                st.markdown(f"- {dec}")

                        # Action Items
                        if full_m.get("action_items"):
                            st.markdown(f"###### 📋 Action Items ({len(full_m['action_items'])})")
                            for act in full_m["action_items"]:
                                pri_badge = render_priority_badge(act.get("priority"))
                                stat_badge = render_status_badge(act.get("status"))
                                owner_str = act.get('owner') or 'Unassigned'
                                due_str = act.get('deadline') or 'None'
                                st.markdown(f"- **{act['action']}** (👤 `{owner_str}` | 📅 Due: `{due_str}`) {pri_badge} {stat_badge}", unsafe_allow_html=True)

                        # Participants
                        if full_m.get("participants"):
                            st.markdown(f"###### 👥 Participants ({len(full_m['participants'])})")
                            p_names = [p['canonical_name'] for p in full_m['participants']]
                            st.write(", ".join(p_names))

                        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

                        # Action Buttons
                        col_btn1, col_btn2, _ = st.columns([2, 2, 3])
                        with col_btn1:
                            if st.button(f"📋 Load into Active Workspace", key=f"db_load_btn_{m['id']}", type="primary"):
                                st.session_state["active_transcript"] = full_m.get("transcript_text", "")
                                st.session_state["active_source_name"] = full_m.get("title", "Meeting")
                                st.session_state["latest_summary"] = {
                                    "summary": full_m.get("summary", ""),
                                    "key_decisions": full_m.get("decisions", []),
                                    "action_items": full_m.get("action_items", [])
                                }
                                st.session_state["extracted_actions_list"] = full_m.get("action_items", [])
                                st.session_state["mapped_participants_list"] = full_m.get("participants", [])
                                st.success(f"Loaded '{m['title']}' into workspace!")
                                st.session_state["nav_page"] = "AI Insights"
                                st.rerun()

                        with col_btn2:
                            if st.button("🗑️ Delete Record", key=f"db_del_btn_{m['id']}"):
                                db_manager.delete_meeting(m['id'])
                                st.success("Meeting record deleted.")
                                st.rerun()
        else:
            render_empty_state(
                title="No Meetings Persisted in Database",
                description="Process an audio/video recording or click 'Save to Database' in AI Insights to store records here.",
                icon="🗄️"
            )

    # ----------------------------------------------------
    # TAB 2: Cross-Meeting Action Tracker
    # ----------------------------------------------------
    with tab_actions:
        st.markdown("##### 📋 Multi-Meeting Action Items Tracker")
        st.caption("View, filter, and manage commitments across all meetings saved in the database.")

        if all_db_actions:
            act_f1, act_f2 = st.columns(2)
            with act_f1:
                status_filter = st.selectbox("Filter DB Tasks by Status:", ["All", "Pending", "In Progress", "Completed", "Blocked"], key="db_filter_status_view")
            with act_f2:
                owners_list = ["All"] + sorted(list({a['owner'] for a in all_db_actions if a.get('owner')}))
                owner_filter = st.selectbox("Filter DB Tasks by Assignee:", owners_list, key="db_filter_owner_view")

            filtered_actions = db_manager.get_all_action_items(status=status_filter, owner=owner_filter)
            st.markdown(f"**Showing {len(filtered_actions)} of {len(all_db_actions)} total action items:**")

            for idx, item in enumerate(filtered_actions):
                with st.container():
                    c_info, c_stat, c_val = st.columns([4, 2, 2])
                    with c_info:
                        p_badge = render_priority_badge(item.get('priority'))
                        st.markdown(f"**{idx+1}. {item['action']}** {p_badge}", unsafe_allow_html=True)
                        st.caption(f"📁 Meeting: **{item.get('meeting_title')}** | 👤 Assignee: **{item.get('owner') or 'Unassigned'}** | 📅 Due: **{item.get('deadline') or 'None'}**")

                    with c_stat:
                        cur_stat = item.get('status', 'Pending')
                        cur_idx = ["Pending", "In Progress", "Completed", "Blocked"].index(cur_stat) if cur_stat in ["Pending", "In Progress", "Completed", "Blocked"] else 0
                        new_stat = st.selectbox(
                            "Status",
                            ["Pending", "In Progress", "Completed", "Blocked"],
                            index=cur_idx,
                            key=f"db_item_stat_{item['id']}_{idx}",
                            label_visibility="collapsed"
                        )
                        if new_stat != cur_stat:
                            db_manager.update_action_item_status(item['id'], new_stat)
                            st.rerun()

                    with c_val:
                        stat_html = render_status_badge(item.get('status'))
                        st.markdown(stat_html, unsafe_allow_html=True)

                    st.markdown("<div style='border-bottom: 1px solid #f1f5f9; margin: 8px 0;'></div>", unsafe_allow_html=True)
        else:
            render_empty_state(
                title="No Action Items Stored",
                description="Persist meetings with extracted action items to manage cross-meeting tasks.",
                icon="⚡"
            )

    # ----------------------------------------------------
    # TAB 3: JSON Summaries Archive
    # ----------------------------------------------------
    with tab_json:
        st.markdown("##### 📑 JSON Summaries Archive")
        st.caption("Browse and review saved JSON summary files stored on disk.")

        saved_summaries = summary_manager.list_summaries() if summary_manager else []
        if saved_summaries:
            for s_path in saved_summaries:
                with st.expander(f"📑 {s_path.name}"):
                    try:
                        s_data = summary_manager.load_summary(str(s_path))
                        st.caption(f"Source: `{s_data.get('source_name')}` | Created: `{s_data.get('created_at', 'N/A')}`")
                        st.markdown(meeting_summarizer.format_markdown(s_data.get("data", {})))

                        col_del, _ = st.columns([1, 5])
                        with col_del:
                            if st.button("🗑️ Delete JSON", key=f"del_json_{s_path.name}"):
                                summary_manager.delete_summary(str(s_path))
                                st.success(f"Deleted {s_path.name}")
                                st.rerun()
                    except Exception as e:
                        st.error(f"Error loading summary: {e}")
        else:
            render_empty_state(
                title="No JSON Summaries Archived",
                description="Click 'Save to Summary Archive' in AI Insights to store JSON summaries on disk.",
                icon="📑"
            )
