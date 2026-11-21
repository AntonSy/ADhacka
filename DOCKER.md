# Docker: запуск и деплой

## Локально

    cp .env.example .env
    docker compose up --build
    # сайт: http://localhost:3000, Swagger: http://localhost:3000/docs

## Деплой на PaaS (git push)

1. Режим «свой Dockerfile», корень репозитория, порт 3000.
2. Постоянный том или каталог на `/data`: там хранится SQLite. Без тома база сбрасывается при пересоздании контейнера.
3. Переменные из `.env.example` задайте в настройках платформы, не в git.

## Заметки

- Контейнер работает не от root (пользователь `app`, UID 10001).
- `start.sh` должен иметь окончания строк LF (закреплено в `.gitattributes`).
- `HEALTHCHECK` обращается к `/api/v1/health`.
