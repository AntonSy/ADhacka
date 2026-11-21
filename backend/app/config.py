import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _default_db() -> str:
    data_dir = Path(os.getenv("DATA_DIR", "/data"))
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        if os.access(data_dir, os.W_OK):
            return str(data_dir / "app.db")
    except OSError:
        pass
    return str(BASE_DIR / "app.db")


DB_PATH = os.getenv("DB_PATH") or _default_db()
DATABASE_URL = f"sqlite:///{DB_PATH}"
SEED_FILE = os.getenv("SEED_FILE", str(BASE_DIR / "data" / "talks.json"))

THRESHOLD_HIGH = float(os.getenv("THRESHOLD_HIGH", "0.50"))
THRESHOLD_MEDIUM = float(os.getenv("THRESHOLD_MEDIUM", "0.25"))
THRESHOLDS_VERSION = os.getenv("THRESHOLDS_VERSION", "t1")
MODEL_VERSION = "tfidf-concepts-1"

RATE_LIMIT_PER_HOUR = int(os.getenv("RATE_LIMIT_PER_HOUR", "10"))
MAX_ANNOTATION = 500

# Необязательная интеграция с LLM (OpenAI-совместимый API). Без неё рекомендации формируются по шаблону.
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "")
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "8"))
