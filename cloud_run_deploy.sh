#!/bin/bash

gcloud run deploy bank-exam-bot \
    --source . \
    --region asia-south1 \
    --allow-unauthenticated \
    --env-vars-file env.yaml