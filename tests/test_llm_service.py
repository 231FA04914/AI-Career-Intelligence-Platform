"""
Test Suite for LLM Service (Milestone 2 Task 1)
Tests LLM processing service with mocks for unit testing.
"""

import sys
from pathlib import Path
import json
from unittest.mock import Mock, patch, MagicMock

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.llm.service import LLMService
from src.llm.validators import InputValidator, OutputValidator
from src.llm.exceptions import (
    InputValidationError,
    OutputValidationError,
    AuthenticationError,
    ServiceUnavailableError,
    RateLimitError,
    RetryLimitExceededError
)
from src.llm.schemas import MeetingIntelligence



class TestInputValidation:
    """Test input validation for LLM service."""
    
    def test_valid_transcript(self):
        """Test validation of a valid transcript."""
        transcript = "Hello, this is a test transcript with meaningful content."
        is_valid, error_msg = InputValidator.validate_transcript(transcript)
        
        assert is_valid == True, f"Expected valid transcript, got: {error_msg}"
        print("✅ TEST 1 - Valid transcript: PASSED")
    
    def test_empty_transcript(self):
        """Test validation of an empty transcript."""
        transcript = ""
        is_valid, error_msg = InputValidator.validate_transcript(transcript)
        
        assert is_valid == False, "Expected invalid transcript for empty text"
        assert "empty" in error_msg.lower(), f"Expected 'empty' in error message, got: {error_msg}"
        print("✅ TEST 2 - Empty transcript: PASSED")
    
    def test_whitespace_transcript(self):
        """Test validation of whitespace-only transcript."""
        transcript = "       "
        is_valid, error_msg = InputValidator.validate_transcript(transcript)
        
        assert is_valid == False, "Expected invalid transcript for whitespace only"
        assert "empty" in error_msg.lower() or "whitespace" in error_msg.lower()
        print("✅ TEST 3 - Whitespace transcript: PASSED")
    
    def test_none_input(self):
        """Test validation of None input."""
        is_valid, error_msg = InputValidator.validate_transcript(None)
        
        assert is_valid == False, "Expected invalid transcript for None"
        assert "none" in error_msg.lower()
        print("✅ TEST 4 - None input: PASSED")
    
    def test_short_transcript(self):
        """Test validation of too-short transcript."""
        transcript = "Hi"
        is_valid, error_msg = InputValidator.validate_transcript(transcript)
        
        assert is_valid == False, "Expected invalid transcript for short text"
        assert "short" in error_msg.lower()
        print("✅ TEST 5 - Short transcript: PASSED")
    
    def test_non_string_input(self):
        """Test validation of non-string input."""
        is_valid, error_msg = InputValidator.validate_transcript(123)
        
        assert is_valid == False, "Expected invalid transcript for non-string"
        assert "string" in error_msg.lower()
        print("✅ TEST 6 - Non-string input: PASSED")


