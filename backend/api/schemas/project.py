import uuid
from datetime import datetime

from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str
    description: str = ""


class ProjectOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
