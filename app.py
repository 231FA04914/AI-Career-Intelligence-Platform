    }
    option_to_page = {v: k for k, v in page_to_option.items()}

    current_idx = 0
    if st.session_state["nav_page"] in page_to_option:
        current_idx = nav_options.index(page_to_option[st.session_state["nav_page"]])

    selected_option = st.sidebar.radio(
        "Navigation",
        options=nav_options,
        index=current_idx,
        label_visibility="collapsed"
    )

    # Sync navigation state
    selected_page = option_to_page[selected_option]
    if selected_page != st.session_state["nav_page"]:
        st.session_state["nav_page"] = selected_page
        st.rerun()

    # Sidebar Quick Stats / Status
    render_system_status(
        ai_ready=ai_ready,
        whisper_ready=True,
        db_ready=db_manager is not None
    )

    # ----------------------------------------------------
    # PAGE ROUTER
    # ----------------------------------------------------
    current_page = st.session_state["nav_page"]

    if current_page == "Dashboard":
        render_dashboard_view(
            db_manager=db_manager,
            transcript_manager=transcript_manager,
            summary_manager=summary_manager,
            repository=repository,
            pipeline=pipeline,
            user_info=current_user
        )

    elif current_page == "Meeting Details":
        render_meeting_details_view(
            db_manager=db_manager,
            user_id=user_id
        )

    elif current_page == "Platform Integrations":
        render_integrations_view(
            zoom_integration=zoom_integration,
            google_meet_integration=google_meet_integration,
            pipeline=pipeline,
            db_manager=db_manager,
            user_id=user_id
        )

    elif current_page == "Interview Analysis":
        render_interview_analysis_view(
            audio_processor=audio_processor,
            transcriber=transcriber,
            file_validator=file_validator,
            transcript_validator=transcript_validator,
            transcript_manager=transcript_manager,
            meeting_summarizer=meeting_summarizer,
            action_extractor=action_extractor,
            participant_mapper=participant_mapper,
            pipeline=pipeline,
            db_manager=db_manager
        )

    elif current_page == "Transcript Workspace":
        render_transcript_view(
            transcript_manager=transcript_manager,
            transcript_validator=transcript_validator,
            meeting_summarizer=meeting_summarizer,
            action_extractor=action_extractor,
            participant_mapper=participant_mapper
        )

    elif current_page == "AI Insights":
        render_ai_insights_view(
            meeting_summarizer=meeting_summarizer,
            summary_manager=summary_manager,
            action_extractor=action_extractor,
            participant_mapper=participant_mapper,
            db_manager=db_manager
        )

    elif current_page == "Knowledge Repository":
        render_knowledge_repository_view(
            repository=repository,
            db_manager=db_manager
        )

    elif current_page == "Career Intelligence":
        render_career_intelligence_view()

    elif current_page == "Interview Preparation":
        render_interview_prep_view(
            db_manager=db_manager,
            llm_service=llm_service
        )

    elif current_page == "Database & Archive":
        render_database_archive_view(
            db_manager=db_manager,
            summary_manager=summary_manager,
            meeting_summarizer=meeting_summarizer
        )

    elif current_page == "Settings & Health":
        render_settings_view(
            llm_service=llm_service,
            transcriber=transcriber,
            db_manager=db_manager
        )

    # Global Footer
    render_footer()


if __name__ == "__main__":
    main()
