"""
Pydantic schemas for LLM input/output validation.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, validator


class ActionItem(BaseModel):
    """Schema for an action item."""
    action: str = Field(..., description="The action or task to be completed")
    owner: Optional[str] = Field(None, description="Person responsible for the action")
    deadline: Optional[str] = Field(None, description="Deadline or due date")
    priority: Optional[str] = Field(None, description="Priority level: High, Medium, or Low")
    status: Optional[str] = Field("Pending", description="Status of the task: Pending, In Progress, Completed, Blocked")
    
    @validator('priority', pre=True)
    def validate_priority(cls, v):
        """Validate and normalize priority value."""
        if not v or v in ["null", "None", ""]:
            return None
        v_str = str(v).strip().capitalize()
        if v_str in ['High', 'Medium', 'Low']:
            return v_str
        if 'high' in str(v).lower():
            return 'High'
        if 'med' in str(v).lower():
            return 'Medium'
        if 'low' in str(v).lower():
            return 'Low'
        return None

    @validator('status', pre=True)
    def validate_status(cls, v):
        """Validate and normalize status value."""
        if not v or v in ["null", "None", ""]:
            return "Pending"
        v_str = str(v).strip().title()
        if v_str in ['Pending', 'In Progress', 'Completed', 'Blocked']:
            return v_str
        if 'prog' in v_str.lower():
            return 'In Progress'
        if 'comp' in v_str.lower() or 'done' in v_str.lower():
            return 'Completed'
        if 'block' in v_str.lower():
            return 'Blocked'
        return "Pending"


class PriorityItem(BaseModel):
    """Schema for a prioritized item."""
    item: str = Field(..., description="The item or topic")
    priority: str = Field("Medium", description="Priority level: High, Medium, or Low")
    
    @validator('priority', pre=True)
    def validate_priority(cls, v):
        """Validate and normalize priority value."""
        if not v or v in ["null", "None", ""]:
            return "Medium"
        v_str = str(v).strip().capitalize()
        if v_str in ['High', 'Medium', 'Low']:
            return v_str
        if 'high' in str(v).lower():
            return 'High'
        if 'med' in str(v).lower():
            return 'Medium'
        if 'low' in str(v).lower():
            return 'Low'
        return "Medium"


class MeetingIntelligence(BaseModel):
    """Schema for structured meeting/interview intelligence."""
    summary: str = Field(..., description="Concise summary of the transcript")
    key_points: List[str] = Field(default_factory=list, description="Important topics discussed")
    decisions: List[str] = Field(default_factory=list, description="Decisions explicitly made or stated")
    action_items: List[ActionItem] = Field(default_factory=list, description="Tasks or follow-up activities")
    participants: List[str] = Field(default_factory=list, description="People mentioned as participants")
    deadlines: List[str] = Field(default_factory=list, description="Deadlines or dates mentioned")
    priorities: List[PriorityItem] = Field(default_factory=list, description="Prioritized items")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "summary": "Candidate is a final-year Computer Science student interested in backend development.",
                "key_points": [
                    "Final-year Computer Science student",
                    "Backend development interest",
                    "Java, SQL and Spring Boot experience"
                ],
                "decisions": [
                    "Candidate will focus on backend development"
                ],
                "action_items": [
                    {
                        "action": "Practice coding questions",
                        "owner": "Candidate",
                        "deadline": "Friday",
                        "priority": "High"
                    }
                ],
                "participants": [
                    "Rahul",
                    "Mentor"
                ],
                "deadlines": [
                    "Friday"
                ],
                "priorities": [
                    {
                        "item": "Practice coding questions",
                        "priority": "High"
                    }
                ]
            }
        }
