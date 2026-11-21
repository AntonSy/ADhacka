# Запуск и деплой

## Локально

    cp .env.example .env
    docker compose up --build
    # сайт: http://localhost:3000, Swagger: http://localhost:3000/docs

Внутри контейнера приложение слушает порт 8080 (так требует RelaxDev), наружу он проброшен на 3000.

## Деплой на RelaxDev (https://adhacka.relaxdev.ru)

1. «Добавить проект» → репозиторий `AntonSy/ADhacka`, ветка `main`, имя проекта `adhacka`
   (системный адрес строится из имени: `adhacka.relaxdev.ru`). Папка (rootDir) — корень репозитория.
2. Тип сборки: Docker (не автоопределение). Иначе платформа соберёт только Next.js,
   FastAPI не запустится, и `/api/v1/health` вернёт 404.
3. Переменные добавлять не нужно: всё имеет значения по умолчанию. Необязательные:
   THRESHOLD_HIGH, THRESHOLD_MEDIUM, RATE_LIMIT_PER_HOUR, LLM_BASE_URL, LLM_API_KEY, LLM_MODEL.
4. «Деплой». После сборки проверьте `/api/v1/health` и `/docs`.

## Заметки

- Трафик приходит на порт 8080 (`PORT`). Next.js слушает его на 0.0.0.0, FastAPI работает внутри на 127.0.0.1:8000.
- `next.config.js` читает `process.env['BACKEND_URL']`: так платформа не подставляет заглушку.
- SQLite лежит в `/data/app.db`. Если у проекта нет постоянного тома, база пересоздаётся при каждом деплое:
  архив докладов загрузится заново из `talks.json`, а заявки и оценки пропадут.
- Контейнер работает не от root (пользователь `app`, UID 10001).