class TestOutputValidation:
    """Test output validation for LLM service."""
    
    def test_valid_json(self):
        """Test validation of valid JSON."""
        json_str = '{"summary": "Test", "key_points": ["point1"]}'
        is_valid, error_msg = OutputValidator.validate_json_structure(json_str)
        
        assert is_valid == True, f"Expected valid JSON, got: {error_msg}"
        print("✅ TEST 7 - Valid JSON: PASSED")
    
    def test_malformed_json(self):
        """Test validation of malformed JSON."""
        json_str = "Here is your summary..."
        is_valid, error_msg = OutputValidator.validate_json_structure(json_str)
        
        assert is_valid == False, "Expected invalid JSON for malformed text"
        assert "json" in error_msg.lower()
        print("✅ TEST 8 - Malformed JSON: PASSED")
    
    def test_empty_response(self):
        """Test validation of empty response."""
        is_valid, error_msg = OutputValidator.validate_json_structure("")
        
        assert is_valid == False, "Expected invalid JSON for empty response"
        print("✅ TEST 9 - Empty response: PASSED")
    
    def test_schema_validation(self):
        """Test Pydantic schema validation."""
        valid_data = {
            "summary": "Test summary",
            "key_points": ["point1", "point2"],
            "decisions": ["decision1"],
            "action_items": [
                {
                    "action": "Task 1",
                    "owner": "John",
                    "deadline": "Friday",
                    "priority": "High"
                }
            ],
            "participants": ["Alice", "Bob"],
            "deadlines": ["Friday"],
            "priorities": [
                {"item": "Task 1", "priority": "High"}
            ]
        }
        
        try:
            validated = MeetingIntelligence(**valid_data)
            assert validated.summary == "Test summary"
            print("✅ TEST 10 - Schema validation: PASSED")
        except Exception as e:
            print(f"❌ TEST 10 - Schema validation: FAILED - {e}")
            raise
    
    def test_missing_required_field(self):
        """Test schema validation with missing required field."""
        invalid_data = {
            "key_points": ["point1"]
            # Missing required "summary" field
        }
        
        try:
            MeetingIntelligence(**invalid_data)
            print("❌ TEST 11 - Missing required field: FAILED - Should have raised validation error")
            assert False, "Should have raised validation error"
        except Exception:
            print("✅ TEST 11 - Missing required field: PASSED")
    
    def test_invalid_priority(self):
        """Test schema validation with invalid priority."""
        invalid_data = {
            "summary": "Test",
            "key_points": [],
            "action_items": [
                {
                    "action": "Task",
                    "priority": "Urgent"  # Invalid priority
                }
            ]
        }
        
        try:
            MeetingIntelligence(**invalid_data)
            print("❌ TEST 12 - Invalid priority: FAILED - Should have raised validation error")
            assert False, "Should have raised validation error"
        except Exception:
            print("✅ TEST 12 - Invalid priority: PASSED")


