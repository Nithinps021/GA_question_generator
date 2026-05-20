#!/bin/bash

# Fallback to 8080 if PORT is not set by Cloud Run (useful for local testing)
PORT="${PORT:-8080}"

# Run the web server.
# Using 'exec' ensures the app runs as PID 1 and receives shutdown signals properly.
exec uvicorn main:app --host 0.0.0.0 --port "$PORT"