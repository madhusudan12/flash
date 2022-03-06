#!/bin/sh
gunicorn wsgi:app --reload -b 0.0.0.0:8000 -w="${workers:-4}" --max-requests=3000 --timeout 600