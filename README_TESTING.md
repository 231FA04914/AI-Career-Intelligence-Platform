# Transcription Accuracy Testing Guide (Task 5)

## Overview

This guide explains how to test the Whisper transcription system's accuracy using Word Error Rate (WER) calculation.

## Testing Methodology

### Word Error Rate (WER) Calculation

**WER Formula:**
```
WER = (Substitutions + Deletions + Insertions) / Total Reference Words × 100%
```

**Accuracy Formula:**
```
Accuracy = 100% - WER
```

### Error Types

1. **Substitutions** - Words replaced with incorrect words
2. **Deletions** - Words missing from transcription
3. **Insertions** - Extra words not in original speech

### Target

**Minimum Required Accuracy:** 90% (WER ≤ 10%)

## Test Dataset Structure

Create the following directory structure:

```
AI-Career-Intelligence-Platform/
├── test_data/
│   ├── test_config.json          # Test configuration file
│   └── recordings/               # Audio/video test recordings
│       ├── 4914_self_intro.mp4
│       ├── technical_response.mp4
│       ├── fast_speech.mp4
│       └── noisy_environment.mp4
└── test_results/
    └── accuracy_report.json      # Generated test report
```

## Test Configuration Format

Edit `test_data/test_config.json` with your test cases:

```json
{
  "test_cases": [
    {
      "test_name": "Test Name",
      "audio_path": "test_data/recordings/filename.mp4",
      "reference_transcript": "Exact spoken words...",
      "test_conditions": "Description of test conditions"
    }
  ]
}
```

## How to Run Tests

### Step 1: Prepare Test Recordings

1. Place your test audio/video files in `test_data/recordings/`
2. Create accurate reference transcripts for each recording
3. Update `test_data/test_config.json` with your test cases

### Step 2: Run Accuracy Tests

```powershell
python tests\accuracy_tester.py
```

### Step 3: Review Results

The test will generate a report at `test_results/accuracy_report.json` containing:
- Summary statistics
- Individual test results
- Error analysis
- Recommendations

## Test Conditions

For comprehensive testing, include recordings with:

- **Normal speech** - Clear, moderate pace
- **Fast speech** - Rapid speaking rate
- **Different accents** - Various pronunciation patterns
- **Background noise** - Environmental noise
- **Technical vocabulary** - Domain-specific terms

## Creating Reference Transcripts

1. **Listen carefully** to each recording
2. **Transcribe accurately** including:
   - All spoken words
   - Proper punctuation
   - Technical terms spelled correctly
3. **Verify** the transcript matches the audio exactly
4. **Save** in the test configuration file

## Example Test Report

```json
{
  "summary": {
    "total_tests": 4,
    "tests_passed": 3,
    "tests_failed": 1,
    "target_accuracy": 90.0,
    "average_accuracy": 92.5,
    "average_wer": 7.5,
    "target_met": true
  },
  "test_results": [
    {
      "test_name": "Self Introduction",
      "wer_metrics": {
        "wer": 5.2,
        "accuracy": 94.8,
        "substitutions": 2,
        "deletions": 1,
        "insertions": 0
      },
      "meets_target": true
    }
  ],
  "recommendations": [
    "✅ Accuracy meets or exceeds the 90% target."
  ]
}
```

## Interpreting Results

### Accuracy ≥ 90%
- ✅ System meets requirements
- ✅ Ready for production use
- 🎉 Good transcription quality

### Accuracy < 90%
- ❌ System below requirements
- 🔍 Review error patterns
- 💡 Implement recommendations

## Common Issues and Solutions

### High Deletion Rate
- **Cause:** Poor audio quality, background noise
- **Solution:** Improve recording quality, use noise reduction

### High Insertion Rate
- **Cause:** Background noise interpreted as speech
- **Solution:** Reduce noise, use larger Whisper model

### High Misrecognition Rate
- **Cause:** Technical terms, domain-specific vocabulary
- **Solution:** Use larger model, fine-tune for domain

## Recommendations for Improvement

If accuracy is below 90%:

1. **Audio Quality**
   - Use higher quality microphones
   - Record in quiet environments
   - Ensure proper microphone placement

2. **Audio Preprocessing**
   - Apply noise reduction
   - Normalize audio levels
   - Remove silence segments

3. **Model Selection**
   - Use larger Whisper model (medium or large)
   - Consider domain-specific fine-tuning
   - Adjust language settings

4. **Recording Practices**
   - Speak clearly and at moderate pace
   - Minimize background noise
   - Use consistent recording environment

## Running Individual Tests

You can also run tests programmatically:

```python
from tests.accuracy_tester import AccuracyTester

tester = AccuracyTester()
result = tester.run_test(
    audio_path="test_data/recordings/test.mp4",
    reference_transcript="Your reference transcript here...",
    test_name="My Test"
)
print(f"Accuracy: {result['wer_metrics']['accuracy']:.2f}%")
```

## Notes

- The testing script uses the Whisper "base" model by default
- For better accuracy, consider using "medium" or "large" models
- Reference transcripts must be accurate for valid WER calculation
- Test multiple recordings to get reliable accuracy metrics
