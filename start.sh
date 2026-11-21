#!/bin/bash
set -eu
cd /srv/backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 &
cd /srv/frontend
PORT="${PORT:-3000}" HOSTNAME=0.0.0.0 node server.js &
# если один из процессов завершился, останавливаем контейнер: платформа перезапустит его
wait -n
exit 1
