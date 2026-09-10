"""
Transcriber Module
Handles speech-to-text transcription using OpenAI Whisper.
"""

import os
import ssl
from pathlib import Path

# Disable SSL verification for model download
os.environ['HF_HUB_DISABLE_SSL_VERIFY'] = '1'
ssl._create_default_https_context = ssl._create_unverified_context

import whisper


class Transcriber:
    """Transcribes audio files using OpenAI Whisper speech-to-text."""
    
    def __init__(self, model_size="base", use_faster=False, **kwargs):
        """
        Initialize Transcriber with Whisper model.
        
        Args:
            model_size: Model size (tiny, base, small, medium, large)
            use_faster: Flag for faster whisper compatibility
        """
        self.model_size = model_size
        self.use_faster = use_faster
        self.model = None
        self.model_loaded = False
        try:
            self._load_model()
        except Exception:
            # Fallback to lazy loading if initial load encounters an environment issue
            pass
    
    def _load_model(self):
        """Load the Whisper model (lazy loading)."""
        if not self.model_loaded:
            try:
                self.model = whisper.load_model(self.model_size)
                self.model_loaded = True
            except Exception as e:
                raise RuntimeError(f"Failed to load Whisper model: {str(e)}")
    
    def transcribe(self, audio_file: str, language: str = "en") -> dict:
        """
        Transcribe audio file to text.
        
        Args:
            audio_file: Path to audio file
            language: Language code (default: English)
            
        Returns:
            Dictionary containing transcript and metadata
        """
        if not Path(audio_file).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file}")
        
        # Load model on first transcription attempt
        self._load_model()
        
        result = self.model.transcribe(
            audio_file,
            language=language,
            fp16=False
        )
        
        return {
            "text": result["text"],
            "language": result.get("language", language),
            "segments": result.get("segments", []),
            "duration": result.get("duration", 0),
            "model": f"whisper-{self.model_size}"
        }
