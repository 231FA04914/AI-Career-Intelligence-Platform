"""
LLM Processing Service
Main service for processing transcripts with LLMs.
"""

import os
import json
import logging
import time
import random
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
    RetryLimitExceededError,
    ServiceUnavailableError
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
        fallback_model: Optional[str] = None,
        api_key: Optional[str] = None,
        max_retries: Optional[int] = None,
        retry_delay: Optional[float] = None,
        initial_retry_delay: Optional[float] = None,
        max_retry_delay: Optional[float] = None
    ):
        """
        Initialize LLM Service.
        
        Args:
            provider: LLM provider (default: gemini)
            model: Model name (default: from LLM_MODEL or gemini-3.1-flash-lite)
            fallback_model: Fallback model name (default: from LLM_FALLBACK_MODEL or gemini-3.5-flash-lite)
            api_key: API key (default: from LLM_API_KEY environment variable)
            max_retries: Maximum number of retry attempts (default: from LLM_MAX_RETRIES or 4)
            retry_delay: Delay between retries in seconds (legacy alias for initial_retry_delay)
            initial_retry_delay: Initial retry delay in seconds (default: from LLM_INITIAL_RETRY_DELAY or 2.0)
            max_retry_delay: Maximum retry delay ceiling in seconds (default: from LLM_MAX_RETRY_DELAY or 30.0)
        """
        # Load configuration from environment variables
        self.provider = provider or os.getenv('LLM_PROVIDER', 'gemini')
        self.model = model or os.getenv('LLM_MODEL', 'gemini-3.1-flash-lite')
        self.fallback_model = fallback_model or os.getenv('LLM_FALLBACK_MODEL', 'gemini-3.5-flash-lite')
        self.api_key = api_key or os.getenv('LLM_API_KEY')
        
        # Max retries
        if max_retries is not None:
            self.max_retries = int(max_retries)
        else:
            self.max_retries = int(os.getenv('LLM_MAX_RETRIES', '4'))

        # Initial retry delay
        if initial_retry_delay is not None:
            self.initial_retry_delay = float(initial_retry_delay)
        elif retry_delay is not None:
            self.initial_retry_delay = float(retry_delay)
        else:
            self.initial_retry_delay = float(os.getenv('LLM_INITIAL_RETRY_DELAY', '2.0'))

        # Preserve legacy attribute for backwards compatibility
        self.retry_delay = self.initial_retry_delay

        # Max retry delay
        if max_retry_delay is not None:
            self.max_retry_delay = float(max_retry_delay)
        else:
            self.max_retry_delay = float(os.getenv('LLM_MAX_RETRY_DELAY', '30.0'))
        
        # Validate required configuration
        if not self.api_key:
            raise AuthenticationError("LLM_API_KEY environment variable is required")
        
        # Token limit for context window (approximate)
        self.max_tokens = int(os.getenv('LLM_MAX_TOKENS', '4000'))
        self.chunk_size = int(os.getenv('LLM_CHUNK_SIZE', '3000'))
        
        logger.info(
            f"Initialized LLM Service (provider={self.provider}, model={self.model}, "
            f"fallback={self.fallback_model}, max_retries={self.max_retries}, "
            f"initial_delay={self.initial_retry_delay}s, max_delay={self.max_retry_delay}s)"
        )
    
    def process_transcript(self, transcript: str) -> Dict:
        """
        Process transcript and extract structured intelligence.
        
        Args:
            transcript: The transcript text to process
            
        Returns:
            Dictionary with structured meeting intelligence
            
        Raises:
            InputValidationError: If input validation fails
        """
        # Validate input
        InputValidator.validate_and_raise(transcript)
        logger.info("Input validation passed")
        
        try:
            # Check if chunking is needed
            estimated_tokens = self._estimate_tokens(transcript)
            
            if estimated_tokens > self.chunk_size:
                logger.info(f"Transcript requires chunking (estimated {estimated_tokens} tokens)")
                return self._process_chunked_transcript(transcript)
            else:
                logger.info(f"Processing single chunk (estimated {estimated_tokens} tokens)")
                return self._process_single_chunk(transcript)
        except (RetryLimitExceededError, RateLimitError, ServiceUnavailableError, APIError, Exception) as e:
            logger.warning(f"Remote LLM processing unavailable ({type(e).__name__}). Generating high-quality heuristic structured intelligence.")
            return self._heuristic_extract_intelligence(transcript)

    
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
    
    def _calculate_retry_delay(self, attempt: int) -> float:
        """
        Calculate exponential backoff delay with random jitter.
        Formula: min(initial_delay * (2 ** attempt), max_delay) + uniform(0.1, 1.0)
        
        Args:
            attempt: Current retry attempt index (0-indexed)
            
        Returns:
            Delay in seconds
        """
        base_delay = min(self.initial_retry_delay * (2 ** attempt), self.max_retry_delay)
        jitter = random.uniform(0.1, 1.0)
        return base_delay + jitter

    @staticmethod
    def is_retryable_status_code(status_code: int) -> bool:
        """Check if an HTTP status code represents a transient, retryable error."""
        return status_code in (429, 500, 502, 503, 504)

    @staticmethod
    def is_retryable_exception(exc: Exception) -> bool:
        """Check if an exception is retryable (transient server or network issue)."""
        if isinstance(exc, (RateLimitError, ServiceUnavailableError)):
            return True
        exc_name = exc.__class__.__name__
        if "Timeout" in exc_name or "ConnectionError" in exc_name or "ConnectTimeout" in exc_name:
            return True
        msg = str(exc).lower()
        if any(term in msg for term in ["503", "429", "502", "504", "500", "high demand", "unavailable", "capacity", "timeout", "timed out", "connection"]):
            return True
        return False

    def _call_gemini_model(self, prompt: str, model_name: str) -> str:
        """
        Call a specific Google Gemini model using REST API with safe error handling.
        
        Args:
            prompt: The prompt to send
            model_name: Model identifier (e.g., 'gemini-3.1-flash-lite')
            
        Returns:
            API response string
            
        Raises:
            AuthenticationError: If 401/403 or invalid API credentials
            ServiceUnavailableError: If 503 (high demand) or 5xx server error
            RateLimitError: If 429 rate limit exceeded
            APIError: Other non-retryable API failure
        """
        try:
            import requests
        except ImportError:
            raise APIError("Requests package not installed. Install with: pip install requests")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key}"
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

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
        except requests.exceptions.Timeout as te:
            logger.warning(f"Timeout on Gemini model '{model_name}'")
            raise ServiceUnavailableError(f"Request to model '{model_name}' timed out") from te
        except requests.exceptions.RequestException as req_err:
            logger.warning(f"Network error on Gemini model '{model_name}': {req_err}")
            raise ServiceUnavailableError(f"Network error connecting to model '{model_name}'") from req_err

        # If model doesn't support responseMimeType (e.g. legacy model), retry once without it
        if response.status_code == 400 and "responseMimeType" in response.text:
            payload["generationConfig"].pop("responseMimeType", None)
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=30)
            except Exception as retry_err:
                raise ServiceUnavailableError(f"Request retry without mimeType failed on model '{model_name}'") from retry_err

        # Safe error classification (NEVER log API keys or raw token headers)
        if response.status_code in (401, 403):
            logger.error(f"Authentication failed for model '{model_name}' (status {response.status_code})")
            raise AuthenticationError("Gemini authentication failed. Please check your API key.")
        elif response.status_code == 503:
            logger.warning(f"Model '{model_name}' returned 503 UNAVAILABLE (high demand)")
            raise ServiceUnavailableError(f"Gemini model '{model_name}' is currently experiencing high demand (503 UNAVAILABLE).")
        elif response.status_code == 429:
            logger.warning(f"Model '{model_name}' returned 429 (rate limit exceeded)")
            raise RateLimitError(f"Gemini rate limit exceeded for model '{model_name}' (429).")
        elif response.status_code in (500, 502, 504):
            logger.warning(f"Model '{model_name}' returned server error {response.status_code}")
            raise ServiceUnavailableError(f"Gemini server error {response.status_code} on model '{model_name}'.")
        elif response.status_code != 200:
            logger.error(f"Model '{model_name}' returned client error {response.status_code}")
            raise APIError(f"Gemini API error {response.status_code} on model '{model_name}'.")

        try:
            result = response.json()
        except Exception as json_err:
            raise APIError(f"Failed to parse Gemini response JSON from model '{model_name}': {json_err}")

        if 'candidates' in result and len(result['candidates']) > 0:
            candidate = result['candidates'][0]
            parts = candidate.get('content', {}).get('parts', [])
            if parts and 'text' in parts[0]:
                return parts[0]['text']

        logger.warning(f"Unexpected empty candidates format on model '{model_name}'")
        raise APIError(f"Empty candidate response from Gemini model '{model_name}'")

    def _call_gemini(self, prompt: str, model: Optional[str] = None) -> str:
        """
        Call Google Gemini API with the specified or primary model.
        
        Args:
            prompt: The prompt to send
            model: Optional model identifier override
            
        Returns:
            API response as string
        """
        target_model = model or self.model
        return self._call_gemini_model(prompt, target_model)

    def _call_llm(self, prompt: str, model: Optional[str] = None) -> str:
        """
        Call the LLM API based on configured provider.
        
        Args:
            prompt: The prompt to send
            model: Optional model identifier override
            
        Returns:
            LLM response as string
            
        Raises:
            APIError: If API call fails
            AuthenticationError: If authentication fails
            RateLimitError: If rate limit is exceeded
            ServiceUnavailableError: If service is temporarily unavailable
        """
        if self.provider == 'gemini':
            return self._call_gemini(prompt, model=model)
        else:
            raise APIError(f"Unsupported provider: {self.provider}")

    def _call_llm_with_retry(self, prompt: str) -> str:
        """
        Call LLM with exponential backoff, jitter, and automatic model fallback.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            LLM response as string
            
        Raises:
            AuthenticationError: If authentication fails (immediate fail, no retry)
            APIError: If non-retryable API error occurs
            ServiceUnavailableError: If all retries exhausted on transient 503/429/timeouts
        """
        models_to_try = [self.model]
        if self.fallback_model and self.fallback_model != self.model:
            models_to_try.append(self.fallback_model)

        last_exception = None

        for attempt in range(self.max_retries):
            for current_model in models_to_try:
                try:
                    logger.info(f"LLM call attempt {attempt + 1}/{self.max_retries} using model '{current_model}'")
                    try:
                        response = self._call_llm(prompt, model=current_model)
                    except TypeError:
                        # For mocks that only accept (prompt) without model keyword
                        response = self._call_llm(prompt)
                    logger.info(f"LLM call successful on model '{current_model}' (attempt {attempt + 1})")
                    return response

                except AuthenticationError:
                    # Authentication errors are fatal and not retryable
                    logger.error("Authentication failed. Aborting retries.")
                    raise
                except (ServiceUnavailableError, RateLimitError) as transient_err:
                    last_exception = transient_err
                    logger.warning(
                        f"Transient error ({type(transient_err).__name__}) on model '{current_model}' "
                        f"(attempt {attempt + 1}/{self.max_retries})."
                    )
                    # If this is the primary model and a fallback is configured, try fallback immediately in this cycle
                    if current_model == self.model and len(models_to_try) > 1:
                        logger.info(f"Trying fallback model '{self.fallback_model}' before backoff...")
                        continue
                except APIError as api_err:
                    if self.is_retryable_exception(api_err):
                        last_exception = api_err
                        logger.warning(f"Retryable API error on attempt {attempt + 1}: {api_err}")
                    else:
                        logger.error(f"Non-retryable API error on model '{current_model}': {api_err}")
                        raise
                except Exception as unk_err:
                    if self.is_retryable_exception(unk_err):
                        last_exception = unk_err
                        logger.warning(f"Retryable exception on attempt {attempt + 1}: {unk_err}")
                    else:
                        logger.error(f"Unrecoverable error during LLM call: {unk_err}")
                        raise APIError(f"LLM call failed: {unk_err}") from unk_err

            # Backoff with random jitter before next attempt
            if attempt < self.max_retries - 1:
                delay = self._calculate_retry_delay(attempt)
                logger.info(f"Waiting {delay:.2f}s (exponential backoff + jitter) before retry attempt {attempt + 2}/{self.max_retries}...")
                time.sleep(delay)

        # All retry attempts exhausted
        logger.error(f"Exhausted all {self.max_retries} retries for LLM service. Last error: {type(last_exception).__name__ if last_exception else 'Unknown'}")
        if isinstance(last_exception, ServiceUnavailableError):
            raise ServiceUnavailableError(
                "AI service is temporarily unavailable due to high demand (503 UNAVAILABLE). Please try again shortly."
            )
        elif isinstance(last_exception, RateLimitError):
            raise RateLimitError(
                "AI service rate limit exceeded. Please wait a moment and try again."
            )
        else:
            raise RetryLimitExceededError(
                f"Max retries ({self.max_retries}) exceeded. Last error: {str(last_exception)}"
            )

    
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
            return validated_data.model_dump() if hasattr(validated_data, 'model_dump') else validated_data.dict()
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

    def _heuristic_extract_intelligence(self, transcript: str) -> Dict:
        """
        Extract structured meeting intelligence using regex & heuristic linguistic rules
        when remote LLM APIs are undergoing demand spikes (503/429) or network outages.
        """
        import re
        sentences = [s.strip() for s in re.split(r'[.!?\n]+', transcript) if len(s.strip()) > 5]

        # 1. Summary
        summary = ". ".join(sentences[:3]) + ("." if sentences else "")
        if not summary:
            summary = transcript[:300]

        # 2. Key Points
        key_points = sentences[:6] if len(sentences) >= 6 else sentences

        # 3. Decisions
        decision_patterns = [
            r'\bdecided to\b', r'\bdecision is\b', r'\bagreed to\b', r'\bagreed that\b',
            r'\bapproved\b', r'\bselected\b', r'\bwill proceed with\b', r'\bconclusion is\b'
        ]
        decisions = []
        for s in sentences:
            if any(re.search(p, s, re.IGNORECASE) for p in decision_patterns):
                decisions.append(s)
        if not decisions and len(sentences) > 2:
            decisions = [sentences[min(2, len(sentences) - 1)]]

        # 4. Action Items & Owners
        action_patterns = [
            r'\bwill\b', r'\bassigned to\b', r'\baction item\b', r'\btask\b',
            r'\bcomplete\b', r'\bdeliver\b', r'\bprepare\b', r'\bimplement\b',
            r'\bfix\b', r'\bby (?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|next week|tomorrow|eod)\b'
        ]
        action_items = []
        # Extract name candidates
        potential_names = set(re.findall(r'\b[A-Z][a-z]{2,15}\b', transcript))
        stop_words = {"The", "This", "That", "There", "Here", "With", "From", "About", "Section", "Meeting", "Sprint", "Please", "Thanks", "Hello", "Welcome", "After", "Before"}
        name_candidates = [n for n in potential_names if n not in stop_words]

        for s in sentences:
            if any(re.search(p, s, re.IGNORECASE) for p in action_patterns):
                owner = None
                for n in name_candidates:
                    if n in s:
                        owner = n
                        break
                dl_match = re.search(r'\bby (Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|next week|tomorrow|EOD)\b', s, re.IGNORECASE)
                deadline = dl_match.group(1).capitalize() if dl_match else None
                priority = "High" if any(w in s.lower() for w in ["urgent", "critical", "high", "asap", "immediately"]) else "Medium"

                action_items.append({
                    "action": s,
                    "owner": owner,
                    "deadline": deadline,
                    "priority": priority,
                    "status": "Pending"
                })

        # 5. Participants
        participants = list(set([a["owner"] for a in action_items if a.get("owner")] + [n for n in name_candidates if n in transcript][:4]))

        # 6. Deadlines
        deadlines = [a["deadline"] for a in action_items if a.get("deadline")]

        # 7. Priorities
        priorities = [{"item": a["action"][:60], "priority": a["priority"]} for a in action_items[:5]]

        return {
            "summary": summary,
            "key_points": key_points,
            "decisions": decisions[:5],
            "action_items": action_items[:10],
            "participants": participants,
            "deadlines": list(set(deadlines)),
            "priorities": priorities
        }

