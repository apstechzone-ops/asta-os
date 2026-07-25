import uuid
from datetime import datetime

from pydantic import BaseModel


class TaskCreate(BaseModel):
    title: str
    description: str = ""
    project_id: uuid.UUID | None = None
    priority: str = "normal"
    due_date: datetime | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None  # pending|in_progress|done|cancelled
    priority: str | None = None
    due_date: datetime | None = None


class TaskOut(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    status: str
    priority: str
    due_date: datetime | None
    project_id: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}
