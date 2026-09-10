"""
Input and output validators for LLM Service.
"""

import re
from typing import Tuple
from src.llm.exceptions import InputValidationError, OutputValidationError


class InputValidator:
    """Validates input transcripts before LLM processing."""
    
    @staticmethod
    def validate_transcript(transcript: str) -> Tuple[bool, str]:
        """
        Validate transcript input.
        
        Args:
            transcript: The transcript text to validate
            
        Returns:
            Tuple of (is_valid, error_message)
            
        Raises:
            InputValidationError: If validation fails
        """
        # Check if input exists
        if transcript is None:
            return False, "Transcript cannot be None."
        
        # Check if input is a string
        if not isinstance(transcript, str):
            return False, "Transcript must be a string."
        
        # Check if input is empty
        if not transcript:
            return False, "Transcript cannot be empty."
        
        # Check if input is only whitespace
        if not transcript.strip():
            return False, "Transcript cannot be empty or only whitespace."
        
        # Check minimum length (at least 10 characters)
        if len(transcript.strip()) < 10:
            return False, "Transcript is too short (minimum 10 characters)."
        
        # Check for reasonable length (prevent extremely long inputs)
        if len(transcript) > 1000000:  # 1 million characters
            return False, "Transcript is too long (maximum 1,000,000 characters)."
        
        # Check for reasonable content (not just repeated characters)
        stripped = transcript.strip()
        unique_chars = set(stripped.lower())
        if len(unique_chars) < 5:
            return False, "Transcript does not contain meaningful content."
        
        return True, ""
    
    @staticmethod
    def validate_and_raise(transcript: str) -> None:
        """
        Validate transcript and raise exception if invalid.
        
        Args:
            transcript: The transcript text to validate
            
        Raises:
            InputValidationError: If validation fails
        """
        is_valid, error_msg = InputValidator.validate_transcript(transcript)
        if not is_valid:
            raise InputValidationError(error_msg)


class OutputValidator:
    """Validates LLM output responses."""
    
    @staticmethod
    def clean_json_string(json_str: str) -> str:
        """
        Strip markdown code fences, comments, and extra text to extract clean JSON.
        
        Args:
            json_str: The raw JSON string from LLM
            
        Returns:
            Cleaned JSON string
        """
        if not json_str:
            return ""
        s = json_str.strip()
        
        # Remove markdown code fences if present
        if "```json" in s:
            parts = s.split("```json", 1)[1]
            if "```" in parts:
                s = parts.split("```", 1)[0].strip()
            else:
                s = parts.strip()
        elif "```" in s:
            parts = s.split("```", 1)[1]
            if "```" in parts:
                s = parts.split("```", 1)[0].strip()
            else:
                s = parts.strip()
        
        # Find opening and closing brackets (either object {} or array [])
        start_obj = s.find('{')
        end_obj = s.rfind('}')
        start_arr = s.find('[')
        end_arr = s.rfind(']')
        
        # If object exists and either appears before array or no array exists
        if start_obj != -1 and end_obj != -1 and end_obj > start_obj:
            if start_arr == -1 or start_obj < start_arr:
                return s[start_obj:end_obj+1].strip()
        
        # If array exists
        if start_arr != -1 and end_arr != -1 and end_arr > start_arr:
            return s[start_arr:end_arr+1].strip()
            
        return s

    @staticmethod
    def validate_json_structure(json_str: str) -> Tuple[bool, str]:
        """
        Validate that response is valid JSON.
        
        Args:
            json_str: The JSON string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        import json
        
        if not json_str:
            return False, "Response is empty."
        
        if not isinstance(json_str, str):
            return False, "Response must be a string."
        
        cleaned = OutputValidator.clean_json_string(json_str)
        
        # Check if it looks like JSON (starts with { and ends with }, or [ and ])
        if not (cleaned.startswith('{') and cleaned.endswith('}')) and not (cleaned.startswith('[') and cleaned.endswith(']')):
            return False, "Response is not valid JSON format."
        
        try:
            json.loads(cleaned)
            return True, ""
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {str(e)}"
    
    @staticmethod
    def validate_and_raise_json(json_str: str) -> None:
        """
        Validate JSON and raise exception if invalid.
        
        Args:
            json_str: The JSON string to validate
            
        Raises:
            OutputValidationError: If validation fails
        """
        is_valid, error_msg = OutputValidator.validate_json_structure(json_str)
        if not is_valid:
            raise OutputValidationError(error_msg)

