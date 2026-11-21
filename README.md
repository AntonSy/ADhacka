# Analyst Days: проверка аннотации доклада

Сайт сверяет аннотацию (до 500 символов) с ранее принятыми докладами Analyst Days 19-23 и показывает уровень
пересечения (LOW / MEDIUM / HIGH), похожие доклады и рекомендации по доработке темы.

| Слой | Технологии | Каталог |
|---|---|---|
| Представление | Next.js 14, Tailwind CSS, компоненты в стиле shadcn/ui | `frontend/` |
| Логика | FastAPI, Swagger на `/docs` | `backend/app/` |
| Данные | SQLite + SQLAlchemy 2 | файл `app.db` в `/data` |

Поток запроса: браузер → Next.js → `/api/*` (rewrite) → FastAPI → SQLAlchemy → SQLite → обратно.

## Запуск

    docker compose up --build        # http://localhost:3000, Swagger: http://localhost:3000/docs

Без Docker: `cd backend && pip install -r requirements.txt && uvicorn app.main:app --port 8000`
и `cd frontend && npm install && npm run dev`. Тесты API: `cd backend && pytest`. Подробности: `DOCKER.md`.

## Данные

При первом запуске БД заполняется из `backend/data/talks.json` (353 принятых доклада Analyst Days 19-23).
Полная аннотация есть только у одного доклада, остальные сравниваются по названию.
Чтобы добавить аннотации, заполните поле `annotation` в `talks.json` и пересоздайте БД.

## API

Swagger: `/docs`, схема: `/openapi.json`. Для APItizer: `python scripts/export_openapi.py > openapi.json`.

| Метод | Путь | Назначение |
|---|---|---|
| POST | `/api/v1/similarity-checks` | создать проверку и получить результат |
| GET | `/api/v1/similarity-checks/{id}` | получить результат |
| POST | `/api/v1/similarity-checks/{id}/feedback` | оценка полезности |
| POST | `/api/v1/applications` | подать заявку (с `check_id` или без) |
| GET | `/api/v1/applications?session_id=` | заявки сессии |
| GET | `/api/v1/conferences`, `/api/v1/archive/talks` | данные архива |
| GET | `/api/v1/health` | проверка работоспособности |

Ошибки: 400 `VALIDATION`, 404 `NOT_FOUND`, 409 `CHECK_OUTDATED`, 429 `RATE_LIMIT`.
