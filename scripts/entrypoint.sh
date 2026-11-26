#!/bin/sh
set -eu
flask --app app init-db
exec gunicorn --bind 0.0.0.0:8000 --workers 1 --threads 4 --access-logfile - 'app:create_app()'
