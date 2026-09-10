"""
Interview Preparation View - AI Career Intelligence Platform
Provides conversation follow-up recommendations and future preparation roadmap.
"""

import streamlit as st
from src.ui.components import render_header, render_empty_state


def render_interview_prep_view():
    """Render the Interview Preparation view."""
    render_header(
        title="Interview Preparation & Follow-Up",
        subtitle="Review discussion themes, prepare smart follow-ups, and track preparation roadmap.",
        badge_text="Prep Ready",
        badge_color="#0ea5e9"
    )

    summary_data = st.session_state.get("latest_summary")

    if summary_data:
        st.markdown("#### 🎯 Follow-Up Discussion Themes")
        st.caption("Key themes identified from your latest interview transcript to prepare for your next conversation:")

        decisions = summary_data.get("key_decisions") or summary_data.get("decisions") or []
        key_points = summary_data.get("key_points", [])

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### 📌 Key Agreed Outcomes to Reference")
            if decisions:
                for d in decisions:
                    st.markdown(f"- **Outcome:** {d}")
            else:
                st.markdown("_No explicit outcomes recorded._")

        with col2:
            st.markdown("##### 💡 Key Discussion Highlights to Review")
            if key_points:
                for kp in key_points[:4]:
                    st.markdown(f"- **Topic:** {kp}")
            else:
                st.markdown("_No specific discussion topics identified._")

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    else:
        render_empty_state(
            title="No Active Interview to Prepare For",
            description="Upload an interview recording or paste text to generate discussion themes and follow-up recommendations.",
            icon="🎯"
        )

    # Future Roadmap Features (Milestone 3)
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
