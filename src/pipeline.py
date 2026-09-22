"""
End-to-End Meeting Intelligence Processing Pipeline (Milestone 2 - Task 6)
Orchestrates:
Upload Meeting -> AudioProcessor -> Whisper Transcriber -> Transcript
-> LLM Processing -> Summary -> Action Extraction -> Participant Mapping -> Database.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable

from src.audio_processor import AudioProcessor
from src.transcriber import Transcriber
from src.validator import FileValidator, TranscriptValidator
from src.transcript_manager import TranscriptManager
from src.llm.service import LLMService
from src.summarizer import MeetingSummarizer
from src.action_item_extractor import ActionItemExtractor
from src.participant_mapper import ParticipantMapper
from src.database import DatabaseManager
from src.embeddings import EmbeddingGenerator

logger = logging.getLogger(__name__)


class MeetingIntelligencePipeline:
    """
    End-to-End Meeting Intelligence Service Pipeline (Task 6 & Milestone 3).
    Integrates the complete flow:
    Upload/Audio -> Whisper -> Transcript -> LLM Processing -> Summary
    -> Action Extraction -> Participant Mapping -> Database Persistence -> Embedding Generation.
    """

    def __init__(
        self,
        audio_processor: Optional[AudioProcessor] = None,
        transcriber: Optional[Transcriber] = None,
        llm_service: Optional[LLMService] = None,
        db_manager: Optional[DatabaseManager] = None,
        embedding_generator: Optional[EmbeddingGenerator] = None
    ):
        """Initialize all pipeline components."""
        self.audio_processor = audio_processor or AudioProcessor(use_temp=True)
        self.transcriber = transcriber or Transcriber(model_size="base")
        self.file_validator = FileValidator()
        self.transcript_validator = TranscriptValidator()
        self.transcript_manager = TranscriptManager()
        self.llm_service = llm_service or LLMService()
        self.summarizer = MeetingSummarizer(llm_service=self.llm_service)
        self.action_extractor = ActionItemExtractor(llm_service=self.llm_service)
        self.participant_mapper = ParticipantMapper(llm_service=self.llm_service)
        self.db_manager = db_manager or DatabaseManager()
        self.embedding_generator = embedding_generator or EmbeddingGenerator(api_key=getattr(self.llm_service, "api_key", None))
        self.last_transcript_text: Optional[str] = None
        self.last_transcript_data: Optional[Dict[str, Any]] = None

        logger.info("Initialized MeetingIntelligencePipeline with all service components and EmbeddingGenerator")


    def process_audio_file(
        self,
        audio_or_video_path: str,
        meeting_title: Optional[str] = None,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> Dict[str, Any]:
        """
        Execute full end-to-end pipeline from an uploaded audio/video file.
        
        Stages:
        1. Validate Audio/Video
        2. Extract & Convert Audio (AudioProcessor)
        3. Transcribe (Whisper)
        4. Validate Transcript
        5. Summarize Meeting (MeetingSummarizer)
        6. Extract Action Items (ActionItemExtractor)
        7. Map Participants & Responsibilities (ParticipantMapper)
        8. Persist to Database (DatabaseManager)
        
        Args:
            audio_or_video_path: Path to recording file.
            meeting_title: Optional title for the meeting.
            progress_callback: Optional callback func(stage_name, percent).
            
        Returns:
            Dictionary containing complete meeting intelligence and database record ID.
        """
        def update_progress(msg: str, pct: int):
            if progress_callback:
                progress_callback(msg, pct)
            logger.info(f"Pipeline Progress [{pct}%]: {msg}")

        # Stage 1: File Validation
        update_progress("Validating input media file...", 10)
        is_valid, err_msg = self.file_validator.validate_file(audio_or_video_path)
        if not is_valid:
            raise ValueError(f"File validation failed: {err_msg}")

        # Stage 2: Audio Extraction
        update_progress("Extracting & processing audio...", 25)
        extracted_audio_path = self.audio_processor.extract_audio(audio_or_video_path)
        duration = self.audio_processor.get_audio_duration(extracted_audio_path)

        # Stage 3: Whisper Transcription
        update_progress("Transcribing audio with Whisper...", 40)
        transcript_data = self.transcriber.transcribe(extracted_audio_path)
        transcript_text = transcript_data.get("text", "")

        # Stage 4: Transcript Validation
        update_progress("Validating transcript...", 55)
        is_valid_t, err_t = self.transcript_validator.validate_transcript(transcript_data)
        if not is_valid_t:
            raise ValueError(f"Transcript validation failed: {err_t}")

        # Save transcript to transcript manager
        original_filename = Path(audio_or_video_path).name
        self.transcript_manager.save_transcript(transcript_data, original_filename)
        self.last_transcript_text = transcript_text
        self.last_transcript_data = transcript_data

        # Cleanup temporary audio files
        self.audio_processor.cleanup_temp_files()

        # Step into LLM Processing stages
        title = meeting_title or Path(original_filename).stem.replace("_", " ").title()
        return self.process_transcript_text(
            transcript_text=transcript_text,
            meeting_title=title,
            original_filename=original_filename,
            duration=duration,
            progress_callback=progress_callback,
            start_progress_pct=60
        )


    def process_transcript_text(
        self,
        transcript_text: str,
        meeting_title: str = "Meeting Transcript",
        original_filename: Optional[str] = None,
        duration: float = 0.0,
        progress_callback: Optional[Callable[[str, int], None]] = None,
        start_progress_pct: int = 10
    ) -> Dict[str, Any]:
        """
        Execute pipeline starting from transcript text.
        
        Args:
            transcript_text: Meeting transcript string.
            meeting_title: Title of the meeting.
            original_filename: Optional source filename.
            duration: Audio duration in seconds.
            progress_callback: Optional callback func(stage_name, percent).
            start_progress_pct: Base percentage for progress tracking.
            
        Returns:
            Dictionary of all processed entities and saved database record.
        """
        def update_progress(msg: str, pct: int):
            if progress_callback:
                progress_callback(msg, pct)
            logger.info(f"Pipeline Progress [{pct}%]: {msg}")

        # Stage 5: Meeting Summarization & Extraction (Comprehensive Single LLM Call)
        update_progress("Generating Meeting Intelligence (Summary, Decisions, Tasks)...", max(start_progress_pct, 65))
        try:
            summary_result = self.summarizer.summarize(transcript_text)
            summary_dict = summary_result.to_dict()
        except Exception as e:
            logger.warning(f"LLM Summarization encountered issue ({e}). Generating graceful fallback summary.")
            sentences = [s.strip() for s in transcript_text.split('.') if len(s.strip()) > 10]
            first_few = ". ".join(sentences[:3]) + ("." if sentences else "")
            summary_dict = {
                "summary": first_few or transcript_text[:300],
                "key_decisions": [],
                "action_items": [],
                "participants": [],
                "key_points": [s for s in sentences[:5]],
                "deadlines": [],
                "priorities": []
            }

        # Stage 6: Action Item Structuring
        update_progress("Structuring Action Items & Priorities...", max(start_progress_pct + 15, 80))
        from src.action_item_extractor import ExtractedActionItem
        action_raw = summary_dict.get("action_items", [])
        action_items = [
            ExtractedActionItem(
                action=a.get("action", ""),
                owner=a.get("owner"),
                deadline=a.get("deadline"),
                priority=a.get("priority") or "Medium",
                status=a.get("status") or "Pending"
            ) if isinstance(a, dict) else a
            for a in action_raw
        ]
        action_dicts = [a.to_dict() if isinstance(a, ExtractedActionItem) else a for a in action_items]

        # Stage 7: Participant & Responsibility Mapping
        update_progress("Mapping Participants & Responsibilities...", max(start_progress_pct + 25, 90))
        mapped_participants = self.participant_mapper.map_responsibilities(
            transcript=transcript_text,
            action_items=action_items,
            meeting_id=meeting_title,
            participants=summary_dict.get("participants", [])
        )
        participant_dicts = [p.to_dict() for p in mapped_participants]

        # Stage 8: Database Persistence (Task 5)
        update_progress("Persisting to SQLite Database...", 95)
        meeting_id = self.db_manager.save_meeting_intelligence(
            title=meeting_title,
            transcript_text=transcript_text,
            summary_text=summary_dict.get("summary", ""),
            decisions=summary_dict.get("key_decisions", []),
            action_items=action_dicts,
            participants=participant_dicts,
            original_filename=original_filename,
            duration=duration
        )

        # Stage 9: Dynamic Embedding Generation (Milestone 3 Task 2)
        update_progress("Generating Vector Embeddings for AI Search...", 98)
        try:
            embeddings = self.embedding_generator.generate_all_meeting_embeddings(
                meeting_id=meeting_id,
                transcript_text=transcript_text,
                summary_text=summary_dict.get("summary", ""),
                decisions=summary_dict.get("key_decisions", []),
                action_items=action_dicts
            )
            self.db_manager.save_embeddings(embeddings)
            logger.info(f"Dynamically generated & saved {len(embeddings)} embeddings for meeting {meeting_id}")
        except Exception as e:
            logger.warning(f"Dynamic embedding generation encountered an error: {e}")

        update_progress("Pipeline processing completed successfully!", 100)

        return {
            "meeting_id": meeting_id,
            "title": meeting_title,
            "original_filename": original_filename,
            "duration": duration,
            "transcript": transcript_text,
            "summary": summary_dict.get("summary", ""),
            "decisions": summary_dict.get("key_decisions", []),
            "action_items": action_dicts,
            "participants": participant_dicts,
            "metrics": self.action_extractor.get_metrics(action_items),
            "database_persisted": True
        }
