#!/bin/bash
set -e

# Загружаем .env
if [ -f .env ]; then
  echo "Loading environment variables from .env"
  set -o allexport
  source .env
  set +o allexport
fi

echo "Waiting for PostgreSQL at $POSTGRES_HOST:$POSTGRES_PORT..."

until pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER"; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 5
done

echo "Postgres is ready, running migrations..."
alembic upgrade head

echo "Starting FastAPI application..."
exec uvicorn main:app --host 0.0.0.0 --port $APP_PORT --reload
