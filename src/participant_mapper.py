"""
Participant & Responsibility Mapping Module (Milestone 2 - Task 4)
Handles participant identification, name normalization, deduplication,
safe unknown participant handling, and linking responsibilities to meetings.
"""

import re
import json
import logging
from typing import List, Dict, Optional, Any, Set
from dataclasses import dataclass, field, asdict

from src.llm.service import LLMService
from src.llm.validators import InputValidator, OutputValidator
from src.action_item_extractor import ExtractedActionItem

logger = logging.getLogger(__name__)


@dataclass
class Participant:
    """Participant and their mapped responsibilities."""
    name: str
    canonical_name: str
    role: Optional[str] = None
    responsibilities: List[Dict[str, Any]] = field(default_factory=list)
    meeting_id: Optional[str] = None
    is_known: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert participant to dictionary."""
        return asdict(self)

    @property
    def total_tasks(self) -> int:
        """Count of assigned tasks."""
        return len(self.responsibilities)


class ParticipantMapper:
    """
    Participant & Responsibility Mapping Engine (Task 4).
    Verifies:
    - Participant names are correctly identified.
    - Names are mapped consistently.
    - Multiple participants are handled.
    - Unknown participants are handled safely.
    - Duplicate participant records are avoided.
    - Responsibilities are linked to the correct meeting.
    """

    TITLE_PREFIXES = ["mr.", "mr", "ms.", "ms", "mrs.", "mrs", "dr.", "dr", "prof.", "prof"]

    def __init__(self, llm_service: Optional[LLMService] = None):
        """
        Initialize ParticipantMapper.
        
        Args:
            llm_service: Optional LLMService instance.
        """
        self.llm_service = llm_service or LLMService()
        logger.info("Initialized ParticipantMapper Engine")

    def normalize_name(self, raw_name: Optional[str]) -> str:
        """
        Normalize participant names consistently.
        Strips common titles, excess whitespace, and standardizes casing.
        
        Args:
            raw_name: Raw name string from text/LLM.
            
        Returns:
            Normalized canonical name.
        """
        if not raw_name or not isinstance(raw_name, str):
            return "Unassigned"

        clean = raw_name.strip()
        if not clean or clean.lower() in ("null", "none", "n/a", "unknown", "unassigned", "nobody"):
            return "Unassigned"

        # Check for title prefixes
        parts = clean.split()
        if len(parts) > 1 and parts[0].lower().rstrip('.') in ["mr", "ms", "mrs", "dr", "prof"]:
            parts = parts[1:]

        # Capitalize each name component consistently
        canonical = " ".join([p.capitalize() for p in parts])
        return canonical if canonical else "Unassigned"

    def deduplicate_participants(self, participants: List[Participant]) -> List[Participant]:
        """
        Merge duplicate participant records and aggregate their responsibilities.
        
        Args:
            participants: List of Participant objects.
            
        Returns:
            Deduplicated list of Participant objects.
        """
        merged_map: Dict[str, Participant] = {}

        for p in participants:
            key = p.canonical_name.lower()
            if key in merged_map:
                existing = merged_map[key]
                # Merge roles if available
                if not existing.role and p.role:
                    existing.role = p.role
                # Merge meeting ID if not set
                if not existing.meeting_id and p.meeting_id:
                    existing.meeting_id = p.meeting_id
                # Merge responsibilities without duplicates
                existing_task_names = {r.get("action", "").lower() for r in existing.responsibilities}
                for resp in p.responsibilities:
                    if resp.get("action", "").lower() not in existing_task_names:
                        existing.responsibilities.append(resp)
                        existing_task_names.add(resp.get("action", "").lower())
            else:
                merged_map[key] = p

        return list(merged_map.values())

    def map_responsibilities(
        self,
        transcript: str,
        action_items: Optional[List[Any]] = None,
        meeting_id: str = "meeting_1",
        participants: Optional[List[str]] = None
    ) -> List[Participant]:
        """
        Map participants and their responsibilities linked to a specific meeting.
        
        Args:
            transcript: Meeting transcript text.
            action_items: Optional pre-extracted action items.
            meeting_id: Identifier of the meeting session.
            participants: Optional pre-extracted participant names to avoid duplicate LLM calls.
            
        Returns:
            List of unique Participant objects with linked responsibilities.
        """
        InputValidator.validate_and_raise(transcript)

        # Step 1: Identify participants from provided list or extract if none given
        raw_participants = list(participants) if participants else []
        if action_items:
            owner_names = [
                i.get("owner") if isinstance(i, dict) else getattr(i, "owner", None)
                for i in action_items
                if (i.get("owner") if isinstance(i, dict) else getattr(i, "owner", None))
            ]
            for o in owner_names:
                if o and o not in raw_participants:
                    raw_participants.append(o)
        elif not raw_participants:
            # Fallback to LLM intelligence only if no pre-extracted data was provided
            intel = self.llm_service.process_transcript(transcript)
            raw_participants = intel.get("participants", [])
            if action_items is None:
                action_items = intel.get("action_items", [])

        # If action items not provided, use empty list
        if action_items is None:
            raw_action_items = []
        else:
            raw_action_items = [
                i.to_dict() if isinstance(i, ExtractedActionItem) else i
                for i in action_items
            ]

        # Step 2: Initialize participant map
        participants_dict: Dict[str, Participant] = {}

        # Register explicitly identified participants
        for p_name in raw_participants:
            canonical = self.normalize_name(p_name)
            if canonical not in participants_dict:
                participants_dict[canonical] = Participant(
                    name=p_name,
                    canonical_name=canonical,
                    meeting_id=meeting_id,
                    is_known=canonical != "Unassigned"
                )

        # Step 3: Link action items to participants
        for item in raw_action_items:
            owner_raw = item.get("owner")
            canonical_owner = self.normalize_name(owner_raw)

            if canonical_owner not in participants_dict:
                participants_dict[canonical_owner] = Participant(
                    name=owner_raw or "Unassigned",
                    canonical_name=canonical_owner,
                    meeting_id=meeting_id,
                    is_known=canonical_owner != "Unassigned"
                )

            # Link task to participant's responsibilities
            participants_dict[canonical_owner].responsibilities.append({
                "action": item.get("action", ""),
                "deadline": item.get("deadline"),
                "priority": item.get("priority", "Medium"),
                "status": item.get("status", "Pending"),
                "meeting_id": meeting_id
            })

        # Step 4: Deduplicate and sort
        deduped = self.deduplicate_participants(list(participants_dict.values()))
        # Sort so known participants come first alphabetically, Unassigned last
        return sorted(deduped, key=lambda x: (not x.is_known, x.canonical_name.lower()))

    def to_matrix_markdown(self, participants: List[Participant]) -> str:
        """
        Generate a Markdown responsibility matrix table.
        
        Args:
            participants: List of Participant objects.
            
        Returns:
            Markdown table string.
        """
        if not participants:
            return "No participants or responsibilities mapped."

        lines = [
            "| Participant | Status | Total Responsibilities | Assigned Tasks & Deadlines | Meeting ID |",
            "|-------------|--------|------------------------|-----------------------------|------------|"
        ]

        for p in participants:
            status_tag = "👤 Identified" if p.is_known else "⚠️ Unassigned"
            tasks_list = []
            for r in p.responsibilities:
                d_str = f" ({r['deadline']})" if r.get('deadline') else ""
                p_str = f" [{r['priority']}]" if r.get('priority') else ""
                tasks_list.append(f"{r['action']}{d_str}{p_str}")

            tasks_display = "<br>".join(tasks_list) if tasks_list else "_No direct action items assigned_"
            lines.append(f"| **{p.canonical_name}** | {status_tag} | {p.total_tasks} | {tasks_display} | {p.meeting_id or 'N/A'} |")

        return "\n".join(lines)

    def to_dict_list(self, participants: List[Participant]) -> List[Dict[str, Any]]:
        """Convert list of participants to JSON serializable list."""
        return [p.to_dict() for p in participants]
