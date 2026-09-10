"""
Summary Manager Module (Milestone 2 - Task 2)
Handles saving, loading, and listing of meeting summaries.
"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any
from src.summarizer import MeetingSummaryResult


class SummaryManager:
    """Manages meeting summary storage and retrieval."""

    def __init__(self, storage_dir="data/summaries"):
        """
        Initialize SummaryManager.
        
        Args:
            storage_dir: Directory to store summaries
        """
        if not Path(storage_dir).is_absolute():
            self.storage_dir = Path(__file__).parent.parent / storage_dir
        else:
            self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_summary(
        self,
        summary_data: Any,
        source_name: str = "meeting_transcript",
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Save meeting summary to JSON file.
        
        Args:
            summary_data: MeetingSummaryResult object or dictionary
            source_name: Name or identifier of the source transcript
            metadata: Optional additional metadata
            
        Returns:
            Path string to saved summary file
        """
        summary_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_source = Path(source_name).stem
        summary_filename = f"summary_{safe_source}_{timestamp}_{summary_id[:8]}.json"
        summary_path = self.storage_dir / summary_filename

        data_dict = summary_data.to_dict() if isinstance(summary_data, MeetingSummaryResult) else summary_data

        save_payload = {
            "summary_id": summary_id,
            "source_name": source_name,
            "timestamp": timestamp,
            "created_at": datetime.now().isoformat(),
            "metadata": metadata or {},
            "data": data_dict
        }

        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(save_payload, f, indent=2, ensure_ascii=False)

        return str(summary_path)

    def load_summary(self, summary_path: str) -> Dict:
        """
        Load summary from file.
        
        Args:
            summary_path: Path to summary JSON file
            
        Returns:
            Summary payload dictionary
        """
        path = Path(summary_path)
        if not path.exists():
            raise FileNotFoundError(f"Summary file not found: {summary_path}")

        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def list_summaries(self) -> List[Path]:
        """
        List all saved summary files ordered newest first.
        
        Returns:
            List of Path objects
        """
        summaries = list(self.storage_dir.glob("*.json"))
        summaries.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return summaries

    def delete_summary(self, summary_path: str) -> bool:
        """
        Delete a summary file.
        
        Args:
            summary_path: Path to summary file
            
        Returns:
            True if deleted, False otherwise
        """
        path = Path(summary_path)
        if path.exists():
            path.unlink()
            return True
        return False
