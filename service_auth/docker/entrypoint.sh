#!/bin/bash
set -e

echo "Waiting for Postgres and Redis"
python3 /opt/wait_for_services.py

exec "$@"