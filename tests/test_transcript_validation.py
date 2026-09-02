"""
Test Suite for Transcript Validation (Task 3)
Tests transcript validation logic and storage.
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.validator import TranscriptValidator


def test_valid_transcript():
    """Test validation of a valid transcript."""
    transcript_data = {
        "text": "Hello, this is a test transcript with meaningful content.",
        "language": "en",
        "duration": 10.5,
        "model": "whisper-base"
    }
    
    is_valid, error_msg = TranscriptValidator.validate_transcript(transcript_data)
    
    assert is_valid == True, f"Expected valid transcript, got: {error_msg}"
    print("✅ test_valid_transcript passed")


def test_empty_transcript():
    """Test validation of an empty transcript."""
    transcript_data = {
        "text": "",
        "language": "en",
        "duration": 0,
        "model": "whisper-base"
    }
    
    is_valid, error_msg = TranscriptValidator.validate_transcript(transcript_data)
    
    assert is_valid == False, "Expected invalid transcript for empty text"
    assert "No speech was detected" in error_msg, f"Expected 'No speech detected' message, got: {error_msg}"
    print("✅ test_empty_transcript passed")


def test_none_transcript():
    """Test validation of None transcript."""
    is_valid, error_msg = TranscriptValidator.validate_transcript(None)
    
    assert is_valid == False, "Expected invalid transcript for None"
    assert "No speech was detected" in error_msg, f"Expected 'No speech detected' message, got: {error_msg}"
    print("✅ test_none_transcript passed")


def test_whitespace_only_transcript():
    """Test validation of whitespace-only transcript."""
    transcript_data = {
        "text": "   \n\t   ",
        "language": "en",
        "duration": 5.0,
        "model": "whisper-base"
    }
    
    is_valid, error_msg = TranscriptValidator.validate_transcript(transcript_data)
    
    assert is_valid == False, "Expected invalid transcript for whitespace only"
    assert "No speech was detected" in error_msg, f"Expected 'No speech detected' message, got: {error_msg}"
    print("✅ test_whitespace_only_transcript passed")


def test_short_transcript():
    """Test validation of too-short transcript."""
    transcript_data = {
        "text": "Hi",
        "language": "en",
        "duration": 1.0,
        "model": "whisper-base"
    }
    
    is_valid, error_msg = TranscriptValidator.validate_transcript(transcript_data)
    
    assert is_valid == False, "Expected invalid transcript for short text"
    assert "No speech was detected" in error_msg, f"Expected 'No speech detected' message, got: {error_msg}"
    print("✅ test_short_transcript passed")


def test_missing_text_field():
    """Test validation of transcript missing text field."""
    transcript_data = {
        "language": "en",
        "duration": 10.0,
        "model": "whisper-base"
    }
    
    is_valid, error_msg = TranscriptValidator.validate_transcript(transcript_data)
    
    assert is_valid == False, "Expected invalid transcript for missing text field"
    assert "No speech was detected" in error_msg, f"Expected 'No speech detected' message, got: {error_msg}"
    print("✅ test_missing_text_field passed")


def test_meaningful_text_detection():
    """Test detection of meaningful vs non-meaningful text."""
    # Test meaningful text
    meaningful_data = {
        "text": "This is a meaningful sentence with several words.",
        "language": "en",
        "duration": 5.0,
        "model": "whisper-base"
    }
    
    is_valid, _ = TranscriptValidator.validate_transcript(meaningful_data)
    assert is_valid == True, "Expected valid transcript for meaningful text"
    
    # Test non-meaningful text (repeated characters)
    non_meaningful_data = {
        "text": "aaaa bbbbb ccccc",
        "language": "en",
        "duration": 5.0,
        "model": "whisper-base"
    }
    
    is_valid, _ = TranscriptValidator.validate_transcript(non_meaningful_data)
    assert is_valid == False, "Expected invalid transcript for non-meaningful text"
    
    print("✅ test_meaningful_text_detection passed")


def test_quality_metrics():
    """Test quality metrics calculation."""
    transcript_data = {
        "text": "This is a test transcript with several words.",
        "language": "en",
        "duration": 10.5,
        "model": "whisper-base"
    }
    
    metrics = TranscriptValidator.get_transcript_quality(transcript_data)
    
    assert metrics["word_count"] == 8, f"Expected 8 words, got {metrics['word_count']}"
    assert metrics["character_count"] == 45, f"Expected 45 characters, got {metrics['character_count']}"
    assert metrics["language"] == "en", f"Expected 'en', got {metrics['language']}"
    assert metrics["duration"] == 10.5, f"Expected 10.5 duration, got {metrics['duration']}"
    
    print("✅ test_quality_metrics passed")


def run_all_tests():
    """Run all transcript validation tests."""
    print("Running Transcript Validation Tests...")
    print("-" * 50)
    
    test_valid_transcript()
    test_empty_transcript()
    test_none_transcript()
    test_whitespace_only_transcript()
    test_short_transcript()
    test_missing_text_field()
    test_meaningful_text_detection()
    test_quality_metrics()
    
    print("-" * 50)
    print("✅ All transcript validation tests passed!")


if __name__ == "__main__":
    run_all_tests()
