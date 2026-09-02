# AI Career Intelligence Platform

An AI-powered platform for career intelligence, starting with audio/video transcription capabilities.

## Project Structure

```
AI-Career-Intelligence-Platform/
├── app.py                          # Main Streamlit interface
├── requirements.txt                 # Python dependencies
├── README.md                       # This file
├── src/                            # Source modules
│   ├── __init__.py                # Package initialization
│   ├── audio_processor.py         # Audio/video processing with FFmpeg
│   ├── transcriber.py             # Whisper transcription
│   ├── validator.py               # File and transcript validation
│   └── transcript_manager.py      # Transcript storage management
├── data/                           # Data directories
│   ├── uploads/                   # Uploaded files
│   ├── audio/                     # Processed audio files
│   └── transcripts/               # Saved transcripts
├── tests/                          # Test files
│   ├── test_transcription.py      # Transcription tests
│   ├── test_upload.py             # Upload validation tests
│   └── test_validation.py         # Transcript validation tests
└── outputs/                       # Output files
```

## Required Software

- **Python 3.9+** - Main programming language
- **FFmpeg** - Audio/video processing (required)
- **Git** - Version control (optional)

## Installation Instructions (Windows)

### 1. Install Python
Download and install Python 3.9 or higher from [python.org](https://www.python.org/downloads/)

### 2. Install FFmpeg
Download FFmpeg from [https://www.gyan.dev/ffmpeg/builds/](https://www.gyan.dev/ffmpeg/builds/)
- Extract the downloaded file
- Add the `bin` folder to your Windows PATH
- Or use Chocolatey: `choco install ffmpeg`

### 3. Clone/Create Project
```powershell
cd c:\Users\DELL\Desktop\AI
```

### 4. Create Virtual Environment
```powershell
cd AI-Career-Intelligence-Platform
python -m venv venv
```

### 5. Activate Virtual Environment
```powershell
venv\Scripts\activate
```

### 6. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 7. Run the Application
```powershell
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

## Module Descriptions

### src/audio_processor.py
Handles audio/video processing using FFmpeg:
- Extracts audio from video files
- Converts audio to WAV format (16kHz, mono)
- Gets audio duration

### src/transcriber.py
Performs speech-to-text transcription:
- Uses Whisper or faster-whisper models
- Supports multiple model sizes (tiny, base, small, medium, large)
- Returns transcript with metadata

### src/validator.py
Validates files and transcripts:
- Checks file formats (audio: mp3, wav, m4a, etc.; video: mp4, avi, mov, etc.)
- Validates file size (max 500MB)
- Validates transcript content and length

### src/transcript_manager.py
Manages transcript storage:
- Saves transcripts as JSON files
- Loads saved transcripts
- Lists and deletes transcripts

### app.py
Main Streamlit interface:
- File upload widget
- Transcription button
- Progress indicators
- Transcript display
- Saved transcripts viewer

## Usage

1. **Launch the application**: `streamlit run app.py`
2. **Upload a file**: Use the file uploader to select an audio or video file
3. **Click "Transcribe Recording"**: The app will process and transcribe your file
4. **View the transcript**: The transcribed text will appear in the text area
5. **Access saved transcripts**: View previously saved transcripts in the bottom section

## Supported Formats

**Audio**: .mp3, .wav, .m4a, .flac, .aac, .ogg, .wma

**Video**: .mp4, .avi, .mov, .mkv, .webm, .wmv, .flv

## Running Tests

```powershell
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_transcription.py -v

# Run with coverage
pytest tests/ --cov=src
```

## Troubleshooting

### FFmpeg not found
- Ensure FFmpeg is installed and added to PATH
- Test with: `ffmpeg -version` in command prompt

### Model download issues
- Whisper models will download automatically on first run
- Ensure stable internet connection
- Models are cached locally for future use

### Memory issues
- Use smaller model size (tiny or base) for limited RAM
- Process shorter audio files initially

## Current Features (Milestone 1)

- ✅ Audio/video file upload
- ✅ File format validation
- ✅ Audio extraction from video
- ✅ Whisper transcription
- ✅ Transcript validation
- ✅ Transcript saving/loading
- ✅ Streamlit interface

## Future Modules

- Career analysis
- Interview preparation
- Resume parsing
- Skill assessment
- Job matching

## License

MIT License
