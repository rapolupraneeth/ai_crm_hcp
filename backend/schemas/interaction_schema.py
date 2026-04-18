from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Conversation session id")
    message: str = Field(..., min_length=1)


class UploadedFileInfo(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_path: str
    file_type: str  # 'materials' or 'samples'
    mime_type: str
    file_size: int
    uploaded_at: datetime


class HCPPayload(BaseModel):
    external_id: str | None = None
    full_name: str | None = None
    specialty: str | None = None
    organization: str | None = None
    city: str | None = None


class InteractionPayload(BaseModel):
    interaction_id: int | None = None
    interaction_type: str | None = None
    channel: str | None = None
    sentiment: str | None = None
    summary: str | None = None
    key_points: list[str] = Field(default_factory=list)
    follow_up_required: bool | None = None
    interaction_date: datetime | None = None
    date: str | None = None  # YYYY-MM-DD format
    time: str | None = None  # HH:MM format
    attendees: str | None = None  # JSON or comma-separated
    materials: str | None = None
    samples: str | None = None
    outcomes: str | None = None
    uploaded_files: list[UploadedFileInfo] = Field(default_factory=list)


class FollowUpPayload(BaseModel):
    suggestion: str | None = None
    due_days: int | None = None


class StructuredFormData(BaseModel):
    hcp: HCPPayload = Field(default_factory=HCPPayload)
    interaction: InteractionPayload = Field(default_factory=InteractionPayload)
    follow_up: FollowUpPayload = Field(default_factory=FollowUpPayload)
    compliance_flags: list[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    action: Literal["update_form"] = "update_form"
    external_id: str | None = None
    full_name: str | None = None
    specialty: str | None = None
    organization: str | None = None
    city: str | None = None


class InteractionPayload(BaseModel):
    interaction_id: int | None = None
    interaction_type: str | None = None
    channel: str | None = None
    sentiment: str | None = None
    summary: str | None = None
    key_points: list[str] = Field(default_factory=list)
    follow_up_required: bool | None = None
    interaction_date: datetime | None = None
    date: str | None = None  # YYYY-MM-DD format
    time: str | None = None  # HH:MM format
    attendees: str | None = None  # JSON or comma-separated
    materials: str | None = None
    samples: str | None = None
    outcomes: str | None = None


class FollowUpPayload(BaseModel):
    suggestion: str | None = None
    due_days: int | None = None


class StructuredFormData(BaseModel):
    hcp: HCPPayload = Field(default_factory=HCPPayload)
    interaction: InteractionPayload = Field(default_factory=InteractionPayload)
    follow_up: FollowUpPayload = Field(default_factory=FollowUpPayload)
    compliance_flags: list[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    action: Literal["update_form"] = "update_form"
    data: StructuredFormData
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class InteractionOut(BaseModel):
    id: int
    hcp_id: int
    interaction_type: str | None
    channel: str | None
    sentiment: str | None
    summary: str | None
    key_points: str | None
    follow_up_required: bool
    interaction_date: datetime

    class Config:
        from_attributes = True

class IntentResult(BaseModel):
    intent: Literal[
        "log_interaction",
        "edit_interaction",
        "suggest_follow_up",
        "retrieve_history",
        "emotional_support",
        "abusive",
        "out_of_scope"
    ]
    reason: str | None = None


class ExtractionResult(BaseModel):
    hcp: dict[str, Any] = Field(default_factory=dict)
    interaction: dict[str, Any] = Field(default_factory=dict)
    follow_up: dict[str, Any] = Field(default_factory=dict)
