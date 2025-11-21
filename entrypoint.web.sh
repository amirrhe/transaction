#!/bin/sh
set -e
python manage.py migrate || true

python manage.py runserver 0.0.0.0:8000
