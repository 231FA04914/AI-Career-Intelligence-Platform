"""
AI Career Intelligence Platform - Main Application
Streamlit interface for audio transcription.
"""

import os
import ssl
import streamlit as st
import sys
from pathlib import Path

# Disable SSL verification for huggingface_hub
os.environ['HF_HUB_DISABLE_SSL_VERIFY'] = '1'
ssl._create_default_https_context = ssl._create_unverified_context

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.audio_processor import AudioProcessor
from src.transcriber import Transcriber
from src.validator import FileValidator, TranscriptValidator
from src.transcript_manager import TranscriptManager


# Page configuration
st.set_page_config(
    page_title="AI Career Intelligence Platform",
    page_icon="🎙️",
    layout="wide"
)


def main():
    """Main application function."""
    st.title("🎙️ AI Career Intelligence Platform")
    st.markdown("---")
    st.markdown("### Audio Processing & Transcription Module")
    
    # Initialize components
    audio_processor = AudioProcessor(use_temp=True)
    transcriber = Transcriber(model_size="base")
    file_validator = FileValidator()
    transcript_validator = TranscriptValidator()
    transcript_manager = TranscriptManager()
    
    # File upload section
    st.markdown("#### Upload Interview Recording")
    st.info(f"Supported formats: {file_validator.get_supported_formats()}")
    
    uploaded_file = st.file_uploader(
        "Choose an audio or video file",
        type=list(file_validator.AUDIO_FORMATS | file_validator.VIDEO_FORMATS)
    )
    
    if uploaded_file:
        # Display file info
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Filename:** {uploaded_file.name}")
            st.write(f"**File size:** {uploaded_file.size / (1024*1024):.2f} MB")
        with col2:
            file_type = "Video" if file_validator.is_video_file(uploaded_file.name) else "Audio"
            st.write(f"**Type:** {file_type}")
        
        # Save uploaded file
        upload_dir = Path(__file__).parent / "data" / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        upload_path = upload_dir / uploaded_file.name
        with open(upload_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Validate file
        is_valid, error_msg = file_validator.validate_file(str(upload_path))
        
        if not is_valid:
            st.error(f"❌ {error_msg}")
            # Clean up uploaded file
            if upload_path.exists():
                upload_path.unlink()
            return
        
        st.success("✅ File uploaded and validated successfully!")
        
        # Transcribe button
        st.markdown("---")
        if st.button("🎯 Transcribe Recording", type="primary"):
            audio_path = None
            try:
                # Step 1: Process audio
                with st.status("📁 Processing audio...", expanded=True) as status:
                    st.write("Extracting/converting audio for transcription...")
                    audio_path = audio_processor.extract_audio(str(upload_path))
                    st.write(f"✅ Audio processed: {audio_path}")
                    
                    # Get audio duration
                    duration = audio_processor.get_audio_duration(audio_path)
                    st.write(f"⏱️ Audio duration: {duration:.2f} seconds")
                    status.update(label="✅ Audio processing complete", state="complete")
                
                # Step 2: Transcribe with Whisper
                with st.status("🎤 Transcribing with Whisper...", expanded=True) as status:
                    st.write("Loading Whisper model and transcribing...")
                    transcript_data = transcriber.transcribe(audio_path)
                    st.write("✅ Transcription complete")
                    status.update(label="✅ Transcription complete", state="complete")
                
                # Step 3: Validate transcript
                is_valid, error_msg = transcript_validator.validate_transcript(transcript_data)
                
                if not is_valid:
                    st.error(f"❌ {error_msg}")
                    return
                
                # Step 4: Save transcript locally
                with st.status("💾 Saving transcript...", expanded=True) as status:
                    transcript_path = transcript_manager.save_transcript(
                        transcript_data,
                        uploaded_file.name,
                        metadata={"duration": duration, "audio_path": audio_path}
                    )
                    st.write(f"✅ Transcript saved to: {transcript_path}")
                    status.update(label="✅ Transcript saved", state="complete")
                
                # Step 5: Display transcript
                st.success("✅ Transcription completed successfully!")
                st.markdown("---")
                st.markdown("#### Transcript")
                st.text_area(
                    "Transcribed Text",
                    transcript_data["text"],
                    height=300,
                    key="transcript_output"
                )
                
                # Display quality metrics
                quality_metrics = transcript_validator.get_transcript_quality(transcript_data)
                with st.expander("📊 Transcript Quality Metrics"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Word Count", quality_metrics["word_count"])
                    with col2:
                        st.metric("Character Count", quality_metrics["character_count"])
                    with col3:
                        st.metric("Duration (s)", f"{quality_metrics['duration']:.1f}")
                    st.json(transcript_data)
                
                # Clean up temporary files
                audio_processor.cleanup_temp_files()
                
            except FileNotFoundError as e:
                st.error(f"❌ File not found: {str(e)}")
            except RuntimeError as e:
                st.error(f"❌ Processing error: {str(e)}")
            except Exception as e:
                st.error(f"❌ Error during transcription: {str(e)}")
                st.exception(e)
            finally:
                # Clean up temporary files even if error occurs
                if audio_processor:
                    audio_processor.cleanup_temp_files()
                # Clean up uploaded file
                if upload_path.exists():
                    upload_path.unlink()
    
    # List existing transcripts
    st.markdown("---")
    st.markdown("#### Saved Transcripts")
    transcripts = transcript_manager.list_transcripts()
    
    if transcripts:
        for transcript_path in transcripts:
            with st.expander(f"📄 {transcript_path.name}"):
                try:
                    data = transcript_manager.load_transcript(str(transcript_path))
                    st.text_area(
                        "Transcript",
                        data["transcript"]["text"],
                        height=200,
                        key=f"transcript_{transcript_path.name}"
                    )
                    st.caption(f"Original: {data['metadata']['original_filename']} | Timestamp: {data['metadata']['timestamp']}")
                except Exception as e:
                    st.error(f"Error loading transcript: {e}")
    else:
        st.info("No transcripts saved yet.")


if __name__ == "__main__":
    main()
