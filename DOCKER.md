# Docker: запуск и деплой

Эти файлы кладутся в корень репозитория рядом с каталогами `backend/` и `frontend/`.

## Локально

    cp .env.example .env
    docker compose up --build
    # сайт: http://localhost:3000, Swagger: http://localhost:3000/docs

## Загрузка в git

    git init
    git add .
    git commit -m "Analyst Days: проверка аннотации"
    git branch -M main
    git remote add origin <URL репозитория>
    git push -u origin main

## Деплой на PaaS (git push)

1. Платформа: режим «свой Dockerfile», корень репозитория.
2. Порт приложения: 3000 (платформа может передать свой через переменную `PORT`).
3. Постоянный том или каталог на `/data`: там хранится SQLite. Без тома база сбрасывается при пересоздании контейнера.
4. Переменные из `.env.example` задайте в настройках платформы, не в git.

## Заметки

- Контейнер работает не от root (пользователь `app`). Если том смонтирован с правами root, выдайте права на запись пользователю с UID 10001.
- `start.sh` должен иметь окончания строк LF: это закреплено в `.gitattributes`.
- `HEALTHCHECK` обращается к `/api/v1/health`.
