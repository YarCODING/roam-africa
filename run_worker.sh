#!/bin/bash

celery -A config worker --loglevel=info -E -B --concurrency=2 &

python healthcheck.py
