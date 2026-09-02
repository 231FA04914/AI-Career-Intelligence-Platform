"""
Transcript Manager Module
Handles saving and loading of transcripts.
"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict


class TranscriptManager:
    """Manages transcript storage and retrieval."""
    
    def __init__(self, storage_dir="data/transcripts"):
        """
        Initialize TranscriptManager.
        
        Args:
            storage_dir: Directory to store transcripts
        """
        # Use absolute path for storage directory
        if not Path(storage_dir).is_absolute():
            self.storage_dir = Path(__file__).parent.parent / storage_dir
        else:
            self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def save_transcript(
        self,
        transcript_data: dict,
        original_filename: str,
        metadata: Optional[dict] = None
    ) -> str:
        """
        Save transcript to file with unique identifier.
        
        Args:
            transcript_data: Dictionary containing transcript text and metadata
            original_filename: Name of original audio/video file
            metadata: Additional metadata to save
            
        Returns:
            Path to saved transcript file
        """
        # Generate unique identifier
        transcript_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = Path(original_filename).stem
        transcript_filename = f"{safe_filename}_{timestamp}_{transcript_id[:8]}.json"
        transcript_path = self.storage_dir / transcript_filename
        
        # Prepare comprehensive metadata
        comprehensive_metadata = {
            "transcript_id": transcript_id,
            "original_filename": original_filename,
            "transcript_filename": transcript_filename,
            "timestamp": timestamp,
            "datetime": datetime.now().isoformat(),
            "language": transcript_data.get("language", "unknown"),
            "duration": transcript_data.get("duration", 0),
            "model": transcript_data.get("model", "unknown"),
            "word_count": len(transcript_data.get("text", "").split()),
            "character_count": len(transcript_data.get("text", "")),
            "custom_metadata": metadata or {}
        }
        
        # Prepare data to save
        save_data = {
            "transcript": transcript_data,
            "metadata": comprehensive_metadata
        }
        
        # Save to JSON file
        with open(transcript_path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)
        
        return str(transcript_path)
    
    def load_transcript(self, transcript_path: str) -> dict:
        """
        Load transcript from file.
        
        Args:
            transcript_path: Path to transcript file
            
        Returns:
            Dictionary containing transcript data
        """
        path = Path(transcript_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Transcript file not found: {transcript_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def list_transcripts(self) -> list:
        """
        List all saved transcripts.
        
        Returns:
            List of transcript file paths
        """
        return list(self.storage_dir.glob("*.json"))
    
    def delete_transcript(self, transcript_path: str) -> bool:
        """
        Delete a transcript file.
        
        Args:
            transcript_path: Path to transcript file
            
        Returns:
            True if deleted successfully
        """
        path = Path(transcript_path)
        
        if path.exists():
            path.unlink()
            return True
        
        return False
    
    def get_transcript_text(self, transcript_path: str) -> str:
        """
        Get just the transcript text from a saved transcript.
        
        Args:
            transcript_path: Path to transcript file
            
        Returns:
            Transcript text string
        """
        data = self.load_transcript(transcript_path)
        return data["transcript"]["text"]
