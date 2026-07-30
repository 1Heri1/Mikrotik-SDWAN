#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting backend..."
exec gunicorn -c gunicorn_conf.py app.main:app
