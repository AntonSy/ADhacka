# syntax=docker/dockerfile:1
# Один образ: Next.js (слушает $PORT, на RelaxDev это 8080) + FastAPI (127.0.0.1:8000, снаружи недоступен).

FROM node:20-slim AS web
WORKDIR /web
COPY frontend/package.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    NODE_ENV=production \
    DATA_DIR=/data \
    PORT=8080
WORKDIR /srv

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY --from=web /usr/local/bin/node /usr/local/bin/node
COPY backend/ backend/
COPY --from=web /web/.next/standalone ./frontend
COPY --from=web /web/.next/static ./frontend/.next/static
COPY --from=web /web/public ./frontend/public
COPY start.sh ./start.sh

RUN useradd --create-home --uid 10001 app \
    && mkdir -p /data \
    && chown -R app:app /data /srv \
    && chmod +x /srv/start.sh
USER app

VOLUME ["/data"]
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD python -c "import os,urllib.request as u; u.urlopen('http://127.0.0.1:%s/api/v1/health' % os.environ.get('PORT','8080'), timeout=4)" || exit 1

CMD ["bash", "/srv/start.sh"]
