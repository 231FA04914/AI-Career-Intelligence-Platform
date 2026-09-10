"""
Transcript Workspace View - AI Career Intelligence Platform
Dedicated interface for inspecting, searching, and managing interview transcripts.
"""

import streamlit as st
from pathlib import Path
from src.ui.components import render_header, render_empty_state
from src.llm import InputValidationError, LLMServiceError


def render_transcript_view(
    transcript_manager,
    transcript_validator,
    meeting_summarizer,
    action_extractor,
    participant_mapper
):
    """Render the Transcript Workspace view."""
    render_header(
        title="Interview Transcript Workspace",
        subtitle="Review, search, and validate speech-to-text transcripts before generating AI intelligence.",
        badge_text="Transcript Ready",
        badge_color="#0ea5e9"
    )

    active_transcript = st.session_state.get("active_transcript", "")
    active_source = st.session_state.get("active_source_name", "interview_transcript.txt")

    if not active_transcript or not active_transcript.strip():
        render_empty_state(
            title="No Active Transcript in Workspace",
            description="Upload an interview recording or paste text in the Interview Analysis page to start working with transcripts.",
            icon="📝"
        )
        col_c1, col_c2, col_c3 = st.columns([1, 2, 1])
        with col_c2:
            if st.button("🎤 Go to Interview Analysis →", type="primary", use_container_width=True):
                st.session_state["nav_page"] = "Interview Analysis"
                st.rerun()

        # Also show saved transcripts library
        st.markdown("---")
        st.markdown("#### 📂 Saved Transcripts Archive")
        saved = transcript_manager.list_transcripts() if transcript_manager else []
        if saved:
            for t_path in saved:
                with st.expander(f"📄 {t_path.name}"):
                    try:
                        d = transcript_manager.load_transcript(str(t_path))
                        text_prev = d["transcript"]["text"]
                        st.text_area("Content", text_prev, height=120, key=f"t_prev_{t_path.name}")
                        if st.button(f"📋 Load '{t_path.name}' into Workspace", key=f"load_t_{t_path.name}"):
                            st.session_state["active_transcript"] = text_prev
                            st.session_state["active_source_name"] = t_path.name
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error loading transcript: {e}")
        return

    # Active Transcript Workspace
    words = len(active_transcript.split())
    chars = len(active_transcript)
    meta = st.session_state.get("active_transcript_metadata", {})
    dur_text = f"{meta['duration']:.1f}s" if "duration" in meta else "N/A"

    # Metadata bar
    st.markdown(f"""
    <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px 18px; margin-bottom: 18px; display: flex; flex-wrap: wrap; gap: 20px; align-items: center; justify-content: space-between;">
        <div><span style="color:#64748b; font-size:12px; font-weight:600;">SOURCE:</span> <strong style="color:#0f172a; font-size:13px;">{active_source}</strong></div>
        <div><span style="color:#64748b; font-size:12px; font-weight:600;">WORD COUNT:</span> <strong style="color:#0f172a; font-size:13px;">{words:,}</strong></div>
        <div><span style="color:#64748b; font-size:12px; font-weight:600;">CHARACTERS:</span> <strong style="color:#0f172a; font-size:13px;">{chars:,}</strong></div>
        <div><span style="color:#64748b; font-size:12px; font-weight:600;">DURATION:</span> <strong style="color:#0f172a; font-size:13px;">{dur_text}</strong></div>
        <div><span style="background:#ecfdf5; color:#059669; border:1px solid #a7f3d0; padding:2px 10px; border-radius:9999px; font-size:11px; font-weight:700;">✓ VALIDATED</span></div>
    </div>
    """, unsafe_allow_html=True)

    # Search & Filter within Transcript
    col_srch, col_cta = st.columns([3, 2])
    with col_srch:
        search_query = st.text_input("🔍 Search within transcript:", placeholder="Type a keyword to highlight...", key="transcript_search")
    with col_cta:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("🚀 Analyze this Transcript with AI →", type="primary", use_container_width=True):
            try:
                with st.status("🧠 Generating AI Meeting Intelligence...", expanded=True) as status:
                    st.write("Extracting Executive Summary, Decisions & Tasks (Gemini)...")
                    summary_res = meeting_summarizer.summarize(active_transcript)

                    st.write("Structuring Action Items & Priorities...")
                    from src.action_item_extractor import ExtractedActionItem
                    action_raw = summary_res.action_items or []
                    actions = [
                        ExtractedActionItem(
                            action=a.get("action", ""),
                            owner=a.get("owner"),
                            deadline=a.get("deadline"),
                            priority=a.get("priority") or "Medium",
                            status=a.get("status") or "Pending"
                        ) if isinstance(a, dict) else a
                        for a in action_raw
                    ]

                    st.write("Mapping Participant Responsibilities...")
                    participants = participant_mapper.map_responsibilities(
                        transcript=active_transcript,
                        action_items=actions,
                        meeting_id=Path(active_source).stem,
                        participants=summary_res.participants or []
                    )

                    status.update(label="✅ Complete AI Intelligence Generated!", state="complete")

                    st.session_state["latest_summary"] = summary_res.to_dict()
                    st.session_state["extracted_actions_list"] = [a.to_dict() if isinstance(a, ExtractedActionItem) else a for a in actions]
                    st.session_state["mapped_participants_list"] = [p.to_dict() for p in participants]

                    st.success("✅ Intelligence ready! Opening AI Insights...")
                    st.session_state["nav_page"] = "AI Insights"
                    st.rerun()

            except Exception as e:
                err_msg = str(e)
                if "rate limit" in err_msg.lower() or "quota" in err_msg.lower():
                    st.error("⚠️ **Gemini API Rate Limit / Quota Reached**: Google Gemini free tier allows a limited number of requests per minute. Please wait 15–30 seconds and try again.")
                else:
                    st.error(f"❌ Analysis failed: {err_msg}")

    # Transcript Text Area
    display_text = active_transcript
    if search_query and search_query.strip():
        q = search_query.strip().lower()
        occurrences = active_transcript.lower().count(q)
        st.caption(f"Found **{occurrences}** occurrences of `{search_query}`")

    st.text_area(
        "Interview Transcript",
        value=display_text,
        height=320,
        key="full_transcript_viewer",
        label_visibility="collapsed"
    )

    # Transcript Quality Metrics Expander
    with st.expander("📊 Transcript Quality Metrics & Details"):
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric("Total Words", f"{words:,}")
        with col_m2:
            st.metric("Total Characters", f"{chars:,}")
        with col_m3:
            reading_time = max(1, round(words / 130))
            st.metric("Est. Reading Time", f"~{reading_time} min")

    # Download transcript options
    st.download_button(
        label="📥 Download Transcript (.txt)",
        data=active_transcript,
        file_name=f"transcript_{Path(active_source).stem}.txt",
        mime="text/plain"
    )
