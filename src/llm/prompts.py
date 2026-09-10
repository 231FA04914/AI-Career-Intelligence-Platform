"""
Prompt templates for LLM processing.
"""


class PromptTemplates:
    """Reusable prompt templates for LLM processing."""
    
    @staticmethod
    def get_career_intelligence_prompt() -> str:
        """
        Get the main prompt for career/interview intelligence extraction.
        
        This prompt instructs the LLM to analyze a transcript and extract
        structured meeting/interview intelligence without hallucinating
        information not present in the transcript.
        """
        return """You are an AI assistant that analyzes career and interview transcripts to extract structured intelligence. 

Your task is to analyze the provided transcript and extract the following information:

1. SUMMARY: A concise summary of the transcript (2-3 sentences maximum).

2. KEY POINTS: Important topics discussed (list as bullet points).

3. DECISIONS: Decisions explicitly made or stated in the transcript (list as bullet points).

4. ACTION ITEMS: Tasks or follow-up activities identified in the transcript. For each action item, include:
   - action: The task to be completed
   - owner: Person responsible (if mentioned, otherwise null)
   - deadline: Due date (if mentioned, otherwise null)
   - priority: High/Medium/Low (if mentioned, otherwise null)

5. PARTICIPANTS: People explicitly mentioned as participants or responsible persons (list as bullet points).

6. DEADLINES: Deadlines or dates explicitly mentioned (list as bullet points).

7. PRIORITIES: Items with explicit priority levels mentioned. For each, include:
   - item: The item or topic
   - priority: High/Medium/Low

IMPORTANT ANTI-HALLUCINATION RULES:
- DO NOT invent participants, deadlines, decisions, action items, priorities, or facts
- If information is not present in the transcript, return an empty list [] or null
- DO NOT guess or infer missing information
- Only extract information that is EXPLICITLY stated in the transcript
- If the transcript mentions skills or technologies, extract them but do not add additional skills not mentioned

The transcript is from a career/interview context. Extract useful information without inventing facts.

Return your response as valid JSON with these fields: summary (string), key_points (array of strings), decisions (array of strings), action_items (array of objects with action, owner, deadline, priority fields), participants (array of strings), deadlines (array of strings), priorities (array of objects with item and priority fields).

Do not include any explanatory text outside the JSON. Return ONLY valid JSON.

TRANSCRIPT:
{transcript}"""
    
    @staticmethod
    def get_chunk_processing_prompt(chunk: str) -> str:
        """
        Get prompt for processing a transcript chunk.
        
        Args:
            chunk: The transcript chunk to process
            
        Returns:
            Formatted prompt for chunk processing
        """
        return f"""Analyze this portion of a career/interview transcript and extract the same structured information as the main prompt.

TRANSCRIPT CHUNK:
{chunk}

Return valid JSON following the same structure as the main prompt."""

    @staticmethod
    def get_action_item_extraction_prompt() -> str:
        """
        Get prompt specialized for high-precision action item extraction.
        
        Extracts tasks, assigned participants, deadlines, priorities, and statuses.
        """
        return """You are an AI assistant specialized in meeting action-item extraction and task analysis.

Your task is to thoroughly analyze the provided transcript and extract all action items, tasks, follow-ups, and commitments made by participants.

For each action item, extract the following attributes:
1. action: The clear description of the action or task to be completed.
2. owner: The person/participant explicitly assigned or responsible for this task. If not mentioned, return null.
3. deadline: Explicit due date, target day, or timeline mentioned (e.g. "Friday", "End of Sprint", "Next Monday"). If not mentioned, return null.
4. priority: Priority level if explicitly stated or clearly indicated (High, Medium, Low). If not mentioned, return null.
5. status: Current status of the task based on discussion ("Pending", "In Progress", "Completed", "Blocked"). Default to "Pending" if newly assigned.

ANTI-HALLUCINATION RULES:
- Only extract tasks explicitly stated or agreed upon in the transcript.
- Do NOT invent participants, deadlines, or priorities.
- If no action items are present, return an empty array for action_items: [].

Return your response as a valid JSON object with a single key "action_items" containing an array of objects with the fields: "action", "owner", "deadline", "priority", "status".

Example JSON format:
{{
  "action_items": [
    {{
      "action": "Complete API integration",
      "owner": "Ravi",
      "deadline": "Friday",
      "priority": "High",
      "status": "Pending"
    }}
  ]
}}

Return ONLY the valid JSON object. Do not include explanatory text outside the JSON.

TRANSCRIPT:
{transcript}"""

