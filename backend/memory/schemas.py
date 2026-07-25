from pydantic import BaseModel, Field


class ShortTermEntry(BaseModel):
    session_id: str
    role: str = Field(pattern="^(user|assistant|tool|system)$")
    content: str
    user_id: str | None = None


class LongTermEntry(BaseModel):
    user_id: str
    content: str
    metadata: dict = Field(default_factory=dict)


class VectorSearchQuery(BaseModel):
    query: str
    top_k: int = 5
    filters: dict | None = None


class VectorSearchResult(BaseModel):
    id: str
    content: str
    metadata: dict
    score: float


class StructuredSearchQuery(BaseModel):
    table: str
    filters: dict = Field(default_factory=dict)
    limit: int = 20
