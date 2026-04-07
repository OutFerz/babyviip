#!/usr/bin/env sh
set -e

DB_HOST="${DATABASE_HOST:-db}"
DB_PORT="${DATABASE_PORT:-5432}"
DB_USER="${DATABASE_USER:-admin}"
DB_NAME="${DATABASE_NAME:-babyviip_db}"

echo "Waiting for Postgres at ${DB_HOST}:${DB_PORT}..."
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; do
  sleep 1
done

python manage.py migrate --noinput

exec python manage.py runserver 0.0.0.0:8000

