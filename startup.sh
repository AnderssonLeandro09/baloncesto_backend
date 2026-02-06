#!/bin/bash
set -e

echo "=== Ejecutando migraciones ==="
python manage.py migrate --noinput

echo "=== Recolectando archivos estáticos ==="
python manage.py collectstatic --noinput

echo "=== Iniciando Gunicorn ==="
exec gunicorn basketball_project.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --threads 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