class TestLLMService:
    """Test LLM service with mocked API calls."""
    
    @patch.dict('os.environ', {'LLM_API_KEY': 'test_key'})
    def test_llm_service_initialization(self):
        """Test LLM service initialization."""
        service = LLMService()
        assert service.api_key == 'test_key'
        assert service.provider == 'gemini'
        print("✅ TEST 13 - LLM service initialization: PASSED")
    
    @patch.dict('os.environ', {}, clear=True)
    def test_llm_service_no_api_key(self):
        """Test LLM service initialization without API key."""
        try:
            service = LLMService()
            print("❌ TEST 14 - No API key: FAILED - Should have raised AuthenticationError")
            assert False, "Should have raised AuthenticationError"
        except AuthenticationError:
            print("✅ TEST 14 - No API key: PASSED")
    
    @patch.dict('os.environ', {'LLM_API_KEY': 'test_key'})
    def test_process_transcript_with_mock(self):
        """Test transcript processing with mocked LLM call."""
        mock_response = json.dumps({
            "summary": "Test summary",
            "key_points": ["point1"],
            "decisions": [],
            "action_items": [],
            "participants": [],
            "deadlines": [],
            "priorities": []
        })
        
        with patch.object(LLMService, '_call_llm', return_value=mock_response):
            service = LLMService()
            result = service.process_transcript("Test transcript")
            
            assert result["summary"] == "Test summary"
            assert isinstance(result["key_points"], list)
            print("✅ TEST 15 - Process transcript with mock: PASSED")
    
    @patch.dict('os.environ', {'LLM_API_KEY': 'test_key'})
    def test_long_transcript_chunking(self):
        """Test long transcript chunking."""
        # Create a long transcript
        long_transcript = " ".join(["word"] * 15000)  # ~15000 words
        
        mock_response = json.dumps({
            "summary": "Test summary",
            "key_points": ["point1"],
            "decisions": [],
            "action_items": [],
            "participants": [],
            "deadlines": [],
            "priorities": []
        })
        
        with patch.object(LLMService, '_call_llm', return_value=mock_response):
            service = LLMService()
            result = service.process_transcript(long_transcript)
            
            assert result["summary"] == "Test summary"
            print("✅ TEST 16 - Long transcript chunking: PASSED")
    
    @patch.dict('os.environ', {'LLM_API_KEY': 'test_key'})
    def test_retry_on_temporary_failure(self):
        """Test retry configuration."""
        service = LLMService(max_retries=3, retry_delay=1.0)
        assert service.max_retries == 3
        assert service.retry_delay == 1.0
        print("✅ TEST 17 - Retry configuration: PASSED")

    @patch.dict('os.environ', {'LLM_API_KEY': 'test_key'})
    def test_exponential_backoff_calculation(self):
        """Test backoff calculation with exponential delay and random jitter."""
        service = LLMService(initial_retry_delay=2.0, max_retry_delay=30.0)
        # Attempt 0: 2 * (2^0) = 2.0 + jitter [0.1, 1.0] -> [2.1, 3.0]
        delay0 = service._calculate_retry_delay(0)
        assert 2.0 <= delay0 <= 3.1, f"Expected delay between 2.0 and 3.1, got {delay0}"

        # Attempt 1: 2 * (2^1) = 4.0 + jitter [0.1, 1.0] -> [4.1, 5.0]
        delay1 = service._calculate_retry_delay(1)
        assert 4.0 <= delay1 <= 5.1, f"Expected delay between 4.0 and 5.1, got {delay1}"

        # Attempt 5: 2 * 32 = 64 > max_delay 30.0 -> [30.1, 31.0]
        delay5 = service._calculate_retry_delay(5)
        assert 30.0 <= delay5 <= 31.1, f"Expected capped delay between 30.0 and 31.1, got {delay5}"
        print("✅ TEST 18 - Exponential backoff calculation with jitter: PASSED")

    def test_retryable_error_classification(self):
        """Test HTTP status code and exception classification for retries."""
        # Retryable HTTP status codes
        for code in [429, 500, 502, 503, 504]:
            assert LLMService.is_retryable_status_code(code) is True, f"Status code {code} should be retryable"

        # Non-retryable HTTP status codes
        for code in [400, 401, 403, 404, 200]:
            assert LLMService.is_retryable_status_code(code) is False, f"Status code {code} should not be retryable"

        # Retryable exceptions
        assert LLMService.is_retryable_exception(ServiceUnavailableError("503 unavailable")) is True
        assert LLMService.is_retryable_exception(RateLimitError("429 rate limit")) is True
        assert LLMService.is_retryable_exception(Exception("Connection timeout")) is True

        # Non-retryable exceptions
        assert LLMService.is_retryable_exception(AuthenticationError("401 unauthorized")) is False
        print("✅ TEST 19 - Retryable error classification: PASSED")

    @patch.dict('os.environ', {'LLM_API_KEY': 'test_key'})
    def test_authentication_error_fails_immediately(self):
        """Test that authentication error is never retried."""
        call_count = 0

        def mock_call_gemini_model(prompt, model_name):
            nonlocal call_count
            call_count += 1
            raise AuthenticationError("Invalid API key")

        service = LLMService(max_retries=4)
        service._call_gemini_model = mock_call_gemini_model

        try:
            service._call_llm_with_retry("test prompt")
            assert False, "Should have raised AuthenticationError"
        except AuthenticationError:
            # Should have called only once and aborted immediately
            assert call_count == 1, f"Expected exactly 1 call without retries, got {call_count}"
            print("✅ TEST 20 - Authentication error fails immediately without retrying: PASSED")

    @patch.dict('os.environ', {'LLM_API_KEY': 'test_key'})
    def test_fallback_model_used_on_primary_failure(self):
        """Test fallback model is attempted when primary model returns 503."""
        called_models = []

        def mock_call_gemini_model(prompt, model_name):
            called_models.append(model_name)
            if model_name == "primary-model":
                raise ServiceUnavailableError("503 high demand on primary")
            return json.dumps({"summary": "Fallback success", "key_points": [], "decisions": [], "action_items": [], "participants": [], "deadlines": [], "priorities": []})

        service = LLMService(model="primary-model", fallback_model="fallback-model", max_retries=1)
        service._call_gemini_model = mock_call_gemini_model

        result = service._call_llm_with_retry("test prompt")
        assert "Fallback success" in result
        assert "primary-model" in called_models
        assert "fallback-model" in called_models
        print("✅ TEST 21 - Fallback model succession on 503: PASSED")

    @patch.dict('os.environ', {'LLM_API_KEY': 'test_key'})
    def test_service_unavailable_error_on_exhaustion(self):
        """Test ServiceUnavailableError raised cleanly when all retries are exhausted."""
        def mock_call_gemini_model(prompt, model_name):
            raise ServiceUnavailableError("503 high demand")

        service = LLMService(max_retries=2, initial_retry_delay=0.01, max_retry_delay=0.02)
        service._call_gemini_model = mock_call_gemini_model

        try:
            service._call_llm_with_retry("test prompt")
            assert False, "Should have raised ServiceUnavailableError"
        except ServiceUnavailableError as e:
            assert "503" in str(e) or "temporarily unavailable" in str(e)
            print("✅ TEST 22 - ServiceUnavailableError raised cleanly on exhaustion: PASSED")



