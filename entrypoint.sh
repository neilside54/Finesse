#!/bin/bash
set -e

echo "Chesslizer entrypoint — SERVICE=${SERVICE:-web}"

# ── Wait for PostgreSQL (when DATABASE_URL is set) ────────────────────
if [ -n "$DATABASE_URL" ]; then
  echo "Waiting for PostgreSQL..."
  for i in $(seq 1 30); do
    if python -c "import psycopg2; psycopg2.connect('${DATABASE_URL}')" 2>/dev/null; then
      echo "PostgreSQL is ready."
      break
    fi
    echo "  ...attempt $i/30"
    sleep 2
  done
fi

# Run migrations on every startup (safe for SQLite and PostgreSQL)
python manage.py migrate --noinput 2>/dev/null || true

# Ensure the sites table has a default entry for django-allauth
python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chessslizer.settings')
django.setup()
from django.contrib.sites.models import Site
Site.objects.get_or_create(id=1, defaults={'domain': 'localhost', 'name': 'Finesse'})
" 2>/dev/null || true

case "${SERVICE}" in
  worker)
    echo "Starting Celery worker..."
    celery -A chessslizer worker -l info -c ${CELERY_CONCURRENCY:-2}
    ;;
  beat)
    echo "Starting Celery beat..."
    celery -A chessslizer beat -l info
    ;;
  web|*)
    PORT=${PORT:-8001}
    echo "Starting gunicorn on 0.0.0.0:${PORT}..."
    exec gunicorn chessslizer.wsgi:application \
        --bind 0.0.0.0:${PORT} \
        --workers ${GUNICORN_WORKERS:-2} \
        --timeout ${GUNICORN_TIMEOUT:-1800} \
        --access-logfile -
    ;;
esac
