import json
from pathlib import Path

from sqlalchemy.orm import Session

from . import config
from .models import ArchiveTalk, Conference


def seed_if_empty(db: Session) -> int:
    if db.query(Conference).first():
        return 0
    path = Path(config.SEED_FILE)
    if not path.exists():
        return 0
    rows = json.loads(path.read_text(encoding="utf-8"))
    confs = {}
    for r in rows:
        n = r["conference_number"]
        if n not in confs:
            confs[n] = Conference(number=n, year=r["year"], url=r.get("url"))
            db.add(confs[n])
    db.flush()
    for r in rows:
        db.add(ArchiveTalk(
            id=r["id"], conference_number=r["conference_number"], title=r["title"], annotation=r.get("annotation"),
            author_name=r["author"], company=r.get("company"), city=r.get("city"), format=r.get("format"),
            source_url=r.get("url"), status="accepted",
        ))
    db.commit()
    return len(rows)
