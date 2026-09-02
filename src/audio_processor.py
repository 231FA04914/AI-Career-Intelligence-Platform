"""
Audio Processor Module
Handles audio/video processing and conversion using FFmpeg.
"""

import os
import subprocess
import tempfile
from pathlib import Path


class AudioProcessor:
    """Processes audio and video files for transcription."""
    
    def __init__(self, output_dir="data/audio", use_temp=False):
        """
        Initialize AudioProcessor.
        
        Args:
            output_dir: Directory to save processed audio files
            use_temp: Use temporary directory for processed files
        """
        # Use absolute path for output directory
        if not Path(output_dir).is_absolute():
            self.output_dir = Path(__file__).parent.parent / output_dir
        else:
            self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.use_temp = use_temp
        self.temp_files = []
    
    def extract_audio(self, input_file: str, output_filename: str = None) -> str:
        """
        Extract audio from video file or process audio file.
        
        Args:
            input_file: Path to input audio/video file
            output_filename: Optional custom output filename
            
        Returns:
            Path to processed audio file (WAV format)
        """
        input_path = Path(input_file)
        
        # Debug: Check if input file exists
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path.absolute()}")
        
        # Determine output path
        if self.use_temp:
            # Use temporary directory
            temp_dir = tempfile.mkdtemp()
            output_path = Path(temp_dir) / f"{input_path.stem}.wav"
            self.temp_files.append(str(output_path))
        else:
            # Use regular output directory
            if output_filename:
                output_path = self.output_dir / output_filename
            else:
                output_path = self.output_dir / f"{input_path.stem}.wav"
        
        # FFmpeg command to extract/convert audio to WAV
        # Use proper quoting for paths with spaces
        input_path_str = str(input_path.absolute())
        output_path_str = str(output_path.absolute())
        
        cmd = [
            "ffmpeg",
            "-i", input_path_str,
            "-vn",  # No video
            "-acodec", "pcm_s16le",  # 16-bit PCM
            "-ar", "16000",  # 16kHz sample rate (Whisper default)
            "-ac", "1",  # Mono
            "-y",  # Overwrite output
            output_path_str
        ]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            if result.stderr:
                print(f"FFmpeg stderr: {result.stderr}")
            return str(output_path.absolute())
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"FFmpeg processing failed: {e.stderr}")
    
    def cleanup_temp_files(self):
        """Clean up temporary files created during processing."""
        for temp_file in self.temp_files:
            try:
                if Path(temp_file).exists():
                    Path(temp_file).unlink()
            except Exception:
                pass
        self.temp_files.clear()
    
    def get_audio_duration(self, audio_file: str) -> float:
        """
        Get duration of audio file in seconds.
        
        Args:
            audio_file: Path to audio file
            
        Returns:
            Duration in seconds
        """
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_file)
        ]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            return float(result.stdout.strip())
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to get audio duration: {e.stderr}")
