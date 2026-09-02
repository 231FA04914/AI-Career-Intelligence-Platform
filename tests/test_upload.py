"""
Test Upload Module
Tests for file upload and validation functionality.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.validator import FileValidator


class TestFileValidator:
    """Test cases for FileValidator class."""
    
    def test_validator_initialization(self):
        """Test that validator initializes correctly."""
        validator = FileValidator()
        assert validator.upload_dir.exists()
    
    def test_supported_formats(self):
        """Test that supported formats are defined."""
        validator = FileValidator()
        assert len(validator.AUDIO_FORMATS) > 0
        assert len(validator.VIDEO_FORMATS) > 0
    
    def test_get_supported_formats(self):
        """Test getting supported formats string."""
        validator = FileValidator()
        formats = validator.get_supported_formats()
        assert isinstance(formats, str)
        assert len(formats) > 0
    
    def test_is_audio_file(self):
        """Test audio file detection."""
        validator = FileValidator()
        assert validator.is_audio_file("test.mp3")
        assert validator.is_audio_file("test.wav")
        assert not validator.is_audio_file("test.mp4")
    
    def test_is_video_file(self):
        """Test video file detection."""
        validator = FileValidator()
        assert validator.is_video_file("test.mp4")
        assert validator.is_video_file("test.avi")
        assert not validator.is_video_file("test.mp3")
    
    def test_validate_nonexistent_file(self):
        """Test validation of non-existent file."""
        validator = FileValidator()
        is_valid, error = validator.validate_file("nonexistent.mp3")
        assert is_valid is False
        assert "does not exist" in error.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
