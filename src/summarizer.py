"""
Meeting Summarization Module (Milestone 2 - Task 2)
Production-ready meeting summarization component that extracts
executive summaries, key decisions, and action items with assignees and deadlines.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from src.llm.service import LLMService
from src.llm.exceptions import LLMServiceError, InputValidationError, OutputValidationError
from src.llm.validators import InputValidator

logger = logging.getLogger(__name__)


@dataclass
class ActionItem:
    """Action item data representation."""
    action: str
    owner: Optional[str] = None
    deadline: Optional[str] = None
    priority: Optional[str] = None

    def formatted_string(self) -> str:
        """Format action item as 'Action – Owner Deadline'."""
        details = []
        if self.owner:
            details.append(self.owner)
        if self.deadline:
            details.append(self.deadline)
        if details:
            return f"{self.action} – {' '.join(details)}"
        return self.action


@dataclass
class MeetingSummaryResult:
    """Production-ready meeting summary result."""
    summary: str
    key_decisions: List[str]
    action_items: List[Dict[str, Optional[str]]]
    key_points: Optional[List[str]] = None
    participants: Optional[List[str]] = None
    deadlines: Optional[List[str]] = None
    priorities: Optional[List[Dict[str, Optional[str]]]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert summary result to dictionary."""
        return asdict(self)


class MeetingSummarizer:
    """
    Production-ready Meeting Summarizer component.
    Processes meeting transcripts into structured summaries, key decisions, and action items.
    """

    def __init__(self, llm_service: Optional[LLMService] = None):
        """
        Initialize the Meeting Summarizer.
        
        Args:
            llm_service: Optional pre-configured LLMService instance.
        """
        self.llm_service = llm_service or LLMService()
        logger.info("Initialized MeetingSummarizer component")

    def summarize(self, transcript: str) -> MeetingSummaryResult:
        """
        Summarize a meeting transcript.
        
        Args:
            transcript: The meeting transcript text to summarize.
            
        Returns:
            MeetingSummaryResult containing summary, key decisions, action items, and metadata.
            
        Raises:
            InputValidationError: If input validation fails.
            LLMServiceError: If processing or LLM call fails.
        """
        # Validate input
        InputValidator.validate_and_raise(transcript)
        logger.info(f"Summarizing transcript ({len(transcript)} chars)...")

        # Process through LLM service
        raw_result = self.llm_service.process_transcript(transcript)

        # Normalize action items into standard dict format
        action_items = []
        for item in raw_result.get("action_items", []):
            if isinstance(item, dict):
                action_items.append({
                    "action": item.get("action", ""),
                    "owner": item.get("owner"),
                    "deadline": item.get("deadline"),
                    "priority": item.get("priority")
                })

        # Create structured result
        result = MeetingSummaryResult(
            summary=raw_result.get("summary", ""),
            key_decisions=raw_result.get("decisions", []),
            action_items=action_items,
            key_points=raw_result.get("key_points", []),
            participants=raw_result.get("participants", []),
            deadlines=raw_result.get("deadlines", []),
            priorities=raw_result.get("priorities", [])
        )

        logger.info("Successfully generated meeting summary")
        return result

    def format_markdown(self, summary_data: Any) -> str:
        """
        Format meeting summary as clean Markdown matching Milestone 2 specification.
        
        Args:
            summary_data: MeetingSummaryResult object or dictionary.
            
        Returns:
            Markdown formatted meeting summary string.
        """
        data = summary_data.to_dict() if isinstance(summary_data, MeetingSummaryResult) else summary_data

        lines = []
        # Summary
        lines.append("### Summary:")
        lines.append(data.get("summary", "No summary available."))
        lines.append("")

        # Key Decisions
        lines.append("### Key Decisions:")
        decisions = data.get("key_decisions") or data.get("decisions") or []
        if decisions:
            for decision in decisions:
                lines.append(f"- {decision}")
        else:
            lines.append("No explicit decisions recorded.")
        lines.append("")

        # Action Items
        lines.append("### Action Items:")
        action_items = data.get("action_items", [])
        if action_items:
            for item in action_items:
                if isinstance(item, dict):
                    action_obj = ActionItem(
                        action=item.get("action", ""),
                        owner=item.get("owner"),
                        deadline=item.get("deadline"),
                        priority=item.get("priority")
                    )
                    lines.append(f"- {action_obj.formatted_string()}")
                elif isinstance(item, str):
                    lines.append(f"- {item}")
        else:
            lines.append("No action items identified.")

        return "\n".join(lines)

    def format_plain_text(self, summary_data: Any) -> str:
        """
        Format meeting summary as plain text format matching task specification.
        
        Args:
            summary_data: MeetingSummaryResult object or dictionary.
            
        Returns:
            Plain text formatted string.
        """
        data = summary_data.to_dict() if isinstance(summary_data, MeetingSummaryResult) else summary_data

        lines = []
        # Summary
        lines.append("Summary:")
        lines.append(data.get("summary", "No summary available."))
        lines.append("")

        # Key Decisions
        lines.append("Key Decisions:")
        decisions = data.get("key_decisions") or data.get("decisions") or []
        if decisions:
            for decision in decisions:
                lines.append(f"- {decision}")
        else:
            lines.append("- None")
        lines.append("")

        # Action Items
        lines.append("Action Items:")
        action_items = data.get("action_items", [])
        if action_items:
            for item in action_items:
                if isinstance(item, dict):
                    action_obj = ActionItem(
                        action=item.get("action", ""),
                        owner=item.get("owner"),
                        deadline=item.get("deadline"),
                        priority=item.get("priority")
                    )
                    lines.append(f"- {action_obj.formatted_string()}")
                elif isinstance(item, str):
                    lines.append(f"- {item}")
        else:
            lines.append("- None")

        return "\n".join(lines)

    def export_summary(self, summary_data: Any, export_format: str = "markdown") -> str:
        """
        Export summary to the specified format.
        
        Args:
            summary_data: MeetingSummaryResult or dictionary.
            export_format: One of 'markdown', 'text', 'json'.
            
        Returns:
            Formatted string.
        """
        export_format = export_format.lower()
        if export_format in ("md", "markdown"):
            return self.format_markdown(summary_data)
        elif export_format in ("txt", "text"):
            return self.format_plain_text(summary_data)
        elif export_format == "json":
            data = summary_data.to_dict() if isinstance(summary_data, MeetingSummaryResult) else summary_data
            return json.dumps(data, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {export_format}. Use 'markdown', 'text', or 'json'.")
