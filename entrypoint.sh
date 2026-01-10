#!/bin/bash
set -e

# optional: run migrations, collectstatic
python manage.py migrate --noinput
# If you serve static from container (not recommended for production CDN):
python manage.py collectstatic --noinput

# Start Uvicorn
exec python -m uvicorn interior_bazzar.asgi:application --port 8000 --host 0.0.0.0
 