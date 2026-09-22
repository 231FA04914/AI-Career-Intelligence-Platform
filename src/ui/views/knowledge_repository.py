"""
Meeting Knowledge Repository, Vector Database & AI Search View (Milestone 3 - Tasks 1, 2 & 3)
Executive-grade interface for organizing, searching, vector database integration,
metadata filtering, and meeting-to-vector traceability.
"""

import streamlit as st
from datetime import datetime
from typing import Optional

from src.repository import MeetingKnowledgeRepository
from src.database import DatabaseManager
from src.vector_db import VectorDatabase
from src.ui.components import (
    render_header,
    render_kpi_card,
    render_empty_state,
    render_priority_badge,
    render_status_badge
)


def render_knowledge_repository_view(
    repository: MeetingKnowledgeRepository,
    db_manager: DatabaseManager
):
    """
    Render the Meeting Knowledge Repository, Vector Database, and AI Search Interface.
    """
    render_header(
        title="Meeting Knowledge Repository & Vector Database",
        subtitle="Organize historical meetings, manage dense vector embeddings, run metadata-filtered similarity search, and verify bidirectional meeting traceability.",
        badge_text="Milestone 3: Vector Database Layer",
        badge_color="#6366f1"
    )

    vdb = getattr(repository, "vdb", None) or VectorDatabase(db_manager=db_manager)
    vdb_stats = vdb.get_stats()
    stats = repository.get_repository_stats()

    # 1. Top KPI Cards
    col_k1, col_k2, col_k3, col_k4, col_k5 = st.columns(5)
    with col_k1:
        render_kpi_card(
            title="Persisted Meetings",
            value=stats["total_meetings"],
            subtitle="Indexed meeting sessions",
            icon="🏛️",
            icon_bg="#eef2ff"
        )
    with col_k2:
        render_kpi_card(
            title="Stored Vectors",
            value=vdb_stats["total_vectors"],
            subtitle="Vectors in database",
            icon="⚡",
            icon_bg="#ecfdf5"
        )
    with col_k3:
        render_kpi_card(
            title="Meetings Mapped",
            value=vdb_stats["total_meetings_indexed"],
            subtitle="With vector embeddings",
            icon="🌐",
            icon_bg="#f0f9ff"
        )
    with col_k4:
        render_kpi_card(
            title="Action Items",
            value=stats["total_action_items"],
            subtitle="Tracked deliverables",
            icon="📋",
            icon_bg="#fef3c7"
        )
    with col_k5:
        render_kpi_card(
            title="Traceability",
            value="100% Valid" if vdb_stats["traceability_verified"] else "Issues Detected",
            subtitle="Vector-to-meeting linkage",
            icon="🛡️",
            icon_bg="#f5f3ff"
        )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # 2. Main Tabs
    tab_vector_db, tab_semantic, tab_multi_search, tab_ai_qa, tab_graph, tab_tracer = st.tabs([
        "🗄️ Vector Database & Filters",
        "⚡ Similarity Search",
        "🔍 Multi-Entity Search",
        "🧠 AI Natural Language Q&A",
        "🌐 Meeting Knowledge Graph",
        "🔎 Vector-to-Meeting Tracer"
    ])

    # ----------------------------------------------------
    # TAB 1: Vector Database & Metadata Filtering (Milestone 3 Task 3)
    # ----------------------------------------------------
    with tab_vector_db:
        st.markdown("##### 🗄️ Vector Database Management & Metadata Filtering")
        st.caption("Inspect stored vector records, test metadata filters, and perform dynamic vector management.")

        all_vectors = db_manager.get_all_embeddings()

        col_v1, col_v2 = st.columns([2, 1])
        with col_v1:
            st.markdown(f"**Total Vectors in Database:** `{len(all_vectors)}` across `{vdb_stats['total_meetings_indexed']}` meetings.")
        with col_v2:
            if st.button("⚡ Re-index / Backfill All Vectors", key="btn_reindex_vdb", type="primary", use_container_width=True):
                with st.spinner("Generating embeddings for all meetings..."):
                    count = repository.generate_all_missing_embeddings()
                st.success(f"Generated {count} vectors!")
                st.rerun()

        if all_vectors:
            # Metadata Filter Sandbox
            st.markdown("###### 🎯 Vector Filter Sandbox")
            f_col1, f_col2, f_col3 = st.columns(3)
            with f_col1:
                sel_ent = st.selectbox("Entity Type Filter:", ["All", "transcript_section", "summary", "decision", "action_item"], key="vdb_f_ent")
            with f_col2:
                meetings = db_manager.get_all_meetings()
                m_options = ["All"] + [m["id"] for m in meetings]
                sel_mid = st.selectbox("Meeting ID Filter:", m_options, key="vdb_f_mid")
            with f_col3:
                all_actions = db_manager.get_all_action_items()
                owners = ["All"] + sorted(list({a['owner'] for a in all_actions if a.get('owner')}))
                sel_owner = st.selectbox("Assignee Filter:", owners, key="vdb_f_owner")

            v_filters = {}
            if sel_ent != "All":
                v_filters["entity_type"] = sel_ent
            if sel_mid != "All":
                v_filters["meeting_id"] = sel_mid
            if sel_owner != "All":
                v_filters["owner"] = sel_owner

            filtered_vecs = [v for v in all_vectors if vdb._matches_filters(v, v_filters)]
            st.markdown(f"**Showing {len(filtered_vecs)} of {len(all_vectors)} matching vector records:**")

            for v in filtered_vecs[:25]:
                with st.expander(f"⚡ Vector `{v['id']}` • [{v['entity_type'].upper()}] • Meeting: {v.get('meeting_title', v['meeting_id'])}"):
                    st.write(f"📄 **Text Content:** *\"{v['text_content']}\"*")
                    st.caption(f"🆔 Vector ID: `{v['id']}` | 📁 Meeting ID: `{v['meeting_id']}` | ⏱️ Dim: `{v['dimension']}` | 🏷️ Model: `{v['model_name']}`")
                    if v.get("metadata"):
                        st.json(v["metadata"])
        else:
            render_empty_state(
                title="No Vectors Stored in Vector Database",
                description="Click the '⚡ Re-index / Backfill All Vectors' button above to generate vector embeddings for all existing meetings.",
                icon="🗄️"
            )

    # ----------------------------------------------------
    # TAB 2: Semantic Similarity Search (Milestone 3 Tasks 2 & 3)
    # ----------------------------------------------------
    with tab_semantic:
        st.markdown("##### ⚡ Vector Similarity Search & Ranking")
        st.caption("Run cosine similarity search over vector database with metadata filtering.")

        sem_col1, sem_col2 = st.columns([3, 1])
        with sem_col1:
            sem_query = st.text_input(
                "Enter concept or query for Vector Database:",
                placeholder="e.g., PostgreSQL migration, UI component styling, DevOps automation",
                key="vdb_sem_query_input"
            )
        with sem_col2:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            sem_btn = st.button("Search Vector DB", type="primary", use_container_width=True)

        sem_f1, sem_f2 = st.columns(2)
        with sem_f1:
            sem_type_filter = st.selectbox(
                "Target Vector Entity:",
                ["All", "transcript_section", "summary", "decision", "action_item"],
                key="vdb_sem_type_sel"
            )
        with sem_f2:
            min_score = st.slider("Cosine Similarity Cutoff:", min_value=0.0, max_value=0.9, value=0.15, step=0.05, key="vdb_sem_cutoff")

        if sem_query or sem_btn:
            filters = {"entity_type": sem_type_filter} if sem_type_filter != "All" else None
            with st.spinner("Searching Vector Database..."):
                results = vdb.similarity_search(
                    query=sem_query,
                    top_k=15,
                    filters=filters,
                    min_similarity=min_score
                )

            if results:
                st.markdown(f"**Found {len(results)} vector matches (Similarity Score ≥ {min_score}):**")
                for idx, r in enumerate(results):
                    score_pct = int(r["similarity_score"] * 100)
                    ent_tag = r.get("entity_type", "vector").replace("_", " ").title()

                    with st.container():
                        st.markdown(f"**{idx+1}. [{ent_tag}]** • Similarity: `{score_pct}%` ({r['similarity_score']}) | Meeting: **{r.get('meeting_title', r['meeting_id'])}**")
                        st.markdown(f"> *\"{r.get('text_content', '')}\"*")
                        st.caption(f"🆔 Vector ID: `{r['id']}` | 📁 Meeting ID: `{r['meeting_id']}` | 🏷️ Dim: `{r['dimension']}`")
                        st.divider()
            else:
                render_empty_state(
                    title="No Vector Matches Found",
                    description="Try lowering the similarity threshold or broadening your search query.",
                    icon="⚡"
                )

    # ----------------------------------------------------
    # TAB 3: Multi-Entity Keyword Search
    # ----------------------------------------------------
    with tab_multi_search:
        st.markdown("##### 🔍 Multi-Entity Knowledge Search")
        st.caption("Search across meeting metadata, full transcripts, summaries, decisions, action items, participants, and deadlines.")

        col_s1, col_s2 = st.columns([3, 1])
        with col_s1:
            keyword = st.text_input("Search query keyword or phrase:", placeholder="e.g., PostgreSQL, roadmap, UI redesign, Priya, Friday", key="repo_keyword_input")
        with col_s2:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            search_trigger = st.button("Search Knowledge Base", type="primary", use_container_width=True)

        if keyword or search_trigger:
            results = repository.search_all(query=keyword)
            st.markdown(f"**Found {results['total_matches']} matching items across {len(results['linked_meetings'])} meetings:**")

            ent_tab1, ent_tab2, ent_tab3, ent_tab4, ent_tab5, ent_tab6, ent_tab7 = st.tabs([
                f"🏛️ Meetings ({len(results['entities']['metadata'])})",
                f"📝 Transcripts ({len(results['entities']['transcript'])})",
                f"📄 Summaries ({len(results['entities']['summary'])})",
                f"🎯 Decisions ({len(results['entities']['decision'])})",
                f"📋 Actions ({len(results['entities']['action_item'])})",
                f"👥 Participants ({len(results['entities']['participant'])})",
                f"📅 Deadlines ({len(results['entities']['deadline'])})"
            ])

            with ent_tab1:
                for m in results['entities']['metadata']:
                    st.markdown(f"**📁 {m['title']}** (ID: `{m['id']}`)")
                    st.caption(f"Filename: `{m.get('original_filename', 'N/A')}` | Duration: `{m.get('duration', 0):.1f}s`")
                    st.divider()

            with ent_tab2:
                for t in results['entities']['transcript']:
                    st.markdown(f"**📁 {t['meeting_title']}** (ID: `{t['meeting_id']}`)")
                    for s in t["snippets"]:
                        st.markdown(f"> *\"{s}\"*")
                    st.divider()

            with ent_tab3:
                for s in results['entities']['summary']:
                    st.markdown(f"**📁 {s['meeting_title']}** (ID: `{s['meeting_id']}`)")
                    st.write(s.get("summary_text", ""))
                    st.divider()

            with ent_tab4:
                for d in results['entities']['decision']:
                    st.markdown(f"**📁 {d['meeting_title']}** (ID: `{d['meeting_id']}`)")
                    st.markdown(f"- 🎯 **Decision:** {d['decision_text']}")
                    st.divider()

            with ent_tab5:
                for a in results['entities']['action_item']:
                    pb = render_priority_badge(a.get('priority'))
                    sb = render_status_badge(a.get('status'))
                    st.markdown(f"- **{a['action']}** (👤 `{a.get('owner') or 'Unassigned'}` | 📅 Due: `{a.get('deadline') or 'None'}`) {pb} {sb}", unsafe_allow_html=True)
                    st.divider()

            with ent_tab6:
                for p in results['entities']['participant']:
                    st.markdown(f"👤 **{p['canonical_name']}** (Role: `{p.get('role') or 'Member'}`) • Meeting: **{p.get('meeting_title')}**")
                    st.divider()

            with ent_tab7:
                for d in results['entities']['deadline']:
                    pb = render_priority_badge(d.get('priority'))
                    sb = render_status_badge(d.get('status'))
                    st.markdown(f"📅 **Due: `{d.get('deadline')}`** — {d.get('action')} (👤 `{d.get('owner') or 'Unassigned'}`) {pb} {sb}", unsafe_allow_html=True)
                    st.divider()

    # ----------------------------------------------------
    # TAB 4: AI Natural Language Q&A
    # ----------------------------------------------------
    with tab_ai_qa:
        st.markdown("##### 🧠 AI Natural Language Query Engine")
        st.caption("Ask questions across meeting knowledge with cited sources.")

        ai_query = st.text_input(
            "Enter your question for the Meeting Knowledge Repository:",
            placeholder="e.g., What did Ravi commit to deliver by Friday?",
            key="ai_repo_search_input"
        )

        if st.button("🚀 Ask Knowledge AI", type="primary", key="btn_ask_qa"):
            if ai_query:
                with st.spinner("Analyzing meeting intelligence..."):
                    response = repository.ai_search(ai_query)

                st.markdown("#### 💡 AI Response")
                st.info(response["answer"])

                if response.get("citations"):
                    st.markdown("##### 📚 Source Citations")
                    for c in response["citations"]:
                        st.markdown(f"- 📁 **{c['title']}** (ID: `{c['id']}`) • Date: `{c.get('created_at', 'N/A')[:19]}`")

    # ----------------------------------------------------
    # TAB 5: Meeting Knowledge Graph
    # ----------------------------------------------------
    with tab_graph:
        st.markdown("##### 🌐 Interconnected Meeting Knowledge Graph")
        st.caption("Inspect the full relational tree and vector embeddings for any meeting.")

        all_meetings = db_manager.get_all_meetings()
        if all_meetings:
            meeting_choices = {f"{m['title']} ({m['id']})": m['id'] for m in all_meetings}
            selected_m_label = st.selectbox("Select Meeting to Inspect:", list(meeting_choices.keys()), key="graph_select_meeting")
            sel_id = meeting_choices[selected_m_label]

            graph = repository.get_meeting_knowledge_graph(sel_id)
            if graph:
                meta = graph["metadata"]
                st.markdown(f"### 📁 {meta['title']}")
                st.write(f"🆔 **ID:** `{meta['id']}` | ⏱️ **Duration:** `{meta.get('duration', 0):.1f}s` | 📅 **Date:** `{meta.get('created_at', 'N/A')[:19]}`")

                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    st.markdown("###### 📄 Executive Summary")
                    st.write(graph.get("summary") or "_No summary available._")

                    st.markdown("###### 🎯 Key Decisions")
                    for dec in graph.get("decisions", []):
                        st.markdown(f"- {dec}")

                with col_g2:
                    st.markdown("###### 👥 Participants")
                    for p in graph.get("participants", []):
                        role_str = f" ({p['role']})" if p.get("role") else ""
                        st.markdown(f"- 👤 **{p['canonical_name']}**{role_str}")

                    st.markdown("###### ⚡ Linked Vectors")
                    m_vecs = vdb.get_vectors_for_meeting(sel_id)
                    st.write(f"Total **{len(m_vecs)} vector embeddings** mapped to this meeting session.")

                st.markdown(f"###### 📋 Action Items ({len(graph.get('action_items', []))})")
                for act in graph.get("action_items", []):
                    pb = render_priority_badge(act.get("priority"))
                    sb = render_status_badge(act.get("status"))
                    st.markdown(f"- **{act['action']}** (👤 `{act.get('owner') or 'Unassigned'}` | 📅 Due: `{act.get('deadline') or 'None'}`) {pb} {sb}", unsafe_allow_html=True)
        else:
            render_empty_state(
                title="No Meetings Available",
                description="Process and save meetings to explore their knowledge graphs.",
                icon="🌐"
            )

    # ----------------------------------------------------
    # TAB 6: Vector-to-Meeting Tracer & Traceability Audit (Milestone 3 Task 3)
    # ----------------------------------------------------
    with tab_tracer:
        st.markdown("##### 🔎 Vector-to-Meeting Tracer & Traceability Audit")
        st.caption("Explicit Milestone 3 Task 3 Requirement: Verify that every stored vector can be traced back to the correct meeting.")

        # 1. Reverse Vector Tracer
        st.markdown("###### 🔍 Reverse Vector Tracer")
        all_vec_records = db_manager.get_all_embeddings()

        if all_vec_records:
            vec_options = {f"[{v['entity_type'].upper()}] Vector {v['id']} ({v['text_content'][:40]}...)": v['id'] for v in all_vec_records}
            sel_vec_label = st.selectbox("Select Vector ID to trace back to parent meeting:", list(vec_options.keys()), key="tracer_select_vec")
            target_vid = vec_options[sel_vec_label]

            trace = vdb.trace_vector_to_meeting(target_vid)
            if trace:
                if trace["is_orphaned"]:
                    st.error(f"❌ Vector `{target_vid}` is ORPHANED! No parent meeting found for `meeting_id={trace['meeting_id']}`.")
                else:
                    st.success(f"✅ **Traceability Confirmed**: Vector `{target_vid}` traces back directly to parent meeting **'{trace['meeting_title']}'** (ID: `{trace['meeting_id']}`).")

                    c_tr1, c_tr2 = st.columns(2)
                    with c_tr1:
                        st.markdown("###### 📁 Parent Meeting Record")
                        st.write(f"- **Title:** {trace['meeting_title']}")
                        st.write(f"- **Meeting ID:** `{trace['meeting_id']}`")
                        st.write(f"- **Recorded Date:** `{trace.get('meeting_created_at', 'N/A')[:19]}`")
                        st.write(f"- **Source File:** `{trace.get('original_filename') or 'Transcript'}`")
                        st.write(f"- **Duration:** `{trace.get('duration', 0):.1f}s`")
                    with c_tr2:
                        st.markdown("###### ⚡ Vector Payload Details")
                        st.write(f"- **Entity Type:** `{trace['entity_type']}`")
                        st.write(f"- **Entity ID:** `{trace['entity_id']}`")
                        st.write(f"- **Dimension:** `{trace['dimension']}` floats")
                        st.write(f"- **Model:** `{trace['model_name']}`")
                        st.write(f"- **Text Content:** *\"{trace['text_content']}\"*")

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

        # 2. Comprehensive Traceability Audit
        st.markdown("###### 🛡️ Repository Traceability Audit")
        if st.button("🔄 Run Full Traceability Audit", type="primary", key="btn_run_trace_audit"):
            with st.spinner("Auditing 100% of stored vectors against parent meeting sessions..."):
                audit = vdb.verify_traceability()

            if audit["is_valid"]:
                st.success(f"✅ **Vector Traceability Audit PASSED**: 100% of stored vectors ({audit['total_vectors']}/{audit['total_vectors']}) successfully trace back to valid parent meeting sessions with 0 orphans.")
            else:
                st.error(f"⚠️ Traceability issues detected: {audit['orphan_count']} orphaned vectors found.")

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Total Vectors Audited", audit["total_vectors"])
            with c2:
                st.metric("Validly Traced Vectors", audit["validly_traced_vectors"])
            with c3:
                st.metric("Orphaned Vectors", audit["orphan_count"])
