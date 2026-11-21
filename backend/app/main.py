import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import config, recommend
from .db import Base, SessionLocal, engine, get_db
from .models import (Application, ArchiveTalk, CheckFeedback, Conference,
                     SimilarityCheck, SimilarityMatch)
from .schemas import (ApplicationIn, ApplicationOut, CheckCreate, CheckOut, ConferenceOut,
                      ErrorOut, FeedbackIn, MatchOut, TalkPage)
from .seed import seed_if_empty
from .similarity import SimilarityIndex, text_hash


class ApiError(Exception):
    def __init__(self, status: int, code: str, **extra):
        self.status, self.code, self.extra = status, code, extra


def build_index(db: Session) -> SimilarityIndex:
    rows = db.execute(select(ArchiveTalk.id, ArchiveTalk.title, ArchiveTalk.annotation)).all()
    return SimilarityIndex([(r.id, r.title, r.annotation) for r in rows])


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed_if_empty(db)
        app.state.index = build_index(db)
    yield


app = FastAPI(
    title="Analyst Days: проверка аннотации доклада",
    description="API проверки аннотации на пересечения с ранее принятыми докладами конференции Analyst Days.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(ApiError)
async def _api_error(_: Request, exc: ApiError):
    return JSONResponse(status_code=exc.status, content={"error": exc.code, **exc.extra})


@app.exception_handler(RequestValidationError)
async def _validation(_: Request, exc: RequestValidationError):
    loc = exc.errors()[0]["loc"] if exc.errors() else ()
    field = str(loc[-1]) if loc else None
    return JSONResponse(status_code=400, content={"error": "VALIDATION", "field": field})


api = APIRouter(prefix="/api/v1")
ERR = {400: {"model": ErrorOut}, 404: {"model": ErrorOut}, 409: {"model": ErrorOut}, 429: {"model": ErrorOut}}


def _check_out(check: SimilarityCheck, cached: bool = False) -> CheckOut:
    matches = []
    for m in check.matches:
        t = m.talk
        matches.append(MatchOut(
            rank=m.rank, talk_id=t.id, title=t.title, conference_number=t.conference_number,
            year=t.conference.year, author=t.author_name, company=t.company, city=t.city, format=t.format,
            annotation=t.annotation, score=round(m.final_score, 3), url=t.source_url,
            matched_aspects=[a for a in m.matched_aspects.split(",") if a],
        ))
    return CheckOut(
        id=check.id, status=check.status, level=check.level, top_score=round(check.top_score, 3),
        matches=matches, recommendation=check.recommendation, recommendation_source=check.recommendation_source,
        annotation_hash=check.annotation_hash, cached=cached, created_at=check.created_at,
    )


@api.post("/similarity-checks", response_model=CheckOut, responses=ERR, tags=["Проверка"],
          summary="Создать проверку аннотации и получить результат")
def create_check(body: CheckCreate, request: Request, db: Session = Depends(get_db)):
    h = text_hash(body.annotation)
    cached = db.scalars(
        select(SimilarityCheck).where(
            SimilarityCheck.annotation_hash == h,
            SimilarityCheck.model_version == config.MODEL_VERSION,
            SimilarityCheck.thresholds_version == config.THRESHOLDS_VERSION,
        ).order_by(SimilarityCheck.created_at.desc())
    ).first()
    if cached:
        return _check_out(cached, cached=True)

    owner = body.session_id or f"ip:{request.client.host if request.client else 'unknown'}"
    since = datetime.now(timezone.utc) - timedelta(hours=1)
    used = db.scalar(select(func.count()).select_from(SimilarityCheck).where(
        SimilarityCheck.session_id == owner, SimilarityCheck.created_at >= since)) or 0
    if used >= config.RATE_LIMIT_PER_HOUR:
        raise ApiError(429, "RATE_LIMIT", retry_after=600)

    t0 = time.perf_counter()
    res = request.app.state.index.search(body.annotation, config.THRESHOLD_HIGH, config.THRESHOLD_MEDIUM)
    talks = {t.id: t for t in db.scalars(select(ArchiveTalk).where(ArchiveTalk.id.in_([m.talk_id for m in res.matches])))}

    rec_text = rec_src = None
    if res.level != "LOW" and res.matches:
        top_talk = talks[res.matches[0].talk_id]
        rec_text, rec_src = recommend.build(body.annotation, {
            "title": top_talk.title, "conference_number": top_talk.conference_number,
            "year": top_talk.conference.year, "aspects": res.matches[0].aspects})

    check = SimilarityCheck(
        session_id=owner, annotation_hash=h, annotation_text=body.annotation, title=body.title,
        level=res.level, top_score=res.top_score, model_version=config.MODEL_VERSION,
        thresholds_version=config.THRESHOLDS_VERSION, status="DONE",
        recommendation=rec_text, recommendation_source=rec_src,
    )
    for i, m in enumerate(res.matches, 1):
        check.matches.append(SimilarityMatch(
            talk_id=m.talk_id, rank=i, final_score=m.score, matched_aspects=",".join(m.aspects)))
    check.duration_ms = int((time.perf_counter() - t0) * 1000)
    db.add(check)
    db.commit()
    db.refresh(check)
    return _check_out(check)


@api.get("/similarity-checks/{check_id}", response_model=CheckOut, responses=ERR, tags=["Проверка"],
         summary="Получить результат проверки")
def get_check(check_id: str, db: Session = Depends(get_db)):
    check = db.get(SimilarityCheck, check_id)
    if not check:
        raise ApiError(404, "NOT_FOUND")
    return _check_out(check)


@api.post("/similarity-checks/{check_id}/feedback", responses=ERR, tags=["Проверка"],
          summary="Оценить полезность проверки")
def feedback(check_id: str, body: FeedbackIn, db: Session = Depends(get_db)):
    if not db.get(SimilarityCheck, check_id):
        raise ApiError(404, "NOT_FOUND")
    fb = db.get(CheckFeedback, check_id)
    updated = fb is not None
    if fb:
        fb.useful, fb.comment = body.useful, body.comment
    else:
        db.add(CheckFeedback(check_id=check_id, useful=body.useful, comment=body.comment))
    db.commit()
    return {"ok": True, "updated": updated}


@api.post("/applications", response_model=ApplicationOut, status_code=201, responses=ERR, tags=["Заявки"],
          summary="Подать заявку (с проверкой или без)")
def create_application(body: ApplicationIn, db: Session = Depends(get_db)):
    state, level, check_id = "not_checked", None, None
    if body.check_id:
        check = db.get(SimilarityCheck, body.check_id)
        if not check:
            raise ApiError(404, "NOT_FOUND")
        if check.annotation_hash != text_hash(body.annotation):
            raise ApiError(409, "CHECK_OUTDATED")
        state, level, check_id = "checked", check.level, check.id
    app_row = Application(
        session_id=body.session_id, author_email=body.email, title=body.title, annotation=body.annotation,
        last_check_id=check_id, check_state=state, level=level)
    db.add(app_row)
    db.commit()
    db.refresh(app_row)
    return app_row


@api.get("/applications", response_model=list[ApplicationOut], tags=["Заявки"],
         summary="Заявки текущей сессии")
def list_applications(session_id: str = Query(min_length=1, max_length=64), db: Session = Depends(get_db)):
    return db.scalars(select(Application).where(Application.session_id == session_id)
                      .order_by(Application.created_at.desc())).all()


@api.get("/conferences", response_model=list[ConferenceOut], tags=["Архив"], summary="Конференции в архиве")
def conferences(db: Session = Depends(get_db)):
    counts = dict(db.execute(select(ArchiveTalk.conference_number, func.count()).group_by(ArchiveTalk.conference_number)).all())
    return [ConferenceOut(number=c.number, year=c.year, url=c.url, talks_count=counts.get(c.number, 0))
            for c in db.scalars(select(Conference).order_by(Conference.number.desc()))]


@api.get("/archive/talks", response_model=TalkPage, tags=["Архив"], summary="Доклады архива")
def archive_talks(conference: int | None = None, q: str | None = None,
                  limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0),
                  db: Session = Depends(get_db)):
    stmt = select(ArchiveTalk)
    if conference is not None:
        stmt = stmt.where(ArchiveTalk.conference_number == conference)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(func.lower(ArchiveTalk.title + " " + ArchiveTalk.author_name + " " +
                                     func.coalesce(ArchiveTalk.company, "")).like(like))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(stmt.order_by(ArchiveTalk.conference_number.desc(), ArchiveTalk.id).limit(limit).offset(offset)).all()
    return TalkPage(total=total, items=items)


@api.get("/health", tags=["Сервис"], summary="Проверка работоспособности")
def health():
    return {"status": "ok"}


app.include_router(api)
