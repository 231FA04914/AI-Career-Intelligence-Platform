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

## Current Features

### Milestone 1: Audio Processing & Transcription
- ✅ Audio/video file upload (.mp3, .wav, .mp4, .mkv, etc.)
- ✅ File format & duration validation
- ✅ Audio extraction from video using FFmpeg
- ✅ Whisper speech-to-text transcription
- ✅ Transcript quality metrics and validation
- ✅ Local transcript storage management

### Milestone 2: Summarization & Action Extraction
- ✅ **Task 1: LLM Service & Prompt Engineering**
  - Configurable LLM service with Google Gemini API (`gemini-3.6-flash`)
  - Structured output generation (Summary, Key Points, Decisions, Action Items, Participants, Deadlines, Priorities)
  - Anti-hallucination prompt design
  - Automatic chunking for long transcripts
  - Exponential backoff retry logic & error handling
- ✅ **Task 2: Meeting Summarization Module**
  - Production-ready meeting summarizer (`src/summarizer.py`)
  - Executive summary extraction
  - Key decisions tracking
  - Action item extraction with owners & deadlines formatted as `Action – Owner Deadline`
  - Multi-format export (Markdown `.md`, Plain Text `.txt`, JSON `.json`)
  - Persistent summary archive manager (`src/summary_manager.py`)
  - Interactive Streamlit dashboard integration with one-click transcript selection
- ✅ **Task 3: Action Item Extraction Engine**
  - Dedicated task extraction pipeline (`src/action_item_extractor.py`)
  - Tracks 4 core attributes: **Assigned Participant**, **Deadline**, **Priority**, and **Status**
  - Interactive status management (Pending, In Progress, Completed, Blocked)
  - Multi-attribute filtering (by Assignee, Priority, Status, keyword search)
  - Flexible sorting (by Priority, Deadline, Assignee, Status)
  - Multi-format exports: CSV (`.csv`), Markdown Table (`.md`), and JSON (`.json`)
  - Live KPI metrics dashboard (Total Tasks, High Priority, Pending, In Progress, Completed)
- ✅ **Task 4: Participant & Responsibility Mapping**
  - Participant identification and alias canonicalization (`src/participant_mapper.py`)
  - Consistent name normalization and title stripping
  - Safe unknown participant handling (`Unassigned`)
  - Automatic duplicate record merging and responsibility aggregation
  - Links responsibilities and action items to corresponding meeting sessions
  - Responsibility matrix generation (Markdown table & JSON exports)
- ✅ **Task 5: Meeting Data Model & Database Persistence**
  - SQLite database layer (`src/database.py`) with relational schema
  - Tables: Meetings, Summaries, Decisions, Action Items, and Participants
  - Relational querying, cross-meeting task filtering, and status updates
  - Cascading deletion and transaction safety
- ✅ **Task 6: Processing API & Service Integration**
  - Complete end-to-end orchestration pipeline (`src/pipeline.py`)
  - Seamless flow: `Upload Media → Whisper Transcription → LLM Processing → Summary → Action Extraction → Participant Mapping → Database`
  - Real-time progress tracking across all pipeline stages
  - One-click full pipeline execution in the Streamlit UI

## Future Modules

- Career analysis
- Interview preparation
- Resume parsing
- Skill assessment
- Job matching

## License

MIT License
