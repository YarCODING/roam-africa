#!/bin/bash

celery -A YOUR_PROJECT_NAME worker --loglevel=info -E -B --concurrency=2 &

python healthcheck.py
