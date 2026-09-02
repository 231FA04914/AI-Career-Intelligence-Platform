"""
Validator Module
Handles file upload validation and transcript validation.
"""

import os
from pathlib import Path
from typing import Tuple, Optional


class FileValidator:
    """Validates uploaded audio/video files."""
    
    # Supported audio formats (Task 1 & Task 2 requirements)
    AUDIO_FORMATS = {".mp3", ".wav", ".m4a"}
    
    # Supported video formats (Task 1 & Task 2 requirements)
    VIDEO_FORMATS = {".mp4", ".webm"}
    
    # Maximum file size (500 MB)
    MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB in bytes
    
    # Magic bytes for file content validation
    MAGIC_BYTES = {
        # Audio formats
        ".mp3": [b"ID3", b"\xff\xfb", b"\xff\xfa", b"\xff\xe3"],
        ".wav": [b"RIFF"],
        ".m4a": [b"ftypM4A", b"ftypmp42", b"ftypisom"],
        # Video formats (more lenient - various container formats)
        ".mp4": [b"ftypmp42", b"ftypisom", b"ftypMSNV", b"ftypM4V", b"ftyp3gp", b"ftyp3g2", b"ftypavc1", b"ftypdash"],
        ".webm": [b"\x1a\x45\xdf\xa3"]  # EBML header
    }
    
    def __init__(self, upload_dir="data/uploads"):
        """
        Initialize FileValidator.
        
        Args:
            upload_dir: Directory for uploaded files
        """
        # Use absolute path for upload directory
        if not Path(upload_dir).is_absolute():
            self.upload_dir = Path(__file__).parent.parent / upload_dir
        else:
            self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def validate_file(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate uploaded file.
        
        Args:
            file_path: Path to uploaded file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        path = Path(file_path)
        
        # Check if file exists
        if not path.exists():
            return False, "File does not exist"
        
        # Check file size
        file_size = path.stat().st_size
        if file_size == 0:
            return False, "The uploaded file is empty."
        if file_size > self.MAX_FILE_SIZE:
            return False, f"The file is too large. Maximum size is {self.MAX_FILE_SIZE / (1024*1024):.0f} MB."
        
        # Check file extension
        ext = path.suffix.lower()
        if ext not in self.AUDIO_FORMATS and ext not in self.VIDEO_FORMATS:
            return False, f"Unsupported file format. Please upload an audio or video file. Supported formats: {', '.join(sorted(self.AUDIO_FORMATS | self.VIDEO_FORMATS))}"
        
        # Validate file content using magic bytes
        content_valid, content_error = self._validate_file_content(path, ext)
        if not content_valid:
            return False, content_error
        
        # Check if file appears to be corrupted
        if self._is_file_corrupted(path, ext):
            return False, "The uploaded file appears to be corrupted."
        
        return True, None
    
    def _validate_file_content(self, file_path: Path, extension: str) -> Tuple[bool, Optional[str]]:
        """
        Validate file content using magic bytes.
        
        Args:
            file_path: Path to file
            extension: File extension
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Skip content validation for MP4 files due to container format variations
        # Extension validation is sufficient for MP4
        if extension == ".mp4":
            return True, None
        
        if extension not in self.MAGIC_BYTES:
            # If we don't have magic bytes for this format, skip content validation
            return True, None
        
        try:
            with open(file_path, 'rb') as f:
                header = f.read(12)  # Read first 12 bytes
            
            # Check if any of the magic bytes match
            magic_signatures = self.MAGIC_BYTES[extension]
            for magic in magic_signatures:
                if header.startswith(magic):
                    return True, None
            
            return False, f"File content does not match {extension} format. The file may have been renamed incorrectly."
        
        except Exception as e:
            return False, f"Error reading file content: {str(e)}"
    
    def _is_file_corrupted(self, file_path: Path, extension: str) -> bool:
        """
        Check if file appears to be corrupted.
        
        Args:
            file_path: Path to file
            extension: File extension
            
        Returns:
            True if file appears corrupted, False otherwise
        """
        try:
            # Basic corruption check: try to read the file
            with open(file_path, 'rb') as f:
                # Try to read a small portion of the file
                f.read(1024)
            return False
        except Exception:
            return True
    
    def is_audio_file(self, file_path: str) -> bool:
        """Check if file is an audio file."""
        return Path(file_path).suffix.lower() in self.AUDIO_FORMATS
    
    def is_video_file(self, file_path: str) -> bool:
        """Check if file is a video file."""
        return Path(file_path).suffix.lower() in self.VIDEO_FORMATS
    
    def get_supported_formats(self) -> str:
        """Get string listing all supported formats."""
        all_formats = sorted(self.AUDIO_FORMATS | self.VIDEO_FORMATS)
        return ", ".join(all_formats)


class TranscriptValidator:
    """Validates generated transcripts."""
    
    @staticmethod
    def validate_transcript(transcript_data: dict) -> Tuple[bool, Optional[str]]:
        """
        Validate transcript data.
        
        Args:
            transcript_data: Dictionary containing transcript data
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if transcript exists
        if not transcript_data:
            return False, "No speech was detected in this recording."
        
        # Check for text field
        if "text" not in transcript_data:
            return False, "No speech was detected in this recording."
        
        # Check if text is not empty
        text = transcript_data["text"].strip()
        if not text:
            return False, "No speech was detected in this recording."
        
        # Check if text is only whitespace
        if not text.strip():
            return False, "No speech was detected in this recording."
        
        # Check for minimum length (at least 10 characters)
        if len(text) < 10:
            return False, "No speech was detected in this recording."
        
        # Check for meaningful text (not just repeated characters or noise)
        if not TranscriptValidator._is_meaningful_text(text):
            return False, "No speech was detected in this recording."
        
        return True, None
    
    @staticmethod
    def _is_meaningful_text(text: str) -> bool:
        """
        Check if text contains meaningful content.
        
        Args:
            text: Text to check
            
        Returns:
            True if text appears meaningful
        """
        # Remove common filler words and check if there's substantial content
        filler_words = {'um', 'uh', 'ah', 'like', 'you know', 'so', 'and', 'or', 'but', 'the', 'a', 'an'}
        words = text.lower().split()
        
        # Filter out filler words
        meaningful_words = [w for w in words if w not in filler_words and len(w) > 1]
        
        # Need at least 3 meaningful words
        if len(meaningful_words) < 3:
            return False
        
        # Check for character variety (not just repeated characters)
        unique_chars = set(text.lower())
        if len(unique_chars) < 5:
            return False
        
        return True
    
    @staticmethod
    def get_word_count(transcript_text: str) -> int:
        """Get word count of transcript."""
        return len(transcript_text.split())
    
    @staticmethod
    def get_character_count(transcript_text: str) -> int:
        """Get character count of transcript."""
        return len(transcript_text)
    
    @staticmethod
    def get_transcript_quality(transcript_data: dict) -> dict:
        """
        Get quality metrics for transcript.
        
        Args:
            transcript_data: Dictionary containing transcript data
            
        Returns:
            Dictionary with quality metrics
        """
        text = transcript_data.get("text", "")
        return {
            "word_count": TranscriptValidator.get_word_count(text),
            "character_count": TranscriptValidator.get_character_count(text),
            "language": transcript_data.get("language", "unknown"),
            "duration": transcript_data.get("duration", 0),
            "model": transcript_data.get("model", "unknown")
        }