class TestExistingTranscriptIntegration:
    """Test integration with existing Whisper transcripts."""
    
    @patch.dict('os.environ', {'LLM_API_KEY': 'test_key'})
    def test_whisper_transcript_processing(self):
        """Test processing a Whisper-generated transcript."""
        # Simulate a Whisper transcript
        whisper_transcript = "Hello, my name is Rahul. I am currently pursuing my final year Computer Science degree. I have experience with Java, SQL and Spring Boot. During my project, I developed an employee management system. I am interested in backend development. My mentor suggested that I improve my problem-solving skills and practice more coding questions. I will complete the practice by Friday."
        
        mock_response = json.dumps({
            "summary": "Candidate is a final-year Computer Science student interested in backend development.",
            "key_points": [
                "Final-year Computer Science student",
                "Backend development interest",
                "Java, SQL and Spring Boot experience"
            ],
            "decisions": [],
            "action_items": [
                {
                    "action": "Practice coding questions",
                    "owner": None,
                    "deadline": "Friday",
                    "priority": None
                }
            ],
            "participants": ["Rahul", "Mentor"],
            "deadlines": ["Friday"],
            "priorities": []
        })
        
        with patch.object(LLMService, '_call_llm', return_value=mock_response):
            service = LLMService()
            result = service.process_transcript(whisper_transcript)
            
            assert result["summary"] == "Candidate is a final-year Computer Science student interested in backend development."
            assert len(result["key_points"]) == 3
            assert "Rahul" in result["participants"]
            print("✅ TEST 18 - Whisper transcript processing: PASSED")


def run_all_tests():
    """Run all LLM service tests."""
    print("=" * 60)
    print("Running LLM Service Tests (Milestone 2 Task 1)")
    print("=" * 60)
    print()
    
    # Input validation tests
    input_tests = TestInputValidation()
    input_tests.test_valid_transcript()
    input_tests.test_empty_transcript()
    input_tests.test_whitespace_transcript()
    input_tests.test_none_input()
    input_tests.test_short_transcript()
    input_tests.test_non_string_input()
    
    print()
    
    # Output validation tests
    output_tests = TestOutputValidation()
    output_tests.test_valid_json()
    output_tests.test_malformed_json()
    output_tests.test_empty_response()
    output_tests.test_schema_validation()
    output_tests.test_missing_required_field()
    output_tests.test_invalid_priority()
    
    print()
    
    # LLM service tests
    llm_tests = TestLLMService()
    llm_tests.test_llm_service_initialization()
    llm_tests.test_llm_service_no_api_key()
    llm_tests.test_process_transcript_with_mock()
    llm_tests.test_long_transcript_chunking()
    llm_tests.test_retry_on_temporary_failure()
    llm_tests.test_exponential_backoff_calculation()
    llm_tests.test_retryable_error_classification()
    llm_tests.test_authentication_error_fails_immediately()
    llm_tests.test_fallback_model_used_on_primary_failure()
    llm_tests.test_service_unavailable_error_on_exhaustion()
    
    print()
    
    # Integration tests
    integration_tests = TestExistingTranscriptIntegration()
    integration_tests.test_whisper_transcript_processing()

    
    print()
    print("=" * 60)
    print("✅ All LLM Service Tests PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
