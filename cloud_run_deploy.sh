#!/bin/bash

ENV="${1:?Usage: $0 <stag|prod>}"

case "$ENV" in
  stag)
    SERVICE_NAME="bank-exam-bot-stag"
    ENV_FILE="stag_env.yaml"
    ;;
  prod)
    SERVICE_NAME="bank-exam-bot"
    ENV_FILE="prod_env.yaml"
    ;;
  *)
    echo "Invalid environment: $ENV. Use 'stag' or 'prod'."
    exit 1
    ;;
esac

gcloud run deploy "$SERVICE_NAME" \
    --source . \
    --region asia-south1 \
    --allow-unauthenticated \
    --env-vars-file "$ENV_FILE"

