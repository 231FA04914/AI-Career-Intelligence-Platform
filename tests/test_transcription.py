"""
Test Transcription Module
Tests for Whisper transcription functionality.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.transcriber import Transcriber


class TestTranscriber:
    """Test cases for Transcriber class."""
    
    def test_transcriber_initialization(self):
        """Test that transcriber initializes correctly."""
        transcriber = Transcriber(model_size="tiny", use_faster=True)
        assert transcriber.model is not None
        assert transcriber.model_size == "tiny"
    
    def test_transcriber_model_sizes(self):
        """Test different model sizes."""
        sizes = ["tiny", "base", "small"]
        for size in sizes:
            transcriber = Transcriber(model_size=size, use_faster=True)
            assert transcriber.model_size == size
    
    def test_transcribe_nonexistent_file(self):
        """Test transcription with non-existent file."""
        transcriber = Transcriber(model_size="tiny", use_faster=True)
        with pytest.raises(FileNotFoundError):
            transcriber.transcribe("nonexistent_file.wav")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
