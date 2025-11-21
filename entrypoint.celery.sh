#!/bin/sh
set -e

python manage.py migrate --noinput || true

celery -A transaction_service worker -l info
