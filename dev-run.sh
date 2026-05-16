#!/bin/bash
set -a
source .env
set +a
source .venv/bin/activate
uvicorn app.main:app --reload --port 8080
