from datetime import UTC, datetime, timedelta
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.lifecycle import IncidentStatus, Severity


class DTO(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")


class LoginIn(DTO):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=256)


class UserOut(DTO):
    id: str
    email: str
    name: str
    role: str
    active: bool


class UserIn(DTO):
    email: str = Field(pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$", max_length=254)
    name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=12, max_length=128)
    role: Literal["Admin", "Analyst", "Viewer"]


class IntegrationIn(DTO):
    name: str = Field(min_length=1, max_length=100)
    synthetic: bool = True


class IntegrationOut(DTO):
    id: str
    name: str
    kind: str
    enabled: bool
    synthetic: bool
    created_at: datetime


class EventIn(DTO):
    external_id: str = Field(min_length=1, max_length=128)
    host: str = Field(min_length=1, max_length=253, pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_.:-]*$")
    service: str | None = Field(default=None, min_length=1, max_length=200)
    event_type: Literal["HOST", "SERVICE"]
    state: Severity
    output: str = Field(default="", max_length=8000)
    observed_at: datetime

    @field_validator("observed_at")
    @classmethod
    def aware_time(cls, value):
        if value.tzinfo is None:
            raise ValueError("Timezone is required")
        if value > datetime.now(UTC) + timedelta(minutes=5):
            raise ValueError("Event timestamp too far in the future")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def service_matches_type(self):
        if (self.event_type == "SERVICE") != (self.service is not None):
            raise ValueError("SERVICE requires service; HOST must omit service")
        return self


class EventOut(DTO):
    id: str
    external_id: str
    integration_id: str
    host_name: str
    service_name: str | None
    event_type: str
    state: str
    output: str
    observed_at: datetime
    created_at: datetime
    out_of_order: bool
    synthetic: bool


class IncidentOut(DTO):
    id: str
    title: str
    integration_id: str
    host_name: str
    service_name: str | None
    event_type: str
    severity: str
    status: str
    assignee_id: str | None
    created_at: datetime
    updated_at: datetime
    last_seen_at: datetime
    acknowledged_at: datetime | None
    resolved_at: datetime | None
    flapping: bool
    reopen_count: int
    synthetic: bool


class TransitionIn(DTO):
    status: IncidentStatus


class AssignmentIn(DTO):
    assignee_id: str | None


class CommentIn(DTO):
    body: str = Field(min_length=1, max_length=4000)

    @field_validator("body")
    @classmethod
    def not_blank(cls, value):
        if not value.strip():
            raise ValueError("Comment must not be blank")
        return value.strip()


class CommentOut(DTO):
    id: str
    incident_id: str
    user_id: str
    body: str
    created_at: datetime


class AuditOut(DTO):
    id: str
    actor_id: str | None
    action: str
    entity_id: str | None
    details: dict
    correlation_id: str
    created_at: datetime
