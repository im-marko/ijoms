#!/bin/bash
# Vercel static build: collect Django static files (admin CSS/JS) into
# staticfiles/, which @vercel/static-build publishes at /static/.
python3 -m pip install --break-system-packages -r requirements.txt
python3 manage.py collectstatic --noinput
