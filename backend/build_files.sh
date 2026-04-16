#!/bin/bash
pip install -r requirements.txt
python manage.py collectstatic --noinput 2>/dev/null || true
python manage.py migrate --noinput
python manage.py loaddata seed_fixtures.json 2>/dev/null || true
