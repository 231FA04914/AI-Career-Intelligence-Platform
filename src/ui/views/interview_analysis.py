"""
Interview Analysis View - AI Career Intelligence Platform
Supports Audio/Video recording upload with Whisper, direct transcript input, and saved transcript loading.
"""

import streamlit as st
from pathlib import Path
from src.ui.components import render_header, render_step_indicator, render_empty_state
from src.llm import (
    InputValidationError,
    LLMServiceError,
    ServiceUnavailableError,
    RateLimitError,
    AuthenticationError
)


def render_interview_analysis_view(
    audio_processor,
    transcriber,
    file_validator,
    transcript_validator,
    transcript_manager,
    meeting_summarizer,
    action_extractor,
    participant_mapper,
    pipeline,
    db_manager
):
    """Render the main Interview Analysis interface."""
    render_header(
        title="Interview Analysis",
        subtitle="Transform your audio/video recording or transcript into structured AI intelligence.",
        badge_text="Analysis Engine",
        badge_color="#4f46e5"
    )

    # 4-Stage Stepper
    current_step = 1
    if "active_transcript" in st.session_state and st.session_state["active_transcript"]:
        current_step = 3
    if "latest_summary" in st.session_state:
        current_step = 4

    render_step_indicator(
        steps=["Input Recording/Text", "Transcription (Whisper)", "AI Analysis (Gemini)", "Structured Insights"],
        current_step=current_step
    )

    # Input method selection tabs
    tab_upload, tab_text, tab_saved = st.tabs([
        "🎙️ Audio / Video Recording",
        "✍️ Paste / Input Transcript",
        "📂 Load Saved Transcript"
    ])

    # ----------------------------------------------------
    # TAB 1: Audio / Video Recording Upload
    # ----------------------------------------------------
    with tab_upload:
        st.markdown("##### 📁 Upload Interview or Meeting Recording")
        st.info(f"Supported media formats: **{file_validator.get_supported_formats()}** (Max 500 MB)")

        uploaded_file = st.file_uploader(
            "Choose an audio or video file",
            type=list(file_validator.AUDIO_FORMATS | file_validator.VIDEO_FORMATS),
            help="Click to select or drag-and-drop an audio (.mp3, .wav, .m4a) or video (.mp4, .webm) file.",
            key="analysis_file_uploader"
        )

        if uploaded_file:
            # File metadata card
            file_type = "Video File (.mp4/.webm)" if file_validator.is_video_file(uploaded_file.name) else "Audio File (.mp3/.wav/.m4a)"
            col_inf1, col_inf2, col_inf3 = st.columns(3)
            with col_inf1:
                st.write(f"📄 **Filename:** `{uploaded_file.name}`")
            with col_inf2:
                st.write(f"📦 **Size:** `{uploaded_file.size / (1024*1024):.2f} MB`")
            with col_inf3:
                st.write(f"🎞️ **Type:** `{file_type}`")

            # Save uploaded file
            upload_dir = Path(__file__).parent.parent.parent.parent / "data" / "uploads"
            upload_dir.mkdir(parents=True, exist_ok=True)
            upload_path = upload_dir / uploaded_file.name
            with open(upload_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Validate file
            is_valid, error_msg = file_validator.validate_file(str(upload_path))

            if not is_valid:
                st.error(f"❌ Invalid File: {error_msg}")
                if upload_path.exists():
                    upload_path.unlink()
            else:
                st.success("✅ File uploaded and format verified successfully!")

                # Action buttons
                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                col_btn_run1, col_btn_run2 = st.columns(2)

                with col_btn_run1:
                    run_transcribe_only = st.button("🎯 Transcribe Recording Only (Whisper)", type="secondary", use_container_width=True)
                with col_btn_run2:
                    run_full_pipeline = st.button("🚀 Run Full Pipeline (Whisper → AI → DB)", type="primary", use_container_width=True, disabled=pipeline is None)

                # Action 1: Full Pipeline execution
                if run_full_pipeline:
                    try:
                        with st.status("🚀 Processing Full Meeting Intelligence Pipeline...", expanded=True) as status:
                            def pipeline_progress_ui(msg, pct):
                                st.write(f"[{pct}%] {msg}")

                            pipeline_result = pipeline.process_audio_file(
                                str(upload_path),
                                meeting_title=uploaded_file.name.rsplit('.', 1)[0].replace('_', ' ').title(),
                                progress_callback=pipeline_progress_ui
                            )
                            status.update(label="✅ Full Pipeline Completed & Persisted to Database!", state="complete")

                            st.session_state["active_transcript"] = pipeline_result["transcript"]
                            st.session_state["active_source_name"] = uploaded_file.name
                            st.session_state["latest_summary"] = {
                                "summary": pipeline_result["summary"],
                                "key_decisions": pipeline_result["decisions"],
                                "action_items": pipeline_result["action_items"]
                            }
                            st.session_state["extracted_actions_list"] = pipeline_result["action_items"]
                            st.session_state["mapped_participants_list"] = pipeline_result["participants"]
                            st.success(f"✅ Successfully processed meeting `{pipeline_result['title']}` (ID: `{pipeline_result['meeting_id']}`)")
                            st.session_state["nav_page"] = "AI Insights"
                            st.rerun()
                    except ServiceUnavailableError as e:
                        if getattr(pipeline, "last_transcript_text", None):
                            st.session_state["active_transcript"] = pipeline.last_transcript_text
                            st.session_state["active_source_name"] = uploaded_file.name
                        st.warning("⚠️ **AI Service High Demand (503 UNAVAILABLE)**: The Google Gemini model is experiencing a temporary spike in traffic. Your audio transcript has been safely saved.")
                        st.info("💡 Click **🔄 Try AI Analysis Again** below to run AI insights directly on the saved transcript without re-transcribing the audio.")
                    except RateLimitError as e:
                        if getattr(pipeline, "last_transcript_text", None):
                            st.session_state["active_transcript"] = pipeline.last_transcript_text
                            st.session_state["active_source_name"] = uploaded_file.name
                        st.warning("⚠️ **Rate Limit Reached (429)**: Gemini free tier rate limit was reached. Please wait 15–30 seconds and click **Try AI Analysis Again**.")
                    except AuthenticationError as e:
                        st.error("❌ **Authentication Failed**: Invalid or missing Gemini API key. Please check LLM_API_KEY in your `.env` file.")
                    except Exception as e:
                        st.error(f"❌ Pipeline failed: {str(e)}")
                        if getattr(pipeline, "last_transcript_text", None):
                            st.session_state["active_transcript"] = pipeline.last_transcript_text
                            st.session_state["active_source_name"] = uploaded_file.name


                # Action 2: Transcribe Only execution
                if run_transcribe_only:
                    audio_path = None
                    try:
                        with st.status("🎤 Transcribing Audio with Whisper...", expanded=True) as status:
                            st.write("Extracting & converting audio track with FFmpeg...")
                            audio_path = audio_processor.extract_audio(str(upload_path))
                            duration = audio_processor.get_audio_duration(audio_path)
                            st.write(f"✅ Audio extracted ({duration:.1f}s). Transcribing with Whisper base model...")

                            transcript_data = transcriber.transcribe(audio_path)
                            st.write("✅ Speech transcription completed.")

                            # Validate transcript
                            is_valid_t, err_t = transcript_validator.validate_transcript(transcript_data)
                            if not is_valid_t:
                                st.error(f"❌ Transcript validation failed: {err_t}")
                                return

                            # Save transcript locally
                            saved_path = transcript_manager.save_transcript(
                                transcript_data,
                                uploaded_file.name,
                                metadata={"duration": duration, "audio_path": audio_path}
                            )
                            status.update(label="✅ Transcription completed & saved!", state="complete")

                            st.session_state["active_transcript"] = transcript_data["text"]
                            st.session_state["active_source_name"] = uploaded_file.name
                            st.session_state["active_transcript_metadata"] = {
                                "duration": duration,
                                "word_count": len(transcript_data["text"].split()),
                                "saved_path": str(saved_path)
                            }
                            st.success("✅ Transcription ready! Navigating to Transcript Workspace...")
                            st.session_state["nav_page"] = "Transcript Workspace"
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error during transcription: {str(e)}")
                    finally:
                        if audio_processor:
                            audio_processor.cleanup_temp_files()
                        if upload_path.exists():
                            upload_path.unlink()

        # Dedicated retry button if transcript exists in session state but summary not yet generated
        if st.session_state.get("active_transcript") and not st.session_state.get("latest_summary"):
            st.markdown("---")
            st.markdown("##### 🔄 Saved Transcript in Workspace")
            st.info("A transcript is available in your workspace. You can re-run AI intelligence extraction without re-uploading or re-transcribing.")
            if st.button("🔄 Try AI Analysis Again (Process Saved Transcript)", type="primary", key="retry_analysis_btn", use_container_width=True):
                try:
                    with st.status("🧠 Processing AI Intelligence...", expanded=True) as status:
                        p_res = pipeline.process_transcript_text(
                            transcript_text=st.session_state["active_transcript"],
                            meeting_title=st.session_state.get("active_source_name", "Meeting").rsplit('.', 1)[0].replace('_', ' ').title()
                        )
                        status.update(label="✅ AI Intelligence Generated!", state="complete")
                        st.session_state["latest_summary"] = {
                            "summary": p_res["summary"],
                            "key_decisions": p_res["decisions"],
                            "action_items": p_res["action_items"]
                        }
                        st.session_state["extracted_actions_list"] = p_res["action_items"]
                        st.session_state["mapped_participants_list"] = p_res["participants"]
                        st.success(f"✅ Successfully processed meeting `{p_res['title']}`")
                        st.session_state["nav_page"] = "AI Insights"
                        st.rerun()
                except ServiceUnavailableError as retry_e:
                    st.warning("⚠️ **Gemini 503 (High Demand)**: The model is still experiencing peak demand. Please wait a moment and click Try Again.")
                except RateLimitError as retry_e:
                    st.warning("⚠️ **Rate Limit Reached (429)**: Please wait 15–30 seconds and click Try Again.")
                except Exception as retry_e:
                    st.error(f"❌ Analysis failed: {retry_e}")

    # ----------------------------------------------------
    # TAB 2: Direct Text / Transcript Input
    # ----------------------------------------------------
    with tab_text:
        st.markdown("##### 📝 Paste or Type Meeting Transcript")
        st.caption("Directly enter text from an interview or meeting conversation to generate executive intelligence.")

        default_text = st.session_state.get("active_transcript", "")
        pasted_text = st.text_area(
            "Meeting Transcript Text",
            value=default_text,
            height=240,
            placeholder="Paste interview or meeting transcript here...",
            key="analysis_text_input",
            label_visibility="collapsed"
        )

        # Word count & estimated token indicator
        word_count = len(pasted_text.split()) if pasted_text else 0
        est_tokens = len(pasted_text) // 4 if pasted_text else 0

        col_stat1, col_stat2, col_stat3 = st.columns([2, 1, 1])
        with col_stat1:
            st.caption(f"📊 Words: **{word_count}** | Estimated Tokens: **{est_tokens}**")
        with col_stat2:
            if st.button("🗑️ Clear Text", use_container_width=True):
                st.session_state["active_transcript"] = ""
                st.session_state.pop("latest_summary", None)
                st.rerun()
        with col_stat3:
            run_text_analysis = st.button("🚀 Analyze with AI", type="primary", use_container_width=True, disabled=meeting_summarizer is None)

        if run_text_analysis:
            if not pasted_text or not pasted_text.strip():
                st.error("❌ Please paste or enter a transcript before analyzing.")
            else:
                try:
                    with st.status("🧠 Generating AI Meeting Intelligence...", expanded=True) as status:
                        st.write("Validating transcript input...")
                        st.write("Extracting Executive Summary, Decisions & Tasks (Gemini)...")
                        summary_res = meeting_summarizer.summarize(pasted_text)

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

                        st.write("Mapping Participant Responsibilities & Aliases...")
                        participants = participant_mapper.map_responsibilities(
                            transcript=pasted_text,
                            action_items=actions,
                            meeting_id="Direct Transcript",
                            participants=summary_res.participants or []
                        )

                        status.update(label="✅ Complete AI Intelligence Generated!", state="complete")

                        st.session_state["active_transcript"] = pasted_text
                        st.session_state["active_source_name"] = "Pasted_Transcript.txt"
                        st.session_state["latest_summary"] = summary_res.to_dict()
                        st.session_state["extracted_actions_list"] = [a.to_dict() if isinstance(a, ExtractedActionItem) else a for a in actions]
                        st.session_state["mapped_participants_list"] = [p.to_dict() for p in participants]

                        st.success("✅ Analysis generated! Navigating to AI Insights...")
                        st.session_state["nav_page"] = "AI Insights"
                        st.rerun()

                except InputValidationError as e:
                    st.error(f"❌ Input Validation Error: {str(e)}")
                except ServiceUnavailableError as e:
                    st.warning("⚠️ **AI Service High Demand (503 UNAVAILABLE)**: The Google Gemini model is experiencing a temporary demand spike. Please wait a few seconds and click **Analyze with AI** again.")
                except RateLimitError as e:
                    st.warning("⚠️ **Gemini API Rate Limit (429)**: Rate limit reached. Please wait 15–30 seconds and click **Analyze with AI** again.")
                except AuthenticationError as e:
                    st.error("❌ **Authentication Error**: Please check your Gemini API key configuration.")
                except Exception as e:
                    st.error(f"❌ AI Service Error: {str(e)}")


    # ----------------------------------------------------
    # TAB 3: Load Saved Transcripts
    # ----------------------------------------------------
    with tab_saved:
        st.markdown("##### 📂 Load from Previous Transcripts")
        st.caption("Select any previously transcribed recording to load into the active workspace.")

        saved_transcripts = transcript_manager.list_transcripts() if transcript_manager else []

        if saved_transcripts:
            transcript_options = {t.name: t for t in saved_transcripts}
            selected_name = st.selectbox("Choose a saved transcript:", list(transcript_options.keys()))

            if selected_name:
                selected_file = transcript_options[selected_name]
                try:
                    t_data = transcript_manager.load_transcript(str(selected_file))
                    raw_text = t_data["transcript"]["text"]
                    metadata = t_data.get("metadata", {})

                    st.markdown(f"**Original Recording:** `{metadata.get('original_filename', 'Unknown')}` | **Recorded:** `{metadata.get('timestamp', 'N/A')}`")
                    st.text_area("Preview", raw_text[:400] + ("..." if len(raw_text) > 400 else ""), height=120, disabled=True)

                    if st.button("📋 Load this Transcript into Workspace", type="primary"):
                        st.session_state["active_transcript"] = raw_text
                        st.session_state["active_source_name"] = selected_name
                        st.session_state["nav_page"] = "Transcript Workspace"
                        st.success("Loaded into workspace!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error reading transcript: {e}")
        else:
            render_empty_state(
                title="No saved transcripts found",
                description="Upload an audio or video file in Tab 1 to generate speech-to-text transcripts.",
                icon="🎙️"
            )
