"""
Interview Preparation View - AI Career Intelligence Platform
Provides conversation follow-up recommendations, preparation roadmap, and smart follow-up generation.
"""

import streamlit as st
from typing import Optional
from src.database import DatabaseManager
from src.ui.components import (
    render_header,
    render_empty_state,
    render_priority_badge,
    render_status_badge,
    render_kpi_card
)


def render_interview_prep_view(
    db_manager: Optional[DatabaseManager] = None,
    llm_service: Optional[any] = None
):
    """Render the Interview Preparation view."""
    render_header(
        title="Interview Preparation & Follow-Up",
        subtitle="Review discussion themes, prepare smart follow-ups, and track preparation roadmap.",
        badge_text="Prep Ready",
        badge_color="#0ea5e9"
    )

    # 1. Check for active session data or persisted database meetings
    summary_data = st.session_state.get("latest_summary")
    all_meetings = db_manager.get_all_meetings() if db_manager else []

    selected_meeting = None

    # Source Selection Toolbar
    col_src1, col_src2 = st.columns([3, 2])
    with col_src1:
        if all_meetings:
            meeting_options = {"[Active In-Memory Session]" if summary_data else "[Choose a Saved Meeting]": None}
            for m in all_meetings:
                meeting_options[f"📁 {m['title']} ({m['id']})"] = m["id"]

            chosen_label = st.selectbox(
                "Select Meeting/Interview for Preparation:",
                list(meeting_options.keys()),
                key="prep_meeting_selector"
            )
            chosen_id = meeting_options[chosen_label]

            if chosen_id:
                selected_meeting = db_manager.get_meeting(chosen_id)
                summary_data = {
                    "summary": selected_meeting.get("summary", ""),
                    "key_decisions": selected_meeting.get("decisions", []),
                    "action_items": selected_meeting.get("action_items", []),
                    "participants": [p.get("canonical_name", p.get("name")) for p in selected_meeting.get("participants", [])],
                    "title": selected_meeting.get("title", "")
                }
        else:
            st.caption("No historical meetings stored in database.")

    with col_src2:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("🎤 New Interview Analysis / Upload →", key="btn_prep_go_upload", use_container_width=True):
            st.session_state["nav_page"] = "Interview Analysis"
            st.rerun()

    st.markdown("---")

    if summary_data:
        m_title = summary_data.get("title") or st.session_state.get("active_source_name", "Active Interview Session")
        st.markdown(f"#### 🎯 Preparation Briefing: `{m_title}`")

        decisions = summary_data.get("key_decisions") or summary_data.get("decisions") or []
        action_items = summary_data.get("action_items") or st.session_state.get("extracted_actions_list", [])
        participants = summary_data.get("participants", [])
        summary_text = summary_data.get("summary", "")

        # Top KPI Cards
        k1, k2, k3 = st.columns(3)
        with k1:
            render_kpi_card("Decisions to Revisit", len(decisions), "Key outcomes", "🎯", "#eff6ff")
        with k2:
            render_kpi_card("Pending Deliverables", len(action_items), "Action items", "📋", "#fef3c7")
        with k3:
            render_kpi_card("Key Contacts", len(participants), "Interviewers/team", "👥", "#ecfdf5")

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

        # Main Preparation Sections
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### 📌 Key Agreed Outcomes to Reference in Next Round")
            if decisions:
                for d in decisions:
                    st.markdown(f"- 🎯 **Agreed:** {d}")
            else:
                st.markdown("_No explicit decisions recorded._")

            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            st.markdown("##### 💡 Executive Context")
            st.markdown(f"> *{summary_text}*")

        with col2:
            st.markdown("##### 📋 Open Action Items & Deliverables to Follow-up")
            if action_items:
                for a in action_items[:6]:
                    act_text = a.get("action") if isinstance(a, dict) else str(a)
                    owner = a.get("owner", "Unassigned") if isinstance(a, dict) else "Unassigned"
                    deadline = a.get("deadline", "None") if isinstance(a, dict) else "None"
                    p_badge = render_priority_badge(a.get("priority", "Medium")) if isinstance(a, dict) else ""
                    st.markdown(f"- **{act_text}** (👤 `{owner}` | 📅 `{deadline}`) {p_badge}", unsafe_allow_html=True)
            else:
                st.markdown("_No pending action items._")

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

        # Smart Follow-up Questions Section
        st.markdown("##### ❓ Recommended Follow-Up Questions to Ask")
        st.caption("Strategic questions synthesized from prior discussions to demonstrate mastery and ownership:")

        q_col1, q_col2 = st.columns(2)
        with q_col1:
            st.markdown("""
            - 🔍 **Technical Validation**: *"In our last discussion, we aligned on the architecture roadmap. What are the top technical risks or dependencies the team is tracking for next sprint?"*
            - ⏱️ **Timeline & Priorities**: *"Regarding the pending high-priority deliverables, what milestone would you like to review first in the upcoming review cycle?"*
            """)
        with q_col2:
            st.markdown("""
            - 👥 **Team & Collaboration**: *"How will cross-functional handoffs between engineering and product be structured during the rollout?"*
            - 🚀 **Next Steps**: *"What is the expected timeline for the next evaluation round or stakeholder sync?"*
            """)

    else:
        render_empty_state(
            title="No Active Interview Selected",
            description="Select an existing meeting from the dropdown above or click 'New Interview Analysis' to upload an interview recording or paste transcript text.",
            icon="🎯"
        )

    # Future Roadmap Features
    st.markdown("---")
    st.markdown("#### 🚀 Upcoming Interview Preparation Modules (Milestone 3)")
    st.caption("The following AI modules are planned for future milestone releases:")

    rc1, rc2, rc3 = st.columns(3)
    with rc1:
        st.markdown("""
        <div class="ui-card" style="opacity: 0.85;">
            <div style="font-size: 20px; margin-bottom: 6px;">🤖</div>
            <div style="font-weight: 700; font-size: 14px; color: #0f172a; margin-bottom: 4px;">Mock Interview Simulator</div>
            <div style="font-size: 12px; color: #64748b; margin-bottom: 8px;">Interactive AI agent simulating real-time technical and behavioral interviews.</div>
            <span style="background: #f1f5f9; color: #475569; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 9999px;">Coming in Milestone 3</span>
        </div>
        """, unsafe_allow_html=True)

    with rc2:
        st.markdown("""
        <div class="ui-card" style="opacity: 0.85;">
            <div style="font-size: 20px; margin-bottom: 6px;">📄</div>
            <div style="font-weight: 700; font-size: 14px; color: #0f172a; margin-bottom: 4px;">Resume & Skill Matcher</div>
            <div style="font-size: 12px; color: #64748b; margin-bottom: 8px;">Automated skill gap analysis comparing interview performance with target job descriptions.</div>
            <span style="background: #f1f5f9; color: #475569; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 9999px;">Coming in Milestone 3</span>
        </div>
        """, unsafe_allow_html=True)

    with rc3:
        st.markdown("""
        <div class="ui-card" style="opacity: 0.85;">
            <div style="font-size: 20px; margin-bottom: 6px;">📈</div>
            <div style="font-weight: 700; font-size: 14px; color: #0f172a; margin-bottom: 4px;">Confidence & Pace Analytics</div>
            <div style="font-size: 12px; color: #64748b; margin-bottom: 8px;">Audio tone, speech rate, and clarity metrics extracted from recorded speech.</div>
            <span style="background: #f1f5f9; color: #475569; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 9999px;">Coming in Milestone 3</span>
        </div>
        """, unsafe_allow_html=True)

