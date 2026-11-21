"""Выгрузка OpenAPI-контракта для импорта в APItizer: python scripts/export_openapi.py > openapi.json"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
os.environ.setdefault("DB_PATH", "/tmp/export.db")
from app.main import app  # noqa: E402

print(json.dumps(app.openapi(), ensure_ascii=False, indent=2))
