"""
Test Validation Module
Tests for transcript validation functionality.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.validator import TranscriptValidator


class TestTranscriptValidator:
    """Test cases for TranscriptValidator class."""
    
    def test_validate_empty_transcript(self):
        """Test validation of empty transcript."""
        validator = TranscriptValidator()
        is_valid, error = validator.validate_transcript({})
        assert is_valid is False
        assert "empty" in error.lower()
    
    def test_validate_missing_text_field(self):
        """Test validation of transcript without text field."""
        validator = TranscriptValidator()
        is_valid, error = validator.validate_transcript({"other_field": "data"})
        assert is_valid is False
        assert "text" in error.lower()
    
    def test_validate_empty_text(self):
        """Test validation of transcript with empty text."""
        validator = TranscriptValidator()
        is_valid, error = validator.validate_transcript({"text": "   "})
        assert is_valid is False
        assert "empty" in error.lower()
    
    def test_validate_short_text(self):
        """Test validation of transcript with too short text."""
        validator = TranscriptValidator()
        is_valid, error = validator.validate_transcript({"text": "hi"})
        assert is_valid is False
        assert "short" in error.lower()
    
    def test_validate_valid_transcript(self):
        """Test validation of valid transcript."""
        validator = TranscriptValidator()
        is_valid, error = validator.validate_transcript({
            "text": "This is a valid transcript with enough text to pass validation."
        })
        assert is_valid is True
        assert error is None
    
    def test_get_word_count(self):
        """Test word count calculation."""
        validator = TranscriptValidator()
        count = validator.get_word_count("This is a test sentence.")
        assert count == 5
    
    def test_get_character_count(self):
        """Test character count calculation."""
        validator = TranscriptValidator()
        count = validator.get_character_count("Hello")
        assert count == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
