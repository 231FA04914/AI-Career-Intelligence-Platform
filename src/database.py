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
        meeting_id: Optional[str] = None
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
            
        Returns:
            Saved meeting_id string.
        """
        m_id = meeting_id or f"meet_{uuid.uuid4().hex[:10]}"

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 1. Insert Meeting
            cursor.execute("""
                INSERT OR REPLACE INTO meetings (id, title, original_filename, transcript_text, duration, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (m_id, title, original_filename, transcript_text, duration, datetime.now().isoformat()))

            # 2. Insert Summary
            s_id = f"sum_{uuid.uuid4().hex[:8]}"
            cursor.execute("""
                INSERT INTO summaries (id, meeting_id, summary_text, created_at)
                VALUES (?, ?, ?, ?)
            """, (s_id, m_id, summary_text, datetime.now().isoformat()))

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
                p_canonical = p.get("canonical_name") if isinstance(p, dict) else getattr(p, "canonical_name", p_name)
                p_role = p.get("role") if isinstance(p, dict) else getattr(p, "role", None)

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

    def delete_meeting(self, meeting_id: str) -> bool:
        """Delete a meeting and all cascading child records."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM meetings WHERE id = ?", (meeting_id,))
            conn.commit()
            return cursor.rowcount > 0
