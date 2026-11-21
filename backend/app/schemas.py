from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .config import MAX_ANNOTATION


class CheckCreate(BaseModel):
    annotation: str = Field(min_length=1, max_length=MAX_ANNOTATION, description="Аннотация доклада, 1-500 символов")
    title: str | None = Field(default=None, max_length=500)
    session_id: str | None = Field(default=None, max_length=64)


class MatchOut(BaseModel):
    rank: int
    talk_id: str
    title: str
    conference_number: int
    year: int
    author: str
    company: str | None = None
    city: str | None = None
    format: str | None = None
    annotation: str | None = None
    score: float
    url: str | None = None
    matched_aspects: list[str] = []


class CheckOut(BaseModel):
    id: str
    status: str
    level: str = Field(description="LOW | MEDIUM | HIGH")
    top_score: float
    matches: list[MatchOut]
    recommendation: str | None = None
    recommendation_source: str | None = None
    annotation_hash: str
    cached: bool = False
    created_at: datetime


class FeedbackIn(BaseModel):
    useful: bool
    comment: str | None = Field(default=None, max_length=1000)


class ApplicationIn(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    annotation: str = Field(min_length=1, max_length=MAX_ANNOTATION)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=200)
    check_id: str | None = None
    session_id: str | None = Field(default=None, max_length=64)


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    annotation: str
    author_email: str
    check_state: str
    last_check_id: str | None = None
    level: str | None = None
    created_at: datetime


class TalkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    conference_number: int
    title: str
    annotation: str | None = None
    author_name: str
    company: str | None = None
    city: str | None = None
    format: str | None = None
    source_url: str | None = None


class TalkPage(BaseModel):
    total: int
    items: list[TalkOut]


class ConferenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    number: int
    year: int
    url: str | None = None
    talks_count: int = 0


class ErrorOut(BaseModel):
    error: str
    field: str | None = None
    retry_after: int | None = None
