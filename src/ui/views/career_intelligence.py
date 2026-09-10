"""
Career Intelligence View - AI Career Intelligence Platform
Synthesizes career-focused insights, communication highlights, and task velocity from analyzed interviews.
"""

import streamlit as st
from src.ui.components import render_header, render_empty_state, render_kpi_card


def render_career_intelligence_view():
    """Render the Career Intelligence analytics view."""
    render_header(
        title="Career Intelligence & Analytics",
        subtitle="Understand conversation dynamics, decision impact, and execution readiness.",
        badge_text="Career Analytics",
        badge_color="#6366f1"
    )

    if "latest_summary" not in st.session_state or not st.session_state["latest_summary"]:
        render_empty_state(
            title="No Career Intelligence Data Available",
            description="Career analytics are computed from analyzed interview transcripts. Complete an interview analysis to explore insights.",
            icon="📊"
        )
        col_c1, col_c2, col_c3 = st.columns([1, 2, 1])
        with col_c2:
            if st.button("🚀 Analyze an Interview Recording →", type="primary", use_container_width=True):
                st.session_state["nav_page"] = "Interview Analysis"
                st.rerun()
        return

    summary_data = st.session_state["latest_summary"]
    actions = st.session_state.get("extracted_actions_list", [])
    participants = st.session_state.get("mapped_participants_list", [])

    # Overview Metrics Row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_kpi_card("Key Points Covered", len(summary_data.get("key_points", [])), "Topics Analyzed", "🎯", "#eef2ff")
    with c2:
        render_kpi_card("Decisions Reached", len(summary_data.get("key_decisions") or summary_data.get("decisions") or []), "Outcomes Decided", "💡", "#f0fdf4")
    with c3:
        render_kpi_card("Action Commitments", len(actions), "Accountability Tasks", "⚡", "#fef3c7")
    with c4:
        render_kpi_card("Identified Stakeholders", len(participants), "Active Contributors", "👥", "#fdf4ff")

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Section 1: Discussion Highlights & Themes
    st.markdown("#### 🎯 Core Discussion Focus & Highlights")
    key_points = summary_data.get("key_points", [])
    if key_points:
        col_kp1, col_kp2 = st.columns(2)
        for i, kp in enumerate(key_points):
            col_target = col_kp1 if i % 2 == 0 else col_kp2
            with col_target:
                st.markdown(f"""
                <div class="ui-card" style="margin-bottom: 12px; padding: 14px 18px;">
                    <div style="font-weight: 700; color: #1e3a8a; font-size: 13.5px; margin-bottom: 4px;">Point {i+1}</div>
                    <div style="font-size: 14px; color: #334155;">{kp}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No specific discussion points categorized.")

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Section 2: Actionability & Execution Profile
    st.markdown("#### 📈 Execution & Ownership Profile")
    if actions:
        high_pri = sum(1 for a in actions if a.get("priority") == "High")
        completed = sum(1 for a in actions if a.get("status") == "Completed")
        assigned = sum(1 for a in actions if a.get("owner"))

        col_pr1, col_pr2, col_pr3 = st.columns(3)
        with col_pr1:
            st.markdown(f"""
            <div class="ui-card">
                <div style="font-size: 12px; font-weight: 700; color: #64748b; text-transform: uppercase;">Delegation Rate</div>
                <div style="font-size: 24px; font-weight: 800; color: #0f172a; margin: 4px 0;">{round((assigned/len(actions))*100 if actions else 0)}%</div>
                <div style="font-size: 12px; color: #64748b;">{assigned} of {len(actions)} tasks assigned to specific owners</div>
            </div>
            """, unsafe_allow_html=True)
        with col_pr2:
            st.markdown(f"""
            <div class="ui-card">
                <div style="font-size: 12px; font-weight: 700; color: #64748b; text-transform: uppercase;">High Priority Focus</div>
                <div style="font-size: 24px; font-weight: 800; color: #b91c1c; margin: 4px 0;">{high_pri} Tasks</div>
                <div style="font-size: 12px; color: #64748b;">Critical action items requiring immediate execution</div>
            </div>
            """, unsafe_allow_html=True)
        with col_pr3:
            st.markdown(f"""
            <div class="ui-card">
                <div style="font-size: 12px; font-weight: 700; color: #64748b; text-transform: uppercase;">Completion Velocity</div>
                <div style="font-size: 24px; font-weight: 800; color: #15803d; margin: 4px 0;">{completed} Tasks</div>
                <div style="font-size: 12px; color: #64748b;">Tasks marked completed in this session</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No action items to compute execution profile.")
