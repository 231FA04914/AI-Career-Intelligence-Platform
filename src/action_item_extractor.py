"""
Action Item Extraction Engine (Milestone 2 - Task 3)
Pipeline for extracting, normalizing, and managing actionable tasks
with assigned participants, deadlines, priorities, and statuses.
"""

import csv
import io
import json
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict, field

from src.llm.service import LLMService
from src.llm.prompts import PromptTemplates
from src.llm.validators import InputValidator, OutputValidator
from src.llm.exceptions import LLMServiceError, InputValidationError, OutputValidationError

logger = logging.getLogger(__name__)


@dataclass
class ExtractedActionItem:
    """Standardized Action Item data representation."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    action: str = ""
    owner: Optional[str] = None
    deadline: Optional[str] = None
    priority: str = "Medium"
    status: str = "Pending"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @property
    def assignee_display(self) -> str:
        """Display name for assignee."""
        return self.owner if self.owner else "Unassigned"

    @property
    def deadline_display(self) -> str:
        """Display deadline or default."""
        return self.deadline if self.deadline else "No deadline"


class ActionItemExtractor:
    """
    Action Item Extraction Engine.
    Processes transcripts through an AI pipeline to identify, normalize,
    and categorize actionable tasks with assignee, deadline, priority, and status.
    """

    PRIORITY_WEIGHTS = {"High": 3, "Medium": 2, "Low": 1}
    VALID_STATUSES = ["Pending", "In Progress", "Completed", "Blocked"]
    VALID_PRIORITIES = ["High", "Medium", "Low"]

    def __init__(self, llm_service: Optional[LLMService] = None):
        """
        Initialize ActionItemExtractor.
        
        Args:
            llm_service: Optional LLMService instance.
        """
        self.llm_service = llm_service or LLMService()
        logger.info("Initialized ActionItemExtractor Engine")

    def extract_action_items(self, transcript: str) -> List[ExtractedActionItem]:
        """
        Extract all action items from meeting transcript.
        
        Args:
            transcript: Meeting or interview transcript text.
            
        Returns:
            List of ExtractedActionItem objects.
            
        Raises:
            InputValidationError: If input is invalid.
            LLMServiceError: If processing fails.
        """
        InputValidator.validate_and_raise(transcript)
        logger.info(f"Extracting action items from transcript ({len(transcript)} chars)...")

        # Format prompt specifically for action items
        prompt = PromptTemplates.get_action_item_extraction_prompt().format(transcript=transcript)
        raw_response = self.llm_service._call_llm_with_retry(prompt)

        # Parse and extract
        cleaned_json = OutputValidator.clean_json_string(raw_response)
        try:
            parsed_data = json.loads(cleaned_json)
        except json.JSONDecodeError:
            # Fallback to general intelligence pipeline if single extraction json was partial
            logger.warning("Dedicated extraction returned non-standard JSON, falling back to general intelligence parser")
            general_res = self.llm_service.process_transcript(transcript)
            parsed_data = {"action_items": general_res.get("action_items", [])}

        items_list = parsed_data.get("action_items", [])
        extracted_items: List[ExtractedActionItem] = []

        for item in items_list:
            if isinstance(item, dict):
                action_text = (item.get("action") or "").strip()
                if not action_text:
                    continue

                owner = item.get("owner")
                if owner and isinstance(owner, str):
                    owner = owner.strip()
                    if owner.lower() in ("null", "none", "n/a", "unassigned"):
                        owner = None

                deadline = item.get("deadline")
                if deadline and isinstance(deadline, str):
                    deadline = deadline.strip()
                    if deadline.lower() in ("null", "none", "n/a"):
                        deadline = None

                priority = item.get("priority")
                if priority and isinstance(priority, str):
                    priority = priority.strip().capitalize()
                    if priority not in self.VALID_PRIORITIES:
                        priority = "Medium"
                else:
                    priority = "Medium"

                status = item.get("status")
                if status and isinstance(status, str):
                    status = status.strip().title()
                    if status == "Open":
                        status = "Pending"
                    elif status not in self.VALID_STATUSES:
                        status = "Pending"
                else:
                    status = "Pending"

                extracted_items.append(ExtractedActionItem(
                    action=action_text,
                    owner=owner,
                    deadline=deadline,
                    priority=priority,
                    status=status
                ))

        logger.info(f"Extracted {len(extracted_items)} action items")
        return extracted_items

    def filter_items(
        self,
        items: List[ExtractedActionItem],
        assignee: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> List[ExtractedActionItem]:
        """
        Filter action items based on criteria.
        
        Args:
            items: List of ExtractedActionItem objects.
            assignee: Filter by specific participant/owner.
            priority: Filter by priority (High, Medium, Low).
            status: Filter by status (Pending, In Progress, Completed, Blocked).
            search_query: Free text search within task description.
            
        Returns:
            Filtered list of action items.
        """
        filtered = items
        if assignee and assignee != "All":
            if assignee == "Unassigned":
                filtered = [i for i in filtered if not i.owner]
            else:
                filtered = [i for i in filtered if i.owner and i.owner.lower() == assignee.lower()]

        if priority and priority != "All":
            filtered = [i for i in filtered if i.priority.lower() == priority.lower()]

        if status and status != "All":
            filtered = [i for i in filtered if i.status.lower() == status.lower()]

        if search_query and search_query.strip():
            q = search_query.strip().lower()
            filtered = [i for i in filtered if q in i.action.lower() or (i.owner and q in i.owner.lower())]

        return filtered

    def sort_items(
        self,
        items: List[ExtractedActionItem],
        sort_by: str = "priority",
        descending: bool = False
    ) -> List[ExtractedActionItem]:
        """
        Sort action items.
        
        Args:
            items: List of ExtractedActionItem objects.
            sort_by: Field to sort by ('priority', 'deadline', 'assignee', 'status', 'action').
            descending: Sort order.
            
        Returns:
            Sorted list of action items.
        """
        if sort_by == "priority":
            return sorted(
                items,
                key=lambda x: self.PRIORITY_WEIGHTS.get(x.priority, 0),
                reverse=not descending  # High first by default
            )
        elif sort_by == "assignee":
            return sorted(items, key=lambda x: x.assignee_display.lower(), reverse=descending)
        elif sort_by == "status":
            return sorted(items, key=lambda x: x.status.lower(), reverse=descending)
        elif sort_by == "deadline":
            return sorted(items, key=lambda x: (x.deadline is None, str(x.deadline)), reverse=descending)
        elif sort_by == "action":
            return sorted(items, key=lambda x: x.action.lower(), reverse=descending)
        return items

    def get_metrics(self, items: List[ExtractedActionItem]) -> Dict[str, Any]:
        """
        Calculate summary metrics for a list of action items.
        
        Args:
            items: List of ExtractedActionItem objects.
            
        Returns:
            Dictionary with metrics.
        """
        total = len(items)
        high_priority = sum(1 for i in items if i.priority == "High")
        pending = sum(1 for i in items if i.status == "Pending")
        in_progress = sum(1 for i in items if i.status == "In Progress")
        completed = sum(1 for i in items if i.status == "Completed")
        assigned = sum(1 for i in items if i.owner)
        unassigned = total - assigned

        return {
            "total": total,
            "high_priority": high_priority,
            "pending": pending,
            "in_progress": in_progress,
            "completed": completed,
            "assigned": assigned,
            "unassigned": unassigned
        }

    def to_markdown_table(self, items: List[ExtractedActionItem]) -> str:
        """
        Format action items as a GitHub-flavored Markdown table.
        
        Args:
            items: List of ExtractedActionItem objects.
            
        Returns:
            Markdown table string.
        """
        if not items:
            return "No action items extracted."

        lines = [
            "| # | Task / Action | Assigned Participant | Deadline | Priority | Status |",
            "|---|---------------|----------------------|----------|----------|--------|"
        ]

        for idx, item in enumerate(items, 1):
            assignee = item.owner if item.owner else "_Unassigned_"
            deadline = item.deadline if item.deadline else "_None_"
            lines.append(f"| {idx} | {item.action} | {assignee} | {deadline} | {item.priority} | {item.status} |")

        return "\n".join(lines)

    def to_csv(self, items: List[ExtractedActionItem]) -> str:
        """
        Export action items to CSV string.
        
        Args:
            items: List of ExtractedActionItem objects.
            
        Returns:
            CSV formatted string.
        """
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Task", "Assigned Participant", "Deadline", "Priority", "Status", "Created At"])

        for item in items:
            writer.writerow([
                item.id,
                item.action,
                item.owner or "",
                item.deadline or "",
                item.priority,
                item.status,
                item.created_at
            ])

        return output.getvalue()

    def to_json(self, items: List[ExtractedActionItem]) -> str:
        """
        Export action items to JSON string.
        
        Args:
            items: List of ExtractedActionItem objects.
            
        Returns:
            JSON formatted string.
        """
        data = [item.to_dict() for item in items]
        return json.dumps(data, indent=2)
