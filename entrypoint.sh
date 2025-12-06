#!/bin/bash
set -e

# optional: run migrations, collectstatic
python manage.py migrate --noinput
# If you serve static from container (not recommended for production CDN):
python manage.py collectstatic --noinput

# Start Gunicorn
exec gunicorn interior_bazzar_api.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --log-level info
