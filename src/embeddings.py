"""
Embedding Generation Engine (Milestone 3 - Task 2)
Generates semantic embeddings for:
- Transcript sections (intelligent chunking & indexing)
- Summaries (executive conceptual embeddings)
- Decisions (organizational decision vectors)
- Action items (task description, assignee, and priority embeddings)

Supports dynamic generation, cosine similarity ranking, and database linkage.
"""

import os
import re
import math
import json
import uuid
import logging
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)


STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "can't", "cannot", "could",
    "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down",
    "during", "each", "few", "for", "from", "further", "had", "hadn't", "has",
    "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her",
    "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's",
    "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it",
    "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my",
    "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other",
    "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shan't",
    "she", "she'd", "she's", "should", "shouldn't", "so", "some", "such",
    "than", "that", "that's", "the", "their", "theirs", "them", "themselves",
    "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
    "they've", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
    "weren't", "what", "what's", "when", "when's", "where", "where's", "which",
    "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
    "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours",
    "yourself", "yourselves", "meeting", "meetings", "discussed", "discuss", "discussion",
    "tell", "show", "give", "find", "list", "get"
}


class EmbeddingGenerator:
    """
    Service for generating dense vector embeddings for meeting intelligence entities.
    Supports API-based generation (Google Gemini text-embedding-004 / embedding-001)
    with a deterministic normalized dense vector fallback for offline and test execution.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "text-embedding-004",
        dimension: int = 768,
        chunk_size: int = 400,
        chunk_overlap: int = 50
    ):
        """
        Initialize Embedding Generator.
        
        Args:
            api_key: Optional API key for Google Gemini embedding API.
            model: Embedding model name.
            dimension: Target vector dimension.
            chunk_size: Character size for transcript chunking.
            chunk_overlap: Character overlap between consecutive transcript sections.
        """
        if api_key == "" or os.getenv("LOCAL_EMBEDDINGS") == "1":
            self.api_key = ""
        else:
            self.api_key = api_key if api_key is not None else os.getenv("LLM_API_KEY")

        self.model = model
        self.dimension = dimension
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        logger.info(f"Initialized EmbeddingGenerator (model={self.model}, dim={self.dimension})")

    # =========================================================================
    # 1. CORE EMBEDDING GENERATION
    # =========================================================================

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate a single embedding vector for the provided text.
        
        Args:
            text: Input string.
            
        Returns:
            List of floats representing the normalized embedding vector.
        """
        if not text or not text.strip():
            return [0.0] * self.dimension

        cleaned = text.strip()

        # Try Google Gemini Embedding API if API key is present
        if self.api_key and self.api_key.strip():
            try:
                vec = self._call_gemini_embedding(cleaned)
                if vec and len(vec) > 0:
                    return vec
            except Exception as e:
                logger.warning(f"Gemini embedding API call failed: {e}. Falling back to dense vector generator.")

        # Fallback to local dense vector generator
        return self._generate_dense_vector(cleaned)

    def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of text strings.
        
        Args:
            texts: List of input strings.
            
        Returns:
            List of embedding vectors.
        """
        return [self.generate_embedding(t) for t in texts]

    # =========================================================================
    # 2. ENTITY-SPECIFIC EMBEDDING GENERATORS (Milestone 3 Task 2 Requirements)
    # =========================================================================

    def generate_transcript_section_embeddings(
        self,
        meeting_id: str,
        transcript_text: str
    ) -> List[Dict[str, Any]]:
        """
        Chunk meeting transcript into sections and generate an embedding vector for each section.
        
        Args:
            meeting_id: Parent meeting ID.
            transcript_text: Full transcript string.
            
        Returns:
            List of embedding records for transcript sections.
        """
        if not transcript_text or not transcript_text.strip():
            return []

        chunks = self._chunk_text(transcript_text, self.chunk_size, self.chunk_overlap)
        records = []

        for idx, chunk in enumerate(chunks):
            vec = self.generate_embedding(chunk)
            records.append({
                "id": f"emb_{meeting_id}_sec_{idx}_{uuid.uuid4().hex[:6]}",
                "meeting_id": meeting_id,
                "entity_type": "transcript_section",
                "entity_id": f"sec_{idx}",
                "section_index": idx,
                "text_content": chunk,
                "embedding_vector": vec,
                "dimension": len(vec),
                "model_name": self.model,
                "metadata": {
                    "section_index": idx,
                    "char_length": len(chunk)
                }
            })

        logger.info(f"Generated {len(records)} transcript section embeddings for meeting_id={meeting_id}")
        return records

    def generate_summary_embedding(
        self,
        meeting_id: str,
        summary_text: str,
        summary_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Generate embedding for meeting executive summary.
        
        Args:
            meeting_id: Parent meeting ID.
            summary_text: Executive summary string.
            summary_id: Optional summary entity ID.
            
        Returns:
            Embedding record dictionary or None if text is empty.
        """
        if not summary_text or not summary_text.strip():
            return None

        cleaned = summary_text.strip()
        vec = self.generate_embedding(cleaned)

        return {
            "id": f"emb_{meeting_id}_sum_{uuid.uuid4().hex[:6]}",
            "meeting_id": meeting_id,
            "entity_type": "summary",
            "entity_id": summary_id or f"sum_{meeting_id}",
            "section_index": 0,
            "text_content": cleaned,
            "embedding_vector": vec,
            "dimension": len(vec),
            "model_name": self.model,
            "metadata": {
                "summary_type": "executive"
            }
        }

    def generate_decisions_embeddings(
        self,
        meeting_id: str,
        decisions: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Generate an individual embedding vector for each meeting decision.
        
        Args:
            meeting_id: Parent meeting ID.
            decisions: List of decision strings.
            
        Returns:
            List of embedding records for decisions.
        """
        records = []
        for idx, dec in enumerate(decisions):
            if not dec or not str(dec).strip():
                continue
            cleaned = str(dec).strip()
            vec = self.generate_embedding(cleaned)
            records.append({
                "id": f"emb_{meeting_id}_dec_{idx}_{uuid.uuid4().hex[:6]}",
                "meeting_id": meeting_id,
                "entity_type": "decision",
                "entity_id": f"dec_{idx}",
                "section_index": idx,
                "text_content": cleaned,
                "embedding_vector": vec,
                "dimension": len(vec),
                "model_name": self.model,
                "metadata": {
                    "decision_index": idx,
                    "decision_text": cleaned
                }
            })

        logger.info(f"Generated {len(records)} decision embeddings for meeting_id={meeting_id}")
        return records

    def generate_action_items_embeddings(
        self,
        meeting_id: str,
        action_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate embedding vectors for action items enriched with assignee, deadline, and priority.
        
        Args:
            meeting_id: Parent meeting ID.
            action_items: List of action item dicts.
            
        Returns:
            List of embedding records for action items.
        """
        records = []
        for idx, item in enumerate(action_items):
            act_text = item.get("action", "") if isinstance(item, dict) else str(item)
            if not act_text or not act_text.strip():
                continue

            owner = item.get("owner", "Unassigned") if isinstance(item, dict) else "Unassigned"
            deadline = item.get("deadline", "None") if isinstance(item, dict) else "None"
            priority = item.get("priority", "Medium") if isinstance(item, dict) else "Medium"
            status = item.get("status", "Pending") if isinstance(item, dict) else "Pending"
            item_id = item.get("id") if isinstance(item, dict) else f"act_{idx}"

            # Enrich text for semantic embedding
            contextual_text = f"Action Item: {act_text}. Assignee: {owner}. Deadline: {deadline}. Priority: {priority}. Status: {status}."
            vec = self.generate_embedding(contextual_text)

            records.append({
                "id": f"emb_{meeting_id}_act_{idx}_{uuid.uuid4().hex[:6]}",
                "meeting_id": meeting_id,
                "entity_type": "action_item",
                "entity_id": item_id or f"act_{idx}",
                "section_index": idx,
                "text_content": contextual_text,
                "embedding_vector": vec,
                "dimension": len(vec),
                "model_name": self.model,
                "metadata": {
                    "owner": owner,
                    "status": status,
                    "priority": priority,
                    "deadline": deadline,
                    "action": act_text
                }
            })

        logger.info(f"Generated {len(records)} action item embeddings for meeting_id={meeting_id}")
        return records

    def generate_all_meeting_embeddings(
        self,
        meeting_id: str,
        transcript_text: str,
        summary_text: str,
        decisions: List[str],
        action_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Dynamically generate embeddings across all 4 entity types for a complete meeting.
        
        Returns:
            Consolidated list of embedding records ready for database storage.
        """
        all_embeddings = []

        # 1. Transcript sections
        sec_embs = self.generate_transcript_section_embeddings(meeting_id, transcript_text)
        all_embeddings.extend(sec_embs)

        # 2. Summary
        sum_emb = self.generate_summary_embedding(meeting_id, summary_text)
        if sum_emb:
            all_embeddings.append(sum_emb)

        # 3. Decisions
        dec_embs = self.generate_decisions_embeddings(meeting_id, decisions)
        all_embeddings.extend(dec_embs)

        # 4. Action Items
        act_embs = self.generate_action_items_embeddings(meeting_id, action_items)
        all_embeddings.extend(act_embs)

        logger.info(
            f"Consolidated {len(all_embeddings)} embeddings for meeting_id={meeting_id} "
            f"({len(sec_embs)} sections, {1 if sum_emb else 0} summary, {len(dec_embs)} decisions, {len(act_embs)} action items)"
        )
        return all_embeddings

    # =========================================================================
    # 3. VECTOR MATH & COSINE SIMILARITY
    # =========================================================================

    @staticmethod
    def compute_cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """
        Calculate cosine similarity between two float vectors.
        
        Returns:
            Cosine similarity score in range [-1.0, 1.0].
        """
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0

        dot_prod = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))

        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0

        return dot_prod / (norm_a * norm_b)

    def rank_embeddings(
        self,
        query_vector: List[float],
        candidate_embeddings: List[Dict[str, Any]],
        top_k: int = 10,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Rank candidate embedding records by cosine similarity with query vector.
        
        Args:
            query_vector: Vector for user query.
            candidate_embeddings: List of embedding dicts from database.
            top_k: Maximum number of top results to return.
            min_score: Minimum similarity score cutoff.
            
        Returns:
            List of candidate dictionaries sorted by similarity score descending.
        """
        scored_candidates = []

        for candidate in candidate_embeddings:
            cand_vec = candidate.get("embedding_vector")
            if not cand_vec:
                continue

            if isinstance(cand_vec, str):
                try:
                    cand_vec = json.loads(cand_vec)
                except Exception:
                    continue

            score = self.compute_cosine_similarity(query_vector, cand_vec)
            if score >= min_score:
                item = dict(candidate)
                item["similarity_score"] = round(score, 4)
                scored_candidates.append(item)

        # Sort descending by similarity score
        scored_candidates.sort(key=lambda x: x["similarity_score"], reverse=True)
        return scored_candidates[:top_k]

    # =========================================================================
    # 4. INTERNAL UTILITIES & FALLBACKS
    # =========================================================================

    def _call_gemini_embedding(self, text: str) -> Optional[List[float]]:
        """Call Google Gemini REST API for embedding."""
        import requests

        candidate_models = [self.model, "text-embedding-004", "embedding-001"]
        for current_model in candidate_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{current_model}:embedContent?key={self.api_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "model": f"models/{current_model}",
                "content": {
                    "parts": [{"text": text[:2000]}]  # truncate overly long inputs
                }
            }
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=15)
                if resp.status_code == 200:
                    data = resp.json()
                    values = data.get("embedding", {}).get("values")
                    if values:
                        return values
            except Exception:
                continue
        return None

    def _generate_dense_vector(self, text: str) -> List[float]:
        """
        Deterministic, normalized dense vector generator for local/offline embedding.
        Constructs a semantic distribution across character and word n-grams,
        producing unit-normalized dense vectors with consistent cosine similarity properties.
        """
        import hashlib

        vector = [0.0] * self.dimension
        cleaned = re.sub(r'[^\w\s]', ' ', text.lower()).strip()
        words = cleaned.split()

        if not words:
            return vector

        # Content words filter
        content_words = [w for w in words if w not in STOP_WORDS and len(w) > 1]
        active_words = content_words if content_words else words

        # Word-level features
        for w in words:
            is_stop = w in STOP_WORDS
            h = int(hashlib.sha256(w.encode("utf-8")).hexdigest(), 16)
            pos1 = h % self.dimension
            pos2 = (h >> 8) % self.dimension
            pos3 = (h >> 16) % self.dimension

            if not is_stop:
                weight = 3.0 + math.log(len(w) + 1) * 2.0
            else:
                weight = 0.05

            vector[pos1] += weight
            vector[pos2] += weight * 0.5
            vector[pos3] -= weight * 0.25

        # Character trigrams for morphological and fuzzy matching on content words
        for w in active_words:
            padded = f"_{w}_"
            for i in range(len(padded) - 2):
                trigram = padded[i:i+3]
                h_tri = int(hashlib.md5(trigram.encode("utf-8")).hexdigest(), 16)
                pos_tri = h_tri % self.dimension
                vector[pos_tri] += 0.5

        # L2-normalize vector to unit sphere
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0.0:
            vector = [v / norm for v in vector]

        return vector

    def _chunk_text(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        """Split text into overlapping character chunks preserving sentence boundaries."""
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + chunk_size, text_len)
            
            # Try to snap to sentence or word boundary if not at end of text
            if end < text_len:
                last_period = text.rfind(". ", start, end)
                last_space = text.rfind(" ", start, end)
                if last_period != -1 and last_period > start + (chunk_size // 2):
                    end = last_period + 1
                elif last_space != -1 and last_space > start + (chunk_size // 2):
                    end = last_space

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            if end >= text_len:
                break

            start = max(start + 1, end - chunk_overlap)

        return chunks
