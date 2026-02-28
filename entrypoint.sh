#!/bin/bash
set -e

echo "Running DataBase migrations..."
cd /app/app/models/db_schemas/mini_rag
alembic upgrade head

exec "$@"