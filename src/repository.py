"""
Meeting Knowledge Repository Layer (Milestone 3 - Task 1)
Organizes, indexes, and queries historical meeting intelligence for AI and structured search.

Stores & makes searchable:
- Meeting metadata (id, title, duration, created_at, source filename)
- Transcript (full text and snippet context matching)
- Summary (executive summaries, discussion points)
- Decisions (key decisions linked to meeting)
- Action items (tasks with assignee, priority, status)
- Participants (attendee names, canonical names, roles)
- Deadlines (due dates and milestone timelines)
- Record Linkage & Integrity Verification (Milestone 3 Task 1 requirement)
"""

import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

from src.database import DatabaseManager
from src.llm.service import LLMService
from src.embeddings import EmbeddingGenerator
from src.vector_db import VectorDatabase

logger = logging.getLogger(__name__)


class MeetingKnowledgeRepository:
    """
    Central Repository for organizing, querying, and linking historical meeting intelligence.
    Provides multi-entity search, structured filters, semantic vector search,
    AI-assisted question answering, and database record integrity verification.
    """

    def __init__(
        self,
        db_manager: Optional[DatabaseManager] = None,
        llm_service: Optional[LLMService] = None,
        embedding_generator: Optional[EmbeddingGenerator] = None,
        vector_db: Optional[VectorDatabase] = None
    ):
        """
        Initialize the repository.
        
        Args:
            db_manager: Database persistence manager instance.
            llm_service: LLM service for AI-powered semantic search and Q&A.
            embedding_generator: Dense vector embedding service.
            vector_db: Integrated Vector Database manager.
        """
        self.db = db_manager or DatabaseManager()
        self.llm = llm_service
        self.embedder = embedding_generator or EmbeddingGenerator(api_key=getattr(llm_service, "api_key", None))
        self.vdb = vector_db or VectorDatabase(db_manager=self.db, embedding_generator=self.embedder)
        logger.info("Initialized MeetingKnowledgeRepository with VectorDatabase")

    # =========================================================================
    # 1. ENTITY SEARCH METHODS (Milestone 3 - Task 1 Requirements)
    # =========================================================================

    def search_metadata(
        self,
        query: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search meeting metadata by title, original filename, or date.
        
        Args:
            query: Search query text.
            date_from: Optional ISO date lower bound.
            date_to: Optional ISO date upper bound.
            
        Returns:
            List of matching meeting metadata dicts.
        """
        records = self.db.search_meetings_raw(query)
        filtered = []
        for r in records:
            created = r.get("created_at", "")
            if date_from and created and created < date_from:
                continue
            if date_to and created and created > date_to:
                continue
            item = dict(r)
            item["entity_type"] = "metadata"
            item["meeting_id"] = item["id"]
            filtered.append(item)
        return filtered

    def search_transcripts(
        self,
        query: str,
        context_window: int = 120
    ) -> List[Dict[str, Any]]:
        """
        Search within meeting transcripts and extract highlighted matching snippets.
        
        Args:
            query: Keyword or phrase to search.
            context_window: Number of surrounding characters to include in snippet.
            
        Returns:
            List of matches with meeting link and context snippets.
        """
        if not query or not query.strip():
            return []

        q_clean = query.strip()
        raw_matches = self.db.search_transcripts_raw(q_clean)
        results = []

        for row in raw_matches:
            text = row.get("transcript_text", "")
            snippets = self._extract_snippets(text, q_clean, context_window)
            if snippets:
                results.append({
                    "entity_type": "transcript",
                    "meeting_id": row["meeting_id"],
                    "meeting_title": row["meeting_title"],
                    "created_at": row.get("created_at"),
                    "original_filename": row.get("original_filename"),
                    "match_count": len(snippets),
                    "snippets": snippets
                })

        return results

    def search_summaries(self, query: str, context_window: int = 150) -> List[Dict[str, Any]]:
        """
        Search within executive summaries.
        
        Args:
            query: Keyword to search.
            context_window: Snippet radius.
            
        Returns:
            List of matching summaries linked to meetings.
        """
        if not query or not query.strip():
            return []

        q_clean = query.strip()
        raw_matches = self.db.search_summaries_raw(q_clean)
        results = []

        for row in raw_matches:
            summary_text = row.get("summary_text", "")
            snippets = self._extract_snippets(summary_text, q_clean, context_window)
            results.append({
                "entity_type": "summary",
                "summary_id": row["summary_id"],
                "meeting_id": row["meeting_id"],
                "meeting_title": row["meeting_title"],
                "created_at": row.get("created_at"),
                "summary_text": summary_text,
                "snippets": snippets
            })

        return results

    def search_decisions(self, query: str) -> List[Dict[str, Any]]:
        """
        Search within meeting decisions.
        
        Args:
            query: Keyword or phrase to search.
            
        Returns:
            List of matching decisions linked to their parent meeting.
        """
        if not query or not query.strip():
            return []

        raw_matches = self.db.search_decisions_raw(query.strip())
        results = []
        for row in raw_matches:
            results.append({
                "entity_type": "decision",
                "decision_id": row["decision_id"],
                "meeting_id": row["meeting_id"],
                "meeting_title": row["meeting_title"],
                "decision_text": row["decision_text"],
                "created_at": row.get("created_at")
            })
        return results

    def search_action_items(
        self,
        query: Optional[str] = None,
        owner: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search action items by keyword, assignee, status, and priority.
        
        Returns:
            List of action items linked to their parent meeting.
        """
        raw_matches = self.db.search_action_items_raw(
            query=query,
            owner=owner,
            status=status,
            priority=priority
        )
        results = []
        for row in raw_matches:
            item = dict(row)
            item["entity_type"] = "action_item"
            results.append(item)
        return results

    def search_participants(
        self,
        query: str,
        role: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search participants across meetings and return linked meeting records.
        """
        if not query or not query.strip():
            return []

        raw_matches = self.db.search_participants_raw(query.strip())
        results = []
        for row in raw_matches:
            if role and role != "All" and (not row.get("role") or role.lower() not in row["role"].lower()):
                continue
            item = dict(row)
            item["entity_type"] = "participant"
            results.append(item)
        return results

    def search_deadlines(
        self,
        query: Optional[str] = None,
        timeframe: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search deadlines extracted across meetings.
        
        Args:
            query: Keyword or date string.
            timeframe: Optional timeframe filter (e.g. 'all', 'upcoming', 'overdue').
            
        Returns:
            List of action items having deadlines linked to their parent meeting.
        """
        raw_matches = self.db.search_deadlines_raw(query)
        results = []
        for row in raw_matches:
            item = dict(row)
            item["entity_type"] = "deadline"
            results.append(item)
        return results

    # =========================================================================
    # 2. UNIFIED MULTI-ENTITY SEARCH ENGINE
    # =========================================================================

    def search_all(
        self,
        query: str,
        entity_types: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute unified search across all 7 meeting knowledge entities simultaneously.
        
        Args:
            query: Search query string.
            entity_types: List of entity types to include. Defaults to all 7:
                         ['metadata', 'transcript', 'summary', 'decision', 'action_item', 'participant', 'deadline']
            filters: Optional dictionary of faceted filters:
                     {'owner': str, 'status': str, 'priority': str, 'role': str}
                     
        Returns:
            Dictionary containing categorized hits, total count, and matched meeting summary.
        """
        filters = filters or {}
        active_types = set(entity_types or [
            "metadata", "transcript", "summary", "decision", "action_item", "participant", "deadline"
        ])

        results = {
            "query": query,
            "total_matches": 0,
            "entities": {
                "metadata": [],
                "transcript": [],
                "summary": [],
                "decision": [],
                "action_item": [],
                "participant": [],
                "deadline": []
            },
            "linked_meetings": {}
        }

        if not query or not query.strip():
            # If empty query but filters present (e.g. status/owner filters for action items)
            if "action_item" in active_types and any(filters.values()):
                act_items = self.search_action_items(
                    query=None,
                    owner=filters.get("owner"),
                    status=filters.get("status"),
                    priority=filters.get("priority")
                )
                results["entities"]["action_item"] = act_items
                results["total_matches"] += len(act_items)
            return results

        q = query.strip()

        # 1. Metadata
        if "metadata" in active_types:
            meta = self.search_metadata(q)
            results["entities"]["metadata"] = meta
            results["total_matches"] += len(meta)

        # 2. Transcripts
        if "transcript" in active_types:
            transcripts = self.search_transcripts(q)
            results["entities"]["transcript"] = transcripts
            results["total_matches"] += len(transcripts)

        # 3. Summaries
        if "summary" in active_types:
            summaries = self.search_summaries(q)
            results["entities"]["summary"] = summaries
            results["total_matches"] += len(summaries)

        # 4. Decisions
        if "decision" in active_types:
            decisions = self.search_decisions(q)
            results["entities"]["decision"] = decisions
            results["total_matches"] += len(decisions)

        # 5. Action Items
        if "action_item" in active_types:
            actions = self.search_action_items(
                query=q,
                owner=filters.get("owner"),
                status=filters.get("status"),
                priority=filters.get("priority")
            )
            results["entities"]["action_item"] = actions
            results["total_matches"] += len(actions)

        # 6. Participants
        if "participant" in active_types:
            participants = self.search_participants(q, role=filters.get("role"))
            results["entities"]["participant"] = participants
            results["total_matches"] += len(participants)

        # 7. Deadlines
        if "deadline" in active_types:
            deadlines = self.search_deadlines(q)
            results["entities"]["deadline"] = deadlines
            results["total_matches"] += len(deadlines)

        # Aggregate unique linked meetings
        for ent_key, ent_list in results["entities"].items():
            for item in ent_list:
                m_id = item.get("meeting_id") or item.get("id")
                m_title = item.get("meeting_title") or item.get("title", f"Meeting {m_id}")
                if m_id:
                    if m_id not in results["linked_meetings"]:
                        results["linked_meetings"][m_id] = {
                            "meeting_id": m_id,
                            "title": m_title,
                            "match_types": set(),
                            "hit_count": 0
                        }
                    results["linked_meetings"][m_id]["match_types"].add(ent_key)
                    results["linked_meetings"][m_id]["hit_count"] += 1

        # Convert set to sorted list for JSON serialization
        for m_id in results["linked_meetings"]:
            results["linked_meetings"][m_id]["match_types"] = sorted(list(results["linked_meetings"][m_id]["match_types"]))

        return results

    # =========================================================================
    # 3. AI-POWERED NATURAL LANGUAGE SEARCH & Q&A
    # =========================================================================

    def ai_search(self, question: str, max_meetings: int = 10) -> Dict[str, Any]:
        """
        Execute natural language AI search over all historical meeting records.
        Synthesizes an answer with specific citations to meeting IDs and sections.
        
        Args:
            question: User natural language query (e.g. "What did Ravi commit to do by Friday?").
            max_meetings: Maximum number of meeting contexts to include in LLM prompt.
            
        Returns:
            Dictionary containing synthesized answer, cited meetings, and matching entities.
        """
        if not question or not question.strip():
            return {
                "answer": "Please provide a search question or query.",
                "citations": [],
                "matched_records": []
            }

        # Step 1: Run keyword search to find relevant candidate meetings
        search_res = self.search_all(question)
        candidate_meeting_ids = list(search_res["linked_meetings"].keys())

        # If keyword search didn't find specific hits, fetch all recent meetings to search across
        if not candidate_meeting_ids:
            all_meetings = self.db.get_all_meetings()
            candidate_meeting_ids = [m["id"] for m in all_meetings[:max_meetings]]

        if not candidate_meeting_ids:
            return {
                "answer": "No meeting records found in the repository to search across.",
                "citations": [],
                "matched_records": []
            }

        # Step 2: Build aggregated context for LLM
        contexts = []
        cited_meetings = []

        for m_id in candidate_meeting_ids[:max_meetings]:
            meeting = self.db.get_meeting(m_id)
            if not meeting:
                continue

            cited_meetings.append({
                "id": meeting["id"],
                "title": meeting["title"],
                "created_at": meeting.get("created_at", "")
            })

            decisions_str = "\n".join([f"- {d}" for d in meeting.get("decisions", [])]) or "None recorded"
            actions_str = "\n".join([
                f"- Action: {a.get('action')} | Assignee: {a.get('owner', 'Unassigned')} | Deadline: {a.get('deadline', 'None')} | Priority: {a.get('priority')} | Status: {a.get('status')}"
                for a in meeting.get("action_items", [])
            ]) or "None recorded"
            parts_str = ", ".join([p.get("canonical_name", p.get("name", "Unknown")) for p in meeting.get("participants", [])]) or "None recorded"

            m_context = (
                f"### Meeting: {meeting['title']} (ID: {meeting['id']})\n"
                f"Date: {meeting.get('created_at', 'N/A')}\n"
                f"Participants: {parts_str}\n"
                f"Summary: {meeting.get('summary', 'No summary.')}\n"
                f"Decisions:\n{decisions_str}\n"
                f"Action Items:\n{actions_str}\n"
                f"Transcript Excerpt: {meeting.get('transcript_text', '')[:600]}...\n"
            )
            contexts.append(m_context)

        full_context_text = "\n---\n".join(contexts)

        # Step 3: Call LLM if available
        if self.llm:
            try:
                system_prompt = (
                    "You are an AI Meeting Knowledge Assistant. Answer the user's question accurately "
                    "based ONLY on the provided historical meeting records. "
                    "Always explicitly cite which meeting title and ID the information came from. "
                    "If the answer is not present in the records, state that clearly without hallucinating."
                )
                user_prompt = (
                    f"Question: {question}\n\n"
                    f"Historical Meeting Records:\n"
                    f"{full_context_text}\n\n"
                    f"Please provide a structured, concise response with bullet points and citations:"
                )
                prompt_to_send = f"{system_prompt}\n\n{user_prompt}"
                if hasattr(self.llm, "generate"):
                    response_text = self.llm.generate(prompt=user_prompt, system_prompt=system_prompt, temperature=0.2)
                elif hasattr(self.llm, "_call_llm_with_retry"):
                    response_text = self.llm._call_llm_with_retry(prompt_to_send)
                else:
                    response_text = str(self.llm(prompt_to_send))

                return {
                    "answer": response_text,
                    "citations": cited_meetings,
                    "matched_records": search_res.get("entities", {})
                }
            except Exception as e:
                logger.warning(f"LLM generation failed: {e}. Falling back to structured search summary.")

        # Fallback without LLM: Synthesize structured summary
        summary_lines = [
            f"**Search Results for:** *'{question}'*",
            f"Found **{search_res['total_matches']} relevant items** across **{len(cited_meetings)} meetings**:\n"
        ]
        for m in cited_meetings:
            summary_lines.append(f"- 📁 **{m['title']}** (`{m['id']}`) - Date: `{m.get('created_at', 'N/A')}`")

        return {
            "answer": "\n".join(summary_lines),
            "citations": cited_meetings,
            "matched_records": search_res.get("entities", {})
        }

    # =========================================================================
    # 4. RECORD LINKAGE & INTEGRITY VERIFICATION (Milestone 3 Task 1 Requirement)
    # =========================================================================

    def verify_records_linkage(self) -> Dict[str, Any]:
        """
        Verify that existing database records can be retrieved correctly and linked
        to the corresponding meeting (Explicit Milestone 3 Task 1 requirement).
        
        Returns:
            Dict with health status, verification details, and complete entity linkage map.
        """
        base_integrity = self.db.verify_database_integrity()
        
        # Verify each meeting's bidirectional linkage
        all_meetings = self.db.get_all_meetings()
        verified_details = []

        for m in all_meetings:
            m_id = m["id"]
            meeting = self.db.get_meeting(m_id)
            if not meeting:
                continue

            linked_actions = meeting.get("action_items", [])
            linked_decisions = meeting.get("decisions", [])
            linked_participants = meeting.get("participants", [])
            has_summary = bool(meeting.get("summary"))

            # Verify every action item links back to this meeting_id
            actions_valid = all(a.get("meeting_id") == m_id for a in linked_actions)
            # Verify every participant links back to this meeting_id
            parts_valid = all(p.get("meeting_id") == m_id for p in linked_participants)

            verified_details.append({
                "meeting_id": m_id,
                "title": meeting.get("title"),
                "has_transcript": bool(meeting.get("transcript_text")),
                "has_summary": has_summary,
                "decisions_count": len(linked_decisions),
                "actions_count": len(linked_actions),
                "participants_count": len(linked_participants),
                "linkage_valid": actions_valid and parts_valid
            })

        all_linkages_valid = all(v["linkage_valid"] for v in verified_details) and base_integrity["is_healthy"]

        return {
            "is_healthy": all_linkages_valid,
            "total_meetings": len(all_meetings),
            "summary_count": base_integrity["summary_count"],
            "decision_count": base_integrity["decision_count"],
            "action_count": base_integrity["action_count"],
            "participant_count": base_integrity["participant_count"],
            "orphans": base_integrity["orphans"],
            "meetings_verified": len(verified_details),
            "verification_details": verified_details,
            "verified_at": datetime.now().isoformat()
        }

    def get_meeting_knowledge_graph(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve complete interconnected knowledge graph for a specific meeting.
        """
        meeting = self.db.get_meeting(meeting_id)
        if not meeting:
            return None

        # Build structured graph
        graph = {
            "metadata": {
                "id": meeting["id"],
                "title": meeting["title"],
                "original_filename": meeting.get("original_filename"),
                "duration": meeting.get("duration", 0),
                "created_at": meeting.get("created_at")
            },
            "transcript": {
                "text": meeting.get("transcript_text", ""),
                "length": len(meeting.get("transcript_text", ""))
            },
            "summary": meeting.get("summary", ""),
            "decisions": meeting.get("decisions", []),
            "action_items": meeting.get("action_items", []),
            "participants": meeting.get("participants", []),
            "deadlines": [
                a for a in meeting.get("action_items", [])
                if a.get("deadline") and a["deadline"].strip().lower() != "none"
            ]
        }
        return graph

    # =========================================================================
    # 5. SEMANTIC VECTOR SEARCH & EMBEDDING MANAGEMENT (Milestone 3 Task 2)
    # =========================================================================

    def generate_embeddings_for_meeting(self, meeting_id: str) -> int:
        """
        Dynamically generate and persist embeddings for all 4 entity types of a meeting:
        - Transcript sections
        - Summaries
        - Decisions
        - Action items
        
        Args:
            meeting_id: Target meeting identifier.
            
        Returns:
            Number of generated and saved embedding records.
        """
        meeting = self.db.get_meeting(meeting_id)
        if not meeting:
            return 0

        # Delete existing embeddings for this meeting to prevent duplicates on regeneration
        self.db.delete_embeddings_for_meeting(meeting_id)

        all_records = self.embedder.generate_all_meeting_embeddings(
            meeting_id=meeting_id,
            transcript_text=meeting.get("transcript_text", ""),
            summary_text=meeting.get("summary", ""),
            decisions=meeting.get("decisions", []),
            action_items=meeting.get("action_items", [])
        )

        saved = self.db.save_embeddings(all_records)
        logger.info(f"Generated & saved {saved} embeddings for meeting_id={meeting_id}")
        return saved

    def generate_all_missing_embeddings(self) -> int:
        """
        Scan all persisted meetings in database and generate embeddings for any meetings
        that currently lack embeddings.
        
        Returns:
            Total count of generated embeddings across all backfilled meetings.
        """
        all_meetings = self.db.get_all_meetings()
        total_generated = 0

        for m in all_meetings:
            m_id = m["id"]
            existing = self.db.get_embeddings_for_meeting(m_id)
            if not existing:
                total_generated += self.generate_embeddings_for_meeting(m_id)

        return total_generated

    def semantic_search(
        self,
        query: str,
        entity_types: Optional[List[str]] = None,
        top_k: int = 10,
        min_score: float = 0.15
    ) -> List[Dict[str, Any]]:
        """
        Execute semantic vector search using cosine similarity across all stored embeddings.
        
        Args:
            query: Natural language search query or concept.
            entity_types: Filter by entity type ('transcript_section', 'summary', 'decision', 'action_item').
            top_k: Max results to return.
            min_score: Minimum similarity score threshold.
            
        Returns:
            List of ranked matches with similarity score, text snippet, and linked meeting information.
        """
        if not query or not query.strip():
            return []

        # If no embeddings exist yet in DB, try to dynamically backfill once
        all_embeddings = self.db.get_all_embeddings()
        if not all_embeddings:
            self.generate_all_missing_embeddings()
            all_embeddings = self.db.get_all_embeddings()

        if not all_embeddings:
            return []

        # Filter by entity types if specified
        if entity_types and "all" not in [t.lower() for t in entity_types]:
            target_types = set(entity_types)
            candidate_embeddings = [e for e in all_embeddings if e.get("entity_type") in target_types]
        else:
            candidate_embeddings = all_embeddings

        # Generate query vector
        query_vector = self.embedder.generate_embedding(query.strip())

        # Rank candidates by cosine similarity
        ranked_results = self.embedder.rank_embeddings(
            query_vector=query_vector,
            candidate_embeddings=candidate_embeddings,
            top_k=top_k,
            min_score=min_score
        )

        return ranked_results

    def get_repository_stats(self) -> Dict[str, Any]:
        """Get aggregate intelligence statistics across the entire knowledge base."""
        integrity = self.db.verify_database_integrity()
        all_meetings = self.db.get_all_meetings()
        meetings_with_embs = 0
        for m in all_meetings:
            if len(self.db.get_embeddings_for_meeting(m["id"])) > 0:
                meetings_with_embs += 1

        return {
            "total_meetings": integrity["meeting_count"],
            "total_summaries": integrity["summary_count"],
            "total_decisions": integrity["decision_count"],
            "total_action_items": integrity["action_count"],
            "total_participants": integrity["participant_count"],
            "total_embeddings": integrity.get("embedding_count", 0),
            "meetings_with_embeddings": meetings_with_embs,
            "database_healthy": integrity["is_healthy"]
        }

    # =========================================================================
    # INTERNAL HELPERS
    # =========================================================================

    def _extract_snippets(self, text: str, query: str, radius: int = 100) -> List[str]:
        """Extract matching context snippets around query occurrences."""
        if not text or not query:
            return []

        snippets = []
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        matches = list(pattern.finditer(text))

        for match in matches[:5]:  # Limit to top 5 snippets per record
            start = max(0, match.start() - radius)
            end = min(len(text), match.end() + radius)
            prefix = "..." if start > 0 else ""
            suffix = "..." if end < len(text) else ""
            snippet = f"{prefix}{text[start:end].strip()}{suffix}"
            snippets.append(snippet)

        return snippets
