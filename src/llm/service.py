"""
LLM Processing Service
Main service for processing transcripts with LLMs.
"""

import os
import json
import logging
import time
from typing import Dict, List, Optional
from pathlib import Path

from src.llm.exceptions import (
    LLMServiceError,
    InputValidationError,
    OutputValidationError,
    APIError,
    RateLimitError,
    AuthenticationError,
    ChunkingError,
    RetryLimitExceededError
)
from src.llm.prompts import PromptTemplates
from src.llm.validators import InputValidator, OutputValidator
from src.llm.schemas import MeetingIntelligence


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMService:
    """Service for processing transcripts with LLMs."""
    
    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize LLM Service.
        
        Args:
            provider: LLM provider (default: openai)
            model: Model name (default: gemini-3.5-flash)
            api_key: API key (default: from environment)
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        # Load configuration from environment variables
        self.provider = provider or os.getenv('LLM_PROVIDER', 'gemini')
        self.model = model or os.getenv('LLM_MODEL', 'gemini-3.5-flash')
        self.api_key = api_key or os.getenv('LLM_API_KEY')
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Validate required configuration
        if not self.api_key:
            raise AuthenticationError("LLM_API_KEY environment variable is required")
        
        # Token limit for context window (approximate)
        self.max_tokens = int(os.getenv('LLM_MAX_TOKENS', '4000'))
        self.chunk_size = int(os.getenv('LLM_CHUNK_SIZE', '3000'))
        
        logger.info(f"Initialized LLM Service with provider={self.provider}, model={self.model}")
    
    def process_transcript(self, transcript: str) -> Dict:
        """
        Process transcript and extract structured intelligence.
        
        Args:
            transcript: The transcript text to process
            
        Returns:
            Dictionary with structured meeting intelligence
            
        Raises:
            InputValidationError: If input validation fails
            LLMServiceError: If processing fails
        """
        # Validate input
        InputValidator.validate_and_raise(transcript)
        logger.info("Input validation passed")
        
        # Check if chunking is needed
        estimated_tokens = self._estimate_tokens(transcript)
        
        if estimated_tokens > self.chunk_size:
            logger.info(f"Transcript requires chunking (estimated {estimated_tokens} tokens)")
            return self._process_chunked_transcript(transcript)
        else:
            logger.info(f"Processing single chunk (estimated {estimated_tokens} tokens)")
            return self._process_single_chunk(transcript)
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Args:
            text: The text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        # Rough estimation: ~4 characters per token
        return len(text) // 4
    
    def _process_single_chunk(self, transcript: str) -> Dict:
        """
        Process a single transcript chunk.
        
        Args:
            transcript: The transcript to process
            
        Returns:
            Dictionary with structured intelligence
        """
        prompt = PromptTemplates.get_career_intelligence_prompt().format(transcript=transcript)
        
        response = self._call_llm_with_retry(prompt)
        
        # Validate and parse response
        validated_data = self._validate_and_parse_response(response)
        
        return validated_data
    
    def _process_chunked_transcript(self, transcript: str) -> Dict:
        """
        Process a long transcript by chunking it.
        
        Args:
            transcript: The long transcript to process
            
        Returns:
            Dictionary with combined structured intelligence
        """
        chunks = self._chunk_transcript(transcript)
        logger.info(f"Split transcript into {len(chunks)} chunks")
        
        chunk_results = []
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)}")
            try:
                chunk_result = self._process_single_chunk(chunk)
                chunk_results.append(chunk_result)
            except Exception as e:
                logger.error(f"Error processing chunk {i+1}: {str(e)}")
                raise ChunkingError(f"Failed to process chunk {i+1}: {str(e)}")
        
        # Combine chunk results
        combined_result = self._combine_chunk_results(chunk_results)
        logger.info("Successfully combined chunk results")
        
        return combined_result
    
    def _chunk_transcript(self, transcript: str) -> List[str]:
        """
        Split transcript into manageable chunks.
        
        Args:
            transcript: The transcript to chunk
            
        Returns:
            List of transcript chunks
        """
        chunks = []
        words = transcript.split()
        current_chunk = []
        current_length = 0
        
        for word in words:
            word_length = len(word) + 1  # +1 for space
            if current_length + word_length > self.chunk_size * 4:  # Convert to characters
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = word_length
            else:
                current_chunk.append(word)
                current_length += word_length
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _combine_chunk_results(self, chunk_results: List[Dict]) -> Dict:
        """
        Combine results from multiple chunks.
        
        Args:
            chunk_results: List of chunk result dictionaries
            
        Returns:
            Combined result dictionary
        """
        combined = {
            "summary": "",
            "key_points": [],
            "decisions": [],
            "action_items": [],
            "participants": [],
            "deadlines": [],
            "priorities": []
        }
        
        # Combine summaries (use first chunk's summary as main)
        if chunk_results:
            combined["summary"] = chunk_results[0].get("summary", "")
        
        # Combine lists, removing duplicates
        for result in chunk_results:
            combined["key_points"].extend(result.get("key_points", []))
            combined["decisions"].extend(result.get("decisions", []))
            combined["action_items"].extend(result.get("action_items", []))
            combined["participants"].extend(result.get("participants", []))
            combined["deadlines"].extend(result.get("deadlines", []))
            combined["priorities"].extend(result.get("priorities", []))
        
        # Remove duplicates while preserving order
        combined["key_points"] = list(dict.fromkeys(combined["key_points"]))
        combined["decisions"] = list(dict.fromkeys(combined["decisions"]))
        combined["participants"] = list(dict.fromkeys(combined["participants"]))
        combined["deadlines"] = list(dict.fromkeys(combined["deadlines"]))
        
        return combined
    
    def _call_llm_with_retry(self, prompt: str) -> str:
        """
        Call LLM with retry logic.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            LLM response as string
            
        Raises:
            APIError: If all retry attempts fail
            AuthenticationError: If authentication fails
            RateLimitError: If rate limit is exceeded
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"LLM call attempt {attempt + 1}/{self.max_retries}")
                response = self._call_llm(prompt)
                logger.info("LLM call successful")
                return response
            except RateLimitError as e:
                last_exception = e
                logger.warning(f"Rate limit hit, attempt {attempt + 1}")
                if attempt < self.max_retries - 1:
                    wait_time = max(3.0, self.retry_delay * (2 ** (attempt + 1)))  # Exponential backoff for rate limits
                    logger.info(f"Rate limit hit. Waiting {wait_time}s before retry attempt {attempt + 2}...")
                    time.sleep(wait_time)
                else:
                    raise
            except AuthenticationError as e:
                # Authentication errors are not retryable
                logger.error("Authentication failed")
                raise
            except APIError as e:
                last_exception = e
                logger.warning(f"API error, attempt {attempt + 1}: {str(e)}")
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (attempt + 1)
                    logger.info(f"Waiting {wait_time}s before retry")
                    time.sleep(wait_time)
        
        raise RetryLimitExceededError(f"Max retries ({self.max_retries}) exceeded. Last error: {str(last_exception)}")
    
    def _call_llm(self, prompt: str) -> str:
        """
        Call the LLM API.
        
        Args:
            prompt: The prompt to send
            
        Returns:
            LLM response as string
            
        Raises:
            APIError: If API call fails
            AuthenticationError: If authentication fails
            RateLimitError: If rate limit is exceeded
        """
        try:
            if self.provider == 'gemini':
                return self._call_gemini(prompt)
            else:
                raise APIError(f"Unsupported provider: {self.provider}")
        except AuthenticationError:
            raise
        except RateLimitError:
            raise
        except Exception as e:
            raise APIError(f"API call failed: {str(e)}")
    
    def _call_gemini(self, prompt: str) -> str:
        """
        Call Google Gemini API using REST API with automatic model fallback.
        
        Args:
            prompt: The prompt to send
            
        Returns:
            API response as string
        """
        try:
            import requests
        except ImportError:
            raise APIError("Requests package not installed. Install with: pip install requests")
        
        # Build candidate models list starting with configured model
        candidate_models = [self.model]
        for fallback in ["gemini-3.5-flash", "gemini-3.7-flash", "gemini-3.1-flash-lite"]:
            if fallback not in candidate_models:
                candidate_models.append(fallback)
        
        last_error = None
        for current_model in candidate_models:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{current_model}:generateContent?key={self.api_key}"
                headers = {"Content-Type": "application/json"}
                payload = {
                    "contents": [{
                        "parts": [{
                            "text": prompt
                        }]
                    }],
                    "generationConfig": {
                        "temperature": 0.2,
                        "maxOutputTokens": 4096,
                        "responseMimeType": "application/json"
                    }
                }
                
                response = requests.post(url, headers=headers, json=payload, timeout=45)
                
                # If model doesn't support responseMimeType, retry without it
                if response.status_code == 400 and "responseMimeType" in response.text:
                    payload["generationConfig"].pop("responseMimeType", None)
                    response = requests.post(url, headers=headers, json=payload, timeout=45)
                
                if response.status_code in (401, 403):
                    raise AuthenticationError("Gemini authentication failed. Please check your API key.")
                elif response.status_code in (404, 429):
                    # Rate limit or unsupported model -> try next fallback model
                    logger.warning(f"Model {current_model} returned {response.status_code}. Attempting fallback model...")
                    last_error = f"{response.status_code} on {current_model}"
                    continue
                elif response.status_code != 200:
                    raise APIError(f"Gemini API error: {response.status_code} - {response.text}")
                
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    return result['candidates'][0]['content']['parts'][0]['text']
                else:
                    raise APIError(f"Unexpected response format: {result}")
                    
            except AuthenticationError:
                raise
            except APIError:
                raise
            except Exception as e:
                error_str = str(e).lower()
                if 'api_key_invalid' in error_str or 'unauthenticated' in error_str:
                    raise AuthenticationError("Gemini authentication failed")
                elif 'quota' in error_str or 'rate limit' in error_str:
                    logger.warning(f"Quota error on {current_model}: {e}. Trying fallback...")
                    last_error = str(e)
                    continue
                else:
                    raise APIError(f"Gemini API error: {str(e)}")
        
        # If all candidates exhausted
        raise RateLimitError(f"All Gemini models reached quota/rate limits. Last error: {last_error}")
    
    def _validate_and_parse_response(self, response: str) -> Dict:
        """
        Validate and parse LLM response.
        
        Args:
            response: The LLM response string
            
        Returns:
            Parsed and validated dictionary
            
        Raises:
            OutputValidationError: If validation fails
        """
        # Clean markdown formatting if present
        cleaned_response = OutputValidator.clean_json_string(response)
        
        # Validate JSON structure
        OutputValidator.validate_and_raise_json(cleaned_response)
        
        # Parse JSON
        try:
            data = json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            raise OutputValidationError(f"Failed to parse JSON: {str(e)}")
            
        if isinstance(data, list):
            data = {
                "summary": "",
                "key_points": [],
                "decisions": [],
                "action_items": data,
                "participants": [],
                "deadlines": [],
                "priorities": []
            }
        
        # Validate schema using Pydantic
        try:
            validated_data = MeetingIntelligence(**data)
            return validated_data.dict()
        except Exception as e:
            logger.warning(f"Pydantic strict schema check issue: {e}. Applying soft field normalization.")
            try:
                # Soft recovery normalization
                actions_raw = data.get("action_items") or []
                norm_actions = []
                for a in actions_raw:
                    if isinstance(a, dict):
                        p_val = a.get("priority")
                        if p_val and str(p_val).capitalize() in ['High', 'Medium', 'Low']:
                            p_clean = str(p_val).capitalize()
                        elif p_val and 'high' in str(p_val).lower():
                            p_clean = 'High'
                        elif p_val and 'low' in str(p_val).lower():
                            p_clean = 'Low'
                        elif p_val and 'med' in str(p_val).lower():
                            p_clean = 'Medium'
                        else:
                            p_clean = None

                        norm_actions.append({
                            "action": str(a.get("action", "")),
                            "owner": a.get("owner"),
                            "deadline": a.get("deadline"),
                            "priority": p_clean,
                            "status": a.get("status", "Pending")
                        })
                    elif isinstance(a, str):
                        norm_actions.append({
                            "action": a,
                            "owner": None,
                            "deadline": None,
                            "priority": None,
                            "status": "Pending"
                        })

                priorities_raw = data.get("priorities") or []
                norm_priorities = []
                for p in priorities_raw:
                    if isinstance(p, dict):
                        norm_priorities.append({
                            "item": str(p.get("item", "")),
                            "priority": str(p.get("priority", "Medium")).capitalize()
                        })

                recovered = {
                    "summary": str(data.get("summary", "")),
                    "key_points": [str(x) for x in data.get("key_points", []) if x],
                    "decisions": [str(x) for x in data.get("decisions", []) if x],
                    "action_items": norm_actions,
                    "participants": [str(x) for x in data.get("participants", []) if x],
                    "deadlines": [str(x) for x in data.get("deadlines", []) if x],
                    "priorities": norm_priorities
                }
                return recovered
            except Exception as rec_err:
                raise OutputValidationError(f"Schema validation failed: {str(e)}")

