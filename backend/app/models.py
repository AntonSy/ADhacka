import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def _id() -> str:
    return uuid.uuid4().hex


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Conference(Base):
    """Справочник конференций Analyst Days."""
    __tablename__ = "conference"
    number: Mapped[int] = mapped_column(Integer, primary_key=True)
    year: Mapped[int] = mapped_column(Integer)
    url: Mapped[str | None] = mapped_column(String(300))
    talks: Mapped[list["ArchiveTalk"]] = relationship(back_populates="conference")


class ArchiveTalk(Base):
    """Принятые доклады архива: эталонный корпус для сравнения."""
    __tablename__ = "archive_talk"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    conference_number: Mapped[int] = mapped_column(ForeignKey("conference.number"), index=True)
    title: Mapped[str] = mapped_column(String(500))
    annotation: Mapped[str | None] = mapped_column(Text)
    author_name: Mapped[str] = mapped_column(String(200))
    company: Mapped[str | None] = mapped_column(String(300))
    city: Mapped[str | None] = mapped_column(String(100))
    format: Mapped[str | None] = mapped_column(String(50))
    source_url: Mapped[str | None] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(20), default="accepted")
    conference: Mapped[Conference] = relationship(back_populates="talks")


class Application(Base):
    """Заявка автора со ссылкой на последнюю проверку."""
    __tablename__ = "application"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    session_id: Mapped[str | None] = mapped_column(String(64), index=True)
    author_email: Mapped[str] = mapped_column(String(200))
    title: Mapped[str] = mapped_column(String(500))
    annotation: Mapped[str] = mapped_column(Text)
    last_check_id: Mapped[str | None] = mapped_column(ForeignKey("similarity_check.id"))
    check_state: Mapped[str] = mapped_column(String(20))  # checked | not_checked
    level: Mapped[str | None] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class SimilarityCheck(Base):
    """Факт проверки: кэш, воспроизводимость, аналитика."""
    __tablename__ = "similarity_check"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    session_id: Mapped[str | None] = mapped_column(String(64), index=True)
    annotation_hash: Mapped[str] = mapped_column(String(16), index=True)
    annotation_text: Mapped[str] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(String(500))
    level: Mapped[str] = mapped_column(String(10))
    top_score: Mapped[float] = mapped_column(Float)
    model_version: Mapped[str] = mapped_column(String(50))
    thresholds_version: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(10), default="DONE")
    recommendation: Mapped[str | None] = mapped_column(Text)
    recommendation_source: Mapped[str | None] = mapped_column(String(20))
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)
    matches: Mapped[list["SimilarityMatch"]] = relationship(
        back_populates="check", cascade="all, delete-orphan", order_by="SimilarityMatch.rank")


class SimilarityMatch(Base):
    """Найденные совпадения проверки."""
    __tablename__ = "similarity_match"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    check_id: Mapped[str] = mapped_column(ForeignKey("similarity_check.id", ondelete="CASCADE"), index=True)
    talk_id: Mapped[str] = mapped_column(ForeignKey("archive_talk.id"))
    rank: Mapped[int] = mapped_column(Integer)
    final_score: Mapped[float] = mapped_column(Float)
    matched_aspects: Mapped[str] = mapped_column(Text, default="")
    check: Mapped[SimilarityCheck] = relationship(back_populates="matches")
    talk: Mapped[ArchiveTalk] = relationship()


class CheckFeedback(Base):
    """Оценка полезности проверки."""
    __tablename__ = "check_feedback"
    check_id: Mapped[str] = mapped_column(ForeignKey("similarity_check.id", ondelete="CASCADE"), primary_key=True)
    useful: Mapped[bool] = mapped_column(Boolean)
    comment: Mapped[str | None] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
