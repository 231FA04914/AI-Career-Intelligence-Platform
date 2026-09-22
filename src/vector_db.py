"""
Vector Database Layer & Store Manager (Milestone 3 - Task 3)
Integrates vector storage, indexing, nearest-neighbor similarity search,
metadata filtering, and verified meeting-to-vector traceability.

Core Capabilities:
- Insert embeddings (single & batch)
- Update embeddings (vector, text, metadata)
- Delete embeddings (by vector ID, entity ID, or meeting ID)
- Similarity search (cosine similarity ranking with score thresholds)
- Metadata filtering (multi-field faceted filtering across entities, assignees, priorities, etc.)
- Meeting-to-vector mapping & reverse traceability
- Complete traceability verification audit
"""

import json
import math
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union, Callable

from src.database import DatabaseManager
from src.embeddings import EmbeddingGenerator

logger = logging.getLogger(__name__)


class VectorDatabase:
    """
    Dedicated Vector Database Manager and Store.
    Provides vector indexing, CRUD operations, similarity search with metadata filtering,
    and bidirectional meeting-to-vector traceability.
    """

    def __init__(
        self,
        db_manager: Optional[DatabaseManager] = None,
        embedding_generator: Optional[EmbeddingGenerator] = None
    ):
        """
        Initialize the Vector Database.
        
        Args:
            db_manager: Persistent database manager instance.
            embedding_generator: Service for generating query embeddings.
        """
        self.db = db_manager or DatabaseManager()
        self.embedder = embedding_generator or EmbeddingGenerator()
        logger.info("Initialized VectorDatabase engine")

    # =========================================================================
    # 1. INSERT EMBEDDINGS (Milestone 3 - Task 3)
    # =========================================================================

    def insert(
        self,
        meeting_id: str,
        entity_type: str,
        text_content: str,
        vector: Optional[List[float]] = None,
        entity_id: Optional[str] = None,
        section_index: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
        vector_id: Optional[str] = None,
        model_name: Optional[str] = None
    ) -> str:
        """
        Insert a single embedding vector with rich metadata.
        If vector is omitted, it is generated dynamically from text_content.
        
        Returns:
            Inserted vector_id string.
        """
        v_id = vector_id or f"vec_{uuid.uuid4().hex[:10]}"
        vec = vector if vector is not None else self.embedder.generate_embedding(text_content)
        meta = metadata or {}
        model = model_name or getattr(self.embedder, "model", "dense-embedding")

        record = {
            "id": v_id,
            "meeting_id": meeting_id,
            "entity_type": entity_type,
            "entity_id": entity_id or v_id,
            "section_index": section_index,
            "text_content": text_content,
            "embedding_vector": vec,
            "dimension": len(vec),
            "model_name": model,
            "metadata": meta
        }

        self.db.save_embeddings([record])
        logger.info(f"Inserted vector {v_id} for meeting {meeting_id} (entity={entity_type})")
        return v_id

    def insert_batch(self, records: List[Dict[str, Any]]) -> int:
        """
        Insert multiple embedding vectors in a single transaction.
        
        Args:
            records: List of dictionaries with required fields:
                     ['meeting_id', 'entity_type', 'text_content', optional 'embedding_vector', 'metadata']
                     
        Returns:
            Count of successfully inserted vectors.
        """
        if not records:
            return 0

        prepared_records = []
        for r in records:
            v_id = r.get("id") or f"vec_{uuid.uuid4().hex[:10]}"
            text = r.get("text_content", "")
            vec = r.get("embedding_vector")
            if vec is None:
                vec = self.embedder.generate_embedding(text)

            meta = r.get("metadata") or {}
            model = r.get("model_name") or getattr(self.embedder, "model", "dense-embedding")

            prepared_records.append({
                "id": v_id,
                "meeting_id": r["meeting_id"],
                "entity_type": r["entity_type"],
                "entity_id": r.get("entity_id", v_id),
                "section_index": r.get("section_index", 0),
                "text_content": text,
                "embedding_vector": vec,
                "dimension": len(vec),
                "model_name": model,
                "metadata": meta
            })

        count = self.db.save_embeddings(prepared_records)
        logger.info(f"Batch inserted {count} vectors into VectorDatabase")
        return count

    # =========================================================================
    # 2. UPDATE EMBEDDINGS (Milestone 3 - Task 3)
    # =========================================================================

    def update(
        self,
        vector_id: str,
        new_vector: Optional[List[float]] = None,
        new_text: Optional[str] = None,
        new_metadata: Optional[Dict[str, Any]] = None,
        recompute_vector: bool = False
    ) -> bool:
        """
        Update an existing embedding vector, text content, and/or metadata.
        
        Args:
            vector_id: ID of vector to update.
            new_vector: Optional updated vector array.
            new_text: Optional updated text content.
            new_metadata: Optional updated metadata dictionary.
            recompute_vector: If True and new_text is provided without new_vector, re-embeds new_text.
            
        Returns:
            True if updated successfully, False otherwise.
        """
        if recompute_vector and new_text and new_vector is None:
            new_vector = self.embedder.generate_embedding(new_text)

        success = self.db.update_embedding(
            vector_id=vector_id,
            new_vector=new_vector,
            new_text=new_text,
            new_metadata=new_metadata
        )
        if success:
            logger.info(f"Updated vector record {vector_id}")
        return success

    # =========================================================================
    # 3. DELETE EMBEDDINGS (Milestone 3 - Task 3)
    # =========================================================================

    def delete(self, vector_id: str) -> bool:
        """Delete a single embedding vector by its ID."""
        return self.db.delete_embedding_by_id(vector_id)

    def delete_by_meeting(self, meeting_id: str) -> int:
        """Delete all embedding vectors associated with a meeting ID."""
        return self.db.delete_embeddings_for_meeting(meeting_id)

    def delete_by_entity(self, meeting_id: str, entity_type: str) -> int:
        """Delete all vectors for a specific entity type within a meeting."""
        vectors = self.get_vectors_for_meeting(meeting_id, entity_type=entity_type)
        deleted = 0
        for v in vectors:
            if self.delete(v["id"]):
                deleted += 1
        return deleted

    # =========================================================================
    # 4. SIMILARITY SEARCH & METADATA FILTERING (Milestone 3 - Task 3)
    # =========================================================================

    def similarity_search(
        self,
        query: Union[str, List[float]],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        min_similarity: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Search for nearest neighbor vectors with flexible metadata filtering.
        
        Args:
            query: Either a query text string (automatically embedded) or a query float vector.
            top_k: Max results to return.
            filters: Dictionary of metadata filter criteria, e.g.:
                     {
                         "meeting_id": "meet_123",
                         "entity_type": "action_item",
                         "owner": "Ravi",
                         "priority": "High",
                         "status": "Pending"
                     }
            min_similarity: Minimum cosine similarity score threshold.
            
        Returns:
            List of ranked results with similarity scores, meeting metadata, and text content.
        """
        # 1. Resolve query vector
        if isinstance(query, str):
            if not query.strip():
                return []
            query_vector = self.embedder.generate_embedding(query.strip())
        else:
            query_vector = query

        # 2. Fetch all candidates from persistent database
        candidates = self.db.get_all_embeddings()
        if not candidates:
            return []

        # 3. Apply metadata filtering
        filtered_candidates = []
        for cand in candidates:
            if self._matches_filters(cand, filters):
                filtered_candidates.append(cand)

        if not filtered_candidates:
            return []

        # 4. Compute cosine similarity & rank
        results = []
        for cand in filtered_candidates:
            cand_vec = cand.get("embedding_vector")
            if not cand_vec:
                continue

            if isinstance(cand_vec, str):
                try:
                    cand_vec = json.loads(cand_vec)
                except Exception:
                    continue

            score = self.embedder.compute_cosine_similarity(query_vector, cand_vec)
            if score >= min_similarity:
                item = dict(cand)
                item["similarity_score"] = round(score, 4)
                results.append(item)

        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:top_k]

    def _matches_filters(self, candidate: Dict[str, Any], filters: Optional[Dict[str, Any]]) -> bool:
        """Check if candidate vector matches provided metadata filters."""
        if not filters:
            return True

        # Extract direct candidate fields & nested metadata
        cand_meta = candidate.get("metadata") or {}
        if isinstance(cand_meta, str):
            try:
                cand_meta = json.loads(cand_meta)
            except Exception:
                cand_meta = {}

        for key, expected_val in filters.items():
            if expected_val is None or expected_val == "All":
                continue

            # Check direct top-level fields (e.g. meeting_id, entity_type)
            actual_val = candidate.get(key)
            if actual_val is None:
                # Check nested metadata (e.g. owner, priority, status)
                actual_val = cand_meta.get(key)

            if actual_val is None:
                return False

            if isinstance(expected_val, list):
                if actual_val not in expected_val:
                    return False
            elif isinstance(expected_val, str) and isinstance(actual_val, str):
                if expected_val.lower() != actual_val.lower():
                    return False
            else:
                if actual_val != expected_val:
                    return False

        return True

    # =========================================================================
    # 5. MEETING-TO-VECTOR MAPPING & REVERSE TRACEABILITY (Milestone 3 - Task 3)
    # =========================================================================

    def get_vectors_for_meeting(
        self,
        meeting_id: str,
        entity_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Meeting-to-Vector Mapping:
        Retrieve all vectors belonging to a specific meeting ID.
        """
        return self.db.get_embeddings_for_meeting(meeting_id, entity_type=entity_type)

    def trace_vector_to_meeting(self, vector_id: str) -> Optional[Dict[str, Any]]:
        """
        Reverse Traceability:
        Given any vector ID, trace back to its exact parent meeting record,
        including meeting title, duration, date, source filename, and entity payload.
        
        Returns:
            Dictionary containing full meeting context and linked vector details.
        """
        vec_record = self.db.get_embedding_by_id(vector_id)
        if not vec_record:
            return None

        meeting_id = vec_record["meeting_id"]
        meeting = self.db.get_meeting(meeting_id)
        if not meeting:
            return {
                "vector_id": vector_id,
                "meeting_id": meeting_id,
                "is_orphaned": True,
                "vector_record": vec_record,
                "meeting": None
            }

        return {
            "vector_id": vector_id,
            "meeting_id": meeting_id,
            "meeting_title": meeting["title"],
            "meeting_created_at": meeting.get("created_at"),
            "original_filename": meeting.get("original_filename"),
            "duration": meeting.get("duration", 0),
            "entity_type": vec_record["entity_type"],
            "entity_id": vec_record.get("entity_id"),
            "section_index": vec_record.get("section_index", 0),
            "text_content": vec_record["text_content"],
            "dimension": vec_record["dimension"],
            "model_name": vec_record["model_name"],
            "is_orphaned": False,
            "full_meeting": meeting
        }

    def verify_traceability(self) -> Dict[str, Any]:
        """
        Verify that EVERY stored vector can be traced back to the correct meeting.
        (Explicit Milestone 3 Task 3 Requirement).
        
        Returns:
            Dictionary with audit results, total vector counts, orphan count,
            and verification status.
        """
        all_vectors = self.db.get_all_embeddings()
        all_meetings = {m["id"]: m for m in self.db.get_all_meetings()}

        total_vectors = len(all_vectors)
        validly_traced = 0
        orphans = []
        vectors_by_meeting = {}

        for vec in all_vectors:
            v_id = vec["id"]
            m_id = vec["meeting_id"]

            if m_id in all_meetings:
                validly_traced += 1
                if m_id not in vectors_by_meeting:
                    vectors_by_meeting[m_id] = {
                        "meeting_title": all_meetings[m_id]["title"],
                        "vector_count": 0,
                        "entity_types": set()
                    }
                vectors_by_meeting[m_id]["vector_count"] += 1
                vectors_by_meeting[m_id]["entity_types"].add(vec["entity_type"])
            else:
                orphans.append({
                    "vector_id": v_id,
                    "invalid_meeting_id": m_id,
                    "entity_type": vec.get("entity_type")
                })

        for m_id in vectors_by_meeting:
            vectors_by_meeting[m_id]["entity_types"] = sorted(list(vectors_by_meeting[m_id]["entity_types"]))

        is_100_percent_traced = (total_vectors == validly_traced) and (len(orphans) == 0)

        return {
            "is_valid": is_100_percent_traced,
            "total_vectors": total_vectors,
            "validly_traced_vectors": validly_traced,
            "orphan_count": len(orphans),
            "orphans": orphans,
            "total_meetings_indexed": len(vectors_by_meeting),
            "meeting_mappings": vectors_by_meeting,
            "audited_at": datetime.now().isoformat()
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get aggregate Vector Database statistics."""
        audit = self.verify_traceability()
        return {
            "total_vectors": audit["total_vectors"],
            "total_meetings_indexed": audit["total_meetings_indexed"],
            "traceability_verified": audit["is_valid"],
            "orphan_vectors": audit["orphan_count"]
        }
