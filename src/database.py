"""
Meeting Data Model & Database Persistence Layer (Milestone 2 - Task 5)
SQLite database manager for persisting transcripts, summaries, decisions,
action items, and mapped participants.
"""

import sqlite3
import json
import logging
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    SQLite Database Manager for Meeting Intelligence (Task 5).
    Persists:
    - meetings (id, title, original_filename, transcript_text, duration, created_at)
    - summaries (id, meeting_id, summary_text, created_at)
    - decisions (id, meeting_id, decision_text)
    - action_items (id, meeting_id, action, owner, deadline, priority, status)
    - participants (id, meeting_id, name, canonical_name, role)
    """

    def __init__(self, db_path: str = "data/meeting_intelligence.db"):
        """
        Initialize database connection and create tables.
        
        Args:
            db_path: Path to SQLite database file.
        """
        if not Path(db_path).is_absolute():
            self.db_path = Path(__file__).parent.parent / db_path
        else:
            self.db_path = Path(db_path)
            
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        logger.info(f"Initialized DatabaseManager at {self.db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """Get SQLite connection with foreign keys enabled."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self):
        """Create database tables if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Meetings Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS meetings (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    original_filename TEXT,
                    transcript_text TEXT NOT NULL,
                    duration REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Summaries Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS summaries (
                    id TEXT PRIMARY KEY,
                    meeting_id TEXT NOT NULL,
                    summary_text TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
                );
            """)

            # Decisions Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS decisions (
                    id TEXT PRIMARY KEY,
                    meeting_id TEXT NOT NULL,
                    decision_text TEXT NOT NULL,
                    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
                );
            """)

            # Action Items Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS action_items (
                    id TEXT PRIMARY KEY,
                    meeting_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    owner TEXT,
                    deadline TEXT,
                    priority TEXT DEFAULT 'Medium',
                    status TEXT DEFAULT 'Pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
                );
            """)

            # Participants Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS participants (
                    id TEXT PRIMARY KEY,
                    meeting_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    canonical_name TEXT NOT NULL,
                    role TEXT,
                    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
                );
            """)

            # Embeddings Table (Milestone 3 - Tasks 2 & 3)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    id TEXT PRIMARY KEY,
                    meeting_id TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT,
                    section_index INTEGER DEFAULT 0,
                    text_content TEXT NOT NULL,
                    embedding_vector TEXT NOT NULL,
                    dimension INTEGER NOT NULL,
                    model_name TEXT NOT NULL,
                    metadata_json TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
                );
            """)

            # Ensure metadata_json column exists if table was created in an earlier task
            try:
                cursor.execute("ALTER TABLE embeddings ADD COLUMN metadata_json TEXT DEFAULT '{}';")
            except sqlite3.OperationalError:
                pass  # Column already exists

            conn.commit()

    def save_meeting_intelligence(
        self,
        title: str,
        transcript_text: str,
        summary_text: str,
        decisions: List[str],
        action_items: List[Dict[str, Any]],
        participants: List[Dict[str, Any]],
        original_filename: Optional[str] = None,
        duration: float = 0.0,
        meeting_id: Optional[str] = None,
        created_at: Optional[str] = None
    ) -> str:
        """
        Save complete processed meeting intelligence to database in a single transaction.
        
        Args:
            title: Meeting title/subject.
            transcript_text: Full transcript string.
            summary_text: Executive summary.
            decisions: List of decision strings.
            action_items: List of action item dictionaries.
            participants: List of participant dictionaries or objects.
            original_filename: Source recording filename.
            duration: Audio duration in seconds.
            meeting_id: Optional unique identifier.
            created_at: Optional ISO creation timestamp.
            
        Returns:
            Saved meeting_id string.
        """
        m_id = meeting_id or f"meet_{uuid.uuid4().hex[:10]}"
        created_time = created_at or datetime.now().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 1. Insert Meeting
            cursor.execute("""
                INSERT OR REPLACE INTO meetings (id, title, original_filename, transcript_text, duration, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (m_id, title, original_filename, transcript_text, duration, created_time))

            # 2. Insert Summary
            s_id = f"sum_{uuid.uuid4().hex[:8]}"
            cursor.execute("""
                INSERT INTO summaries (id, meeting_id, summary_text, created_at)
                VALUES (?, ?, ?, ?)
            """, (s_id, m_id, summary_text, created_time))

            # 3. Insert Decisions
            for d in decisions:
                if d and d.strip():
                    d_id = f"dec_{uuid.uuid4().hex[:8]}"
                    cursor.execute("""
                        INSERT INTO decisions (id, meeting_id, decision_text)
                        VALUES (?, ?, ?)
                    """, (d_id, m_id, d.strip()))

            # 4. Insert Action Items
            for item in action_items:
                a_id = item.get("id") or f"act_{uuid.uuid4().hex[:8]}"
                cursor.execute("""
                    INSERT INTO action_items (id, meeting_id, action, owner, deadline, priority, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    a_id,
                    m_id,
                    item.get("action", ""),
                    item.get("owner"),
                    item.get("deadline"),
                    item.get("priority", "Medium"),
                    item.get("status", "Pending"),
                    item.get("created_at", datetime.now().isoformat())
                ))

            # 5. Insert Participants
            for p in participants:
                p_id = f"part_{uuid.uuid4().hex[:8]}"
                p_name = p.get("name") if isinstance(p, dict) else getattr(p, "name", "Unknown")
                if isinstance(p_name, dict):
                    p_name = p_name.get("name") or p_name.get("canonical_name") or "Unknown"
                if not isinstance(p_name, str):
                    p_name = str(p_name) if p_name is not None else "Unknown"

                p_canonical = p.get("canonical_name") if isinstance(p, dict) else getattr(p, "canonical_name", p_name)
                if isinstance(p_canonical, dict):
                    p_canonical = p_canonical.get("canonical_name") or p_canonical.get("name") or p_name
                if not isinstance(p_canonical, str):
                    p_canonical = str(p_canonical) if p_canonical is not None else p_name

                p_role = p.get("role") if isinstance(p, dict) else getattr(p, "role", None)
                if isinstance(p_role, dict):
                    p_role = p_role.get("role")
                if p_role is not None and not isinstance(p_role, str):
                    p_role = str(p_role)

                cursor.execute("""
                    INSERT INTO participants (id, meeting_id, name, canonical_name, role)
                    VALUES (?, ?, ?, ?, ?)
                """, (p_id, m_id, p_name, p_canonical, p_role))

            conn.commit()

        logger.info(f"Successfully saved meeting intelligence for meeting_id={m_id}")
        return m_id

    def get_meeting(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve complete meeting details by ID.
        
        Args:
            meeting_id: Meeting unique identifier.
            
        Returns:
            Dictionary containing meeting record and related sub-records.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,))
            meeting_row = cursor.fetchone()
            if not meeting_row:
                return None

            meeting = dict(meeting_row)

            # Get Summary
            cursor.execute("SELECT summary_text FROM summaries WHERE meeting_id = ? ORDER BY created_at DESC LIMIT 1", (meeting_id,))
            sum_row = cursor.fetchone()
            meeting["summary"] = sum_row["summary_text"] if sum_row else ""

            # Get Decisions
            cursor.execute("SELECT decision_text FROM decisions WHERE meeting_id = ?", (meeting_id,))
            meeting["decisions"] = [row["decision_text"] for row in cursor.fetchall()]

            # Get Action Items
            cursor.execute("SELECT * FROM action_items WHERE meeting_id = ?", (meeting_id,))
            meeting["action_items"] = [dict(row) for row in cursor.fetchall()]

            # Get Participants
            cursor.execute("SELECT * FROM participants WHERE meeting_id = ?", (meeting_id,))
            meeting["participants"] = [dict(row) for row in cursor.fetchall()]

            return meeting

    def get_all_meetings(self) -> List[Dict[str, Any]]:
        """
        Retrieve summary list of all meetings ordered by creation date (newest first).
        
        Returns:
            List of meeting summaries.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT m.id, m.title, m.original_filename, m.duration, m.created_at,
                       (SELECT summary_text FROM summaries WHERE meeting_id = m.id LIMIT 1) as summary,
                       (SELECT COUNT(*) FROM action_items WHERE meeting_id = m.id) as action_item_count,
                       (SELECT COUNT(*) FROM participants WHERE meeting_id = m.id) as participant_count
                FROM meetings m
                ORDER BY m.created_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]

    def get_all_action_items(self, status: Optional[str] = None, owner: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Query action items across all meetings with optional filters.
        
        Args:
            status: Optional filter by status.
            owner: Optional filter by assignee.
            
        Returns:
            List of action items with meeting title.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT a.*, m.title as meeting_title
                FROM action_items a
                JOIN meetings m ON a.meeting_id = m.id
                WHERE 1=1
            """
            params = []
            if status and status != "All":
                query += " AND a.status = ?"
                params.append(status)
            if owner and owner != "All":
                query += " AND a.owner = ?"
                params.append(owner)

            query += " ORDER BY a.created_at DESC"
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def update_action_item_status(self, action_item_id: str, new_status: str) -> bool:
        """Update status of a specific action item."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE action_items SET status = ? WHERE id = ?", (new_status, action_item_id))
            conn.commit()
            return cursor.rowcount > 0

    def search_meetings_raw(self, query: str) -> List[Dict[str, Any]]:
        """Search meeting metadata by keyword in title or filename."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            search_param = f"%{query.strip()}%"
            cursor.execute("""
                SELECT id, title, original_filename, duration, created_at
                FROM meetings
                WHERE title LIKE ? OR original_filename LIKE ?
                ORDER BY created_at DESC
            """, (search_param, search_param))
            return [dict(row) for row in cursor.fetchall()]

    def search_transcripts_raw(self, query: str) -> List[Dict[str, Any]]:
        """Search within full transcript texts and return linked meeting records."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            search_param = f"%{query.strip()}%"
            cursor.execute("""
                SELECT id as meeting_id, title as meeting_title, transcript_text, created_at, original_filename
                FROM meetings
                WHERE transcript_text LIKE ?
                ORDER BY created_at DESC
            """, (search_param,))
            return [dict(row) for row in cursor.fetchall()]

    def search_summaries_raw(self, query: str) -> List[Dict[str, Any]]:
        """Search within executive summaries and return linked meeting metadata."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            search_param = f"%{query.strip()}%"
            cursor.execute("""
                SELECT s.id as summary_id, s.meeting_id, s.summary_text, s.created_at, m.title as meeting_title
                FROM summaries s
                JOIN meetings m ON s.meeting_id = m.id
                WHERE s.summary_text LIKE ?
                ORDER BY s.created_at DESC
            """, (search_param,))
            return [dict(row) for row in cursor.fetchall()]

    def search_decisions_raw(self, query: str) -> List[Dict[str, Any]]:
        """Search within meeting decisions and return linked meeting metadata."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            search_param = f"%{query.strip()}%"
            cursor.execute("""
                SELECT d.id as decision_id, d.meeting_id, d.decision_text, m.title as meeting_title, m.created_at
                FROM decisions d
                JOIN meetings m ON d.meeting_id = m.id
                WHERE d.decision_text LIKE ?
                ORDER BY m.created_at DESC
            """, (search_param,))
            return [dict(row) for row in cursor.fetchall()]

    def search_action_items_raw(
        self,
        query: Optional[str] = None,
        owner: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search action items by keyword, owner, status, and priority."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            sql = """
                SELECT a.*, m.title as meeting_title, m.created_at as meeting_created_at
                FROM action_items a
                JOIN meetings m ON a.meeting_id = m.id
                WHERE 1=1
            """
            params = []
            if query and query.strip():
                sql += " AND (a.action LIKE ? OR a.owner LIKE ? OR a.deadline LIKE ?)"
                p = f"%{query.strip()}%"
                params.extend([p, p, p])
            if owner and owner != "All":
                sql += " AND a.owner LIKE ?"
                params.append(f"%{owner.strip()}%")
            if status and status != "All":
                sql += " AND a.status = ?"
                params.append(status)
            if priority and priority != "All":
                sql += " AND a.priority = ?"
                params.append(priority)

            sql += " ORDER BY a.created_at DESC"
            cursor.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]

    def search_participants_raw(self, query: str) -> List[Dict[str, Any]]:
        """Search participants across meetings with linked meeting information."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            search_param = f"%{query.strip()}%"
            cursor.execute("""
                SELECT p.id as participant_id, p.meeting_id, p.name, p.canonical_name, p.role,
                       m.title as meeting_title, m.created_at as meeting_created_at
                FROM participants p
                JOIN meetings m ON p.meeting_id = m.id
                WHERE p.name LIKE ? OR p.canonical_name LIKE ? OR (p.role IS NOT NULL AND p.role LIKE ?)
                ORDER BY m.created_at DESC
            """, (search_param, search_param, search_param))
            return [dict(row) for row in cursor.fetchall()]

    def search_deadlines_raw(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search non-empty deadlines across action items with linked meeting information."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            sql = """
                SELECT a.id as action_id, a.meeting_id, a.action, a.owner, a.deadline, a.priority, a.status,
                       m.title as meeting_title, m.created_at as meeting_created_at
                FROM action_items a
                JOIN meetings m ON a.meeting_id = m.id
                WHERE a.deadline IS NOT NULL AND TRIM(a.deadline) != '' AND LOWER(a.deadline) != 'none'
            """
            params = []
            if query and query.strip():
                sql += " AND (a.deadline LIKE ? OR a.action LIKE ? OR a.owner LIKE ?)"
                p = f"%{query.strip()}%"
                params.extend([p, p, p])

            sql += " ORDER BY a.created_at DESC"
            cursor.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]

    def verify_database_integrity(self) -> Dict[str, Any]:
        """
        Verify that all database records can be retrieved correctly and linked
        to their corresponding meeting (Milestone 3 Task 1 Requirement).
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 1. Total counts
            cursor.execute("SELECT COUNT(*) FROM meetings")
            meeting_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM summaries")
            summary_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM decisions")
            decision_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM action_items")
            action_count = cursor.fetchone()[0]

    def save_embeddings(self, embeddings_list: List[Dict[str, Any]]) -> int:
        """
        Save a batch of embedding records to database.
        
        Args:
            embeddings_list: List of embedding dictionaries.
            
        Returns:
            Number of saved embeddings.
        """
        if not embeddings_list:
            return 0

        saved_count = 0
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for emb in embeddings_list:
                emb_id = emb.get("id") or f"emb_{uuid.uuid4().hex[:10]}"
                meeting_id = emb["meeting_id"]
                entity_type = emb["entity_type"]
                entity_id = emb.get("entity_id")
                section_idx = emb.get("section_index", 0)
                text_content = emb.get("text_content", "")
                vec = emb["embedding_vector"]
                vec_json = json.dumps(vec) if isinstance(vec, list) else str(vec)
                dim = emb.get("dimension", len(vec) if isinstance(vec, list) else 0)
                model_name = emb.get("model_name", "dense-embedding")
                meta = emb.get("metadata") or emb.get("metadata_json") or {}
                meta_json = json.dumps(meta) if isinstance(meta, dict) else str(meta)

                cursor.execute("""
                    INSERT OR REPLACE INTO embeddings (
                        id, meeting_id, entity_type, entity_id, section_index,
                        text_content, embedding_vector, dimension, model_name, metadata_json, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    emb_id, meeting_id, entity_type, entity_id, section_idx,
                    text_content, vec_json, dim, model_name, meta_json, datetime.now().isoformat()
                ))
                saved_count += 1
            conn.commit()

        logger.info(f"Saved {saved_count} embeddings to database.")
        return saved_count

    def get_embedding_by_id(self, vector_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific embedding record by vector ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT e.*, m.title as meeting_title, m.created_at as meeting_created_at
                FROM embeddings e
                JOIN meetings m ON e.meeting_id = m.id
                WHERE e.id = ?
            """, (vector_id,))
            row = cursor.fetchone()
            if not row:
                return None
            item = dict(row)
            if isinstance(item.get("embedding_vector"), str):
                try:
                    item["embedding_vector"] = json.loads(item["embedding_vector"])
                except Exception:
                    pass
            if isinstance(item.get("metadata_json"), str):
                try:
                    item["metadata"] = json.loads(item["metadata_json"])
                except Exception:
                    item["metadata"] = {}
            else:
                item["metadata"] = item.get("metadata_json") or {}
            return item

    def update_embedding(
        self,
        vector_id: str,
        new_vector: Optional[List[float]] = None,
        new_text: Optional[str] = None,
        new_metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update an existing embedding vector, text content, or metadata.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM embeddings WHERE id = ?", (vector_id,))
            row = cursor.fetchone()
            if not row:
                return False

            updates = []
            params = []

            if new_vector is not None:
                updates.append("embedding_vector = ?")
                updates.append("dimension = ?")
                params.extend([json.dumps(new_vector), len(new_vector)])

            if new_text is not None:
                updates.append("text_content = ?")
                params.append(new_text)

            if new_metadata is not None:
                updates.append("metadata_json = ?")
                params.append(json.dumps(new_metadata))

            if not updates:
                return True

            params.append(vector_id)
            sql = f"UPDATE embeddings SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(sql, params)
            conn.commit()
            return cursor.rowcount > 0

    def delete_embedding_by_id(self, vector_id: str) -> bool:
        """Delete a single embedding record by its ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM embeddings WHERE id = ?", (vector_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_embeddings_for_meeting(
        self,
        meeting_id: str,
        entity_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all embeddings associated with a specific meeting.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM embeddings WHERE meeting_id = ?"
            params = [meeting_id]
            if entity_type and entity_type != "All":
                query += " AND entity_type = ?"
                params.append(entity_type)
            query += " ORDER BY entity_type, section_index ASC"

            cursor.execute(query, params)
            results = []
            for row in cursor.fetchall():
                item = dict(row)
                if isinstance(item.get("embedding_vector"), str):
                    try:
                        item["embedding_vector"] = json.loads(item["embedding_vector"])
                    except Exception:
                        pass
                if isinstance(item.get("metadata_json"), str):
                    try:
                        item["metadata"] = json.loads(item["metadata_json"])
                    except Exception:
                        item["metadata"] = {}
                else:
                    item["metadata"] = item.get("metadata_json") or {}
                results.append(item)
            return results

    def get_all_embeddings(self, entity_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve all embeddings across the entire repository with linked meeting metadata.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT e.*, m.title as meeting_title, m.created_at as meeting_created_at
                FROM embeddings e
                JOIN meetings m ON e.meeting_id = m.id
                WHERE 1=1
            """
            params = []
            if entity_type and entity_type != "All":
                query += " AND e.entity_type = ?"
                params.append(entity_type)
            query += " ORDER BY e.created_at DESC"

            cursor.execute(query, params)
            results = []
            for row in cursor.fetchall():
                item = dict(row)
                if isinstance(item.get("embedding_vector"), str):
                    try:
                        item["embedding_vector"] = json.loads(item["embedding_vector"])
                    except Exception:
                        pass
                if isinstance(item.get("metadata_json"), str):
                    try:
                        item["metadata"] = json.loads(item["metadata_json"])
                    except Exception:
                        item["metadata"] = {}
                else:
                    item["metadata"] = item.get("metadata_json") or {}
                results.append(item)
            return results

    def delete_embeddings_for_meeting(self, meeting_id: str) -> int:
        """Delete all embeddings for a specific meeting."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM embeddings WHERE meeting_id = ?", (meeting_id,))
            conn.commit()
            return cursor.rowcount

    def verify_database_integrity(self) -> Dict[str, Any]:
        """
        Verify that all database records can be retrieved correctly and linked
        to their corresponding meeting (Milestone 3 Task 1 & Task 2 Requirement).
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 1. Total counts
            cursor.execute("SELECT COUNT(*) FROM meetings")
            meeting_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM summaries")
            summary_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM decisions")
            decision_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM action_items")
            action_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM participants")
            participant_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM embeddings")
            embedding_count = cursor.fetchone()[0]

            # 2. Check for orphaned records (records without valid parent meeting)
            cursor.execute("""
                SELECT COUNT(*) FROM summaries WHERE meeting_id NOT IN (SELECT id FROM meetings)
            """)
            orphan_summaries = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*) FROM decisions WHERE meeting_id NOT IN (SELECT id FROM meetings)
            """)
            orphan_decisions = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*) FROM action_items WHERE meeting_id NOT IN (SELECT id FROM meetings)
            """)
            orphan_actions = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*) FROM participants WHERE meeting_id NOT IN (SELECT id FROM meetings)
            """)
            orphan_participants = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*) FROM embeddings WHERE meeting_id NOT IN (SELECT id FROM meetings)
            """)
            orphan_embeddings = cursor.fetchone()[0]

            # 3. Test retrieving each meeting with all linked child entities
            cursor.execute("SELECT id FROM meetings")
            all_meeting_ids = [row[0] for row in cursor.fetchall()]

            retrieval_success_count = 0
            for m_id in all_meeting_ids:
                meeting_data = self.get_meeting(m_id)
                if meeting_data is not None and "summary" in meeting_data and "decisions" in meeting_data and "action_items" in meeting_data and "participants" in meeting_data:
                    retrieval_success_count += 1

            is_healthy = (
                orphan_summaries == 0 and
                orphan_decisions == 0 and
                orphan_actions == 0 and
                orphan_participants == 0 and
                orphan_embeddings == 0 and
                retrieval_success_count == meeting_count
            )

            return {
                "is_healthy": is_healthy,
                "meeting_count": meeting_count,
                "summary_count": summary_count,
                "decision_count": decision_count,
                "action_count": action_count,
                "participant_count": participant_count,
                "embedding_count": embedding_count,
                "orphans": {
                    "summaries": orphan_summaries,
                    "decisions": orphan_decisions,
                    "actions": orphan_actions,
                    "participants": orphan_participants,
                    "embeddings": orphan_embeddings
                },
                "retrieval_verified_meetings": retrieval_success_count,
                "checked_at": datetime.now().isoformat()
            }

    def delete_meeting(self, meeting_id: str) -> bool:
        """Delete a meeting and all cascading child records."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM meetings WHERE id = ?", (meeting_id,))
            conn.commit()
            return cursor.rowcount > 0
