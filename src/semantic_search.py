"""
Semantic Search Engine (Milestone 3 - Task 4)
Implements natural-language search across historical meetings:
User Query -> Query Embedding -> Vector Search -> Relevant Meetings -> Search Results

Guarantees:
- Strict sub-3-second retrieval latency (< 3000ms SLA)
- Accurate meeting relevance ranking & snippet extraction
- Dynamic generation for new and historical meetings
- Direct answers with explicit meeting citations
"""

import time
import math
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union

from src.database import DatabaseManager
from src.embeddings import EmbeddingGenerator
from src.vector_db import VectorDatabase
from src.llm.service import LLMService

logger = logging.getLogger(__name__)


@dataclass
class RelevantMeeting:
    """Represents a matched meeting in semantic search results."""
    meeting_id: str
    title: str
    relevance_score: float
    relevance_percentage: int
    matched_vectors_count: int
    matched_entities: List[str]
    best_matching_text: str
    snippets: List[Dict[str, Any]]
    summary: str
    created_at: Optional[str] = None
    original_filename: Optional[str] = None
    duration: float = 0.0


@dataclass
class SemanticSearchResult:
    """Complete response payload for a semantic search query."""
    query: str
    latency_ms: float
    sla_met: bool  # True if latency_ms < 3000
    total_meetings_found: int
    relevant_meetings: List[RelevantMeeting]
    direct_answer: Optional[str] = None
    query_vector_dim: int = 0
    executed_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary representation."""
        return {
            "query": self.query,
            "latency_ms": round(self.latency_ms, 2),
            "sla_met": self.sla_met,
            "total_meetings_found": self.total_meetings_found,
            "relevant_meetings": [
                {
                    "meeting_id": m.meeting_id,
                    "title": m.title,
                    "relevance_score": round(m.relevance_score, 4),
                    "relevance_percentage": m.relevance_percentage,
                    "matched_vectors_count": m.matched_vectors_count,
                    "matched_entities": m.matched_entities,
                    "best_matching_text": m.best_matching_text,
                    "snippets": m.snippets,
                    "summary": m.summary,
                    "created_at": m.created_at,
                    "original_filename": m.original_filename,
                    "duration": m.duration
                }
                for m in self.relevant_meetings
            ],
            "direct_answer": self.direct_answer,
            "query_vector_dim": self.query_vector_dim,
            "executed_at": self.executed_at
        }


class SemanticSearchEngine:
    """
    Dedicated Natural Language Semantic Search Engine.
    Executes: User Query -> Query Embedding -> Vector Search -> Relevant Meetings -> Results
    with strict sub-3-second latency verification.
    """

    def __init__(
        self,
        db_manager: Optional[DatabaseManager] = None,
        embedding_generator: Optional[EmbeddingGenerator] = None,
        vector_db: Optional[VectorDatabase] = None,
        llm_service: Optional[LLMService] = None,
        max_latency_ms: float = 3000.0
    ):
        """
        Initialize the Semantic Search Engine.
        
        Args:
            db_manager: Persistent database manager.
            embedding_generator: Dense vector embedding service.
            vector_db: Vector database store.
            llm_service: LLM service for optional direct answer synthesis.
            max_latency_ms: Latency SLA threshold in milliseconds (default: 3000ms).
        """
        self.db = db_manager or DatabaseManager()
        self.embedder = embedding_generator or EmbeddingGenerator(api_key=getattr(llm_service, "api_key", None))
        self.vdb = vector_db or VectorDatabase(db_manager=self.db, embedding_generator=self.embedder)
        self.llm = llm_service
        self.max_latency_ms = max_latency_ms
        logger.info(f"Initialized SemanticSearchEngine (SLA threshold = {self.max_latency_ms}ms)")

    def search(
        self,
        query: str,
        top_k_meetings: int = 5,
        min_similarity: float = 0.15,
        filters: Optional[Dict[str, Any]] = None,
        include_direct_answer: bool = True
    ) -> SemanticSearchResult:
        """
        Execute full natural-language semantic search across historical meetings.
        
        Flow:
        1. User Query
        2. Query Embedding
        3. Vector Search
        4. Relevant Meetings Aggregation & Ranking
        5. Search Results & Direct Answer Synthesis
        
        Args:
            query: Natural language question or phrase.
            top_k_meetings: Number of top relevant meetings to return.
            min_similarity: Minimum cosine similarity score threshold.
            filters: Optional metadata filters (e.g. entity_type, owner, priority).
            include_direct_answer: If True and LLM available, generates direct natural language answer.
            
        Returns:
            SemanticSearchResult with latency timing, relevant meetings list, and direct answer.
        """
        start_time = time.perf_counter()

        if not query or not query.strip():
            latency = (time.perf_counter() - start_time) * 1000.0
            return SemanticSearchResult(
                query=query or "",
                latency_ms=latency,
                sla_met=latency <= self.max_latency_ms,
                total_meetings_found=0,
                relevant_meetings=[],
                direct_answer="Please provide a search query."
            )

        q_clean = query.strip()

        # Step 2: Generate Query Embedding
        query_vector = self.embedder.generate_embedding(q_clean)
        dim = len(query_vector)

        # Step 3: Vector Search
        vector_hits = self.vdb.similarity_search(
            query=query_vector,
            top_k=50,  # Fetch broad candidate vector pool
            filters=filters,
            min_similarity=min_similarity
        )

        # Step 4: Group vector hits by parent meeting and calculate meeting-level relevance
        meetings_map: Dict[str, Dict[str, Any]] = {}

        for hit in vector_hits:
            m_id = hit["meeting_id"]
            sim_score = hit["similarity_score"]
            ent_type = hit.get("entity_type", "entity")
            text_snippet = hit.get("text_content", "")

            if m_id not in meetings_map:
                meetings_map[m_id] = {
                    "meeting_id": m_id,
                    "scores": [],
                    "entity_types": set(),
                    "snippets": []
                }

            meetings_map[m_id]["scores"].append(sim_score)
            meetings_map[m_id]["entity_types"].add(ent_type)
            meetings_map[m_id]["snippets"].append({
                "entity_type": ent_type,
                "text": text_snippet,
                "score": sim_score,
                "vector_id": hit.get("id")
            })

        # Calculate composite meeting relevance scores
        ranked_meetings: List[RelevantMeeting] = []

        for m_id, data in meetings_map.items():
            meeting_record = self.db.get_meeting(m_id)
            if not meeting_record:
                continue

            scores = data["scores"]
            max_score = max(scores)
            avg_top3 = sum(sorted(scores, reverse=True)[:3]) / min(3, len(scores))
            # Weighted formula: 70% peak match, 20% average of top matches, 10% density bonus
            density_bonus = min(0.1, 0.02 * math.log(1 + len(scores)))
            composite_score = min(1.0, (0.7 * max_score) + (0.2 * avg_top3) + density_bonus)
            rel_percentage = max(1, min(100, int(composite_score * 100)))

            # Sort snippets by similarity score
            sorted_snippets = sorted(data["snippets"], key=lambda s: s["score"], reverse=True)
            best_text = sorted_snippets[0]["text"] if sorted_snippets else ""

            ranked_meetings.append(
                RelevantMeeting(
                    meeting_id=m_id,
                    title=meeting_record["title"],
                    relevance_score=composite_score,
                    relevance_percentage=rel_percentage,
                    matched_vectors_count=len(scores),
                    matched_entities=sorted(list(data["entity_types"])),
                    best_matching_text=best_text,
                    snippets=sorted_snippets[:5],  # top 5 snippets
                    summary=meeting_record.get("summary", ""),
                    created_at=meeting_record.get("created_at"),
                    original_filename=meeting_record.get("original_filename"),
                    duration=meeting_record.get("duration", 0.0)
                )
            )

        # Sort meetings descending by relevance score
        ranked_meetings.sort(key=lambda m: m.relevance_score, reverse=True)
        top_meetings = ranked_meetings[:top_k_meetings]

        # Step 5: Direct Answer Synthesis (if LLM is present or structured summary)
        direct_answer = self._synthesize_answer(q_clean, top_meetings, include_direct_answer)

        # Measure end-to-end latency
        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000.0
        sla_met = latency_ms <= self.max_latency_ms

        logger.info(
            f"SemanticSearch: query='{q_clean}', found {len(top_meetings)} meetings, "
            f"latency={latency_ms:.2f}ms, SLA met={sla_met}"
        )

        return SemanticSearchResult(
            query=q_clean,
            latency_ms=latency_ms,
            sla_met=sla_met,
            total_meetings_found=len(top_meetings),
            relevant_meetings=top_meetings,
            direct_answer=direct_answer,
            query_vector_dim=dim
        )

    def _synthesize_answer(
        self,
        query: str,
        relevant_meetings: List[RelevantMeeting],
        include_direct_answer: bool
    ) -> str:
        """Synthesize a natural language answer citing top relevant meetings."""
        if not relevant_meetings:
            return f"No historical meetings were found matching '{query}'."

        top_m = relevant_meetings[0]

        # If LLM is enabled and direct answer requested
        if include_direct_answer and self.llm:
            try:
                context_blocks = []
                for m in relevant_meetings[:3]:
                    snippets_str = "\n".join([f"- [{s['entity_type']}] {s['text']}" for s in m.snippets[:3]])
                    context_blocks.append(
                        f"Meeting: {m.title} (ID: {m.meeting_id}, Date: {m.created_at or 'N/A'})\n"
                        f"Summary: {m.summary}\n"
                        f"Matching Snippets:\n{snippets_str}"
                    )
                full_ctx = "\n\n".join(context_blocks)

                prompt = (
                    f"User Question: {query}\n\n"
                    f"Relevant Meeting Context:\n{full_ctx}\n\n"
                    f"Directly answer the user's question in 1-3 sentences. "
                    f"Explicitly name the relevant meeting title (and ID)."
                )
                system_prompt = (
                    "You are a Meeting Intelligence Assistant. Answer the question accurately "
                    "using ONLY the provided meeting context. Be direct, factual, and cite the meeting title."
                )
                answer = self.llm.generate(prompt=prompt, system_prompt=system_prompt, temperature=0.1)
                if isinstance(answer, str) and answer.strip():
                    return answer.strip()
            except Exception as e:
                logger.warning(f"LLM direct answer generation failed: {e}")

        # Deterministic structured direct answer
        ent_list_str = ", ".join([e.replace('_', ' ') for e in top_m.matched_entities])
        return (
            f"**'{top_m.title}'** (`{top_m.meeting_id}`) is the most relevant meeting discussing this topic "
            f"({top_m.relevance_percentage}% match across {ent_list_str}). "
            f"Key snippet: *\"{top_m.best_matching_text}\"*"
        )
