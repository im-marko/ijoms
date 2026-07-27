#!/bin/bash
# Vercel static build: collect Django static files (admin CSS/JS) into
# staticfiles/, which @vercel/static-build publishes at /static/.
pip install -r requirements.txt
python manage.py collectstatic --noinput
