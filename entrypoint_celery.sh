#!/bin/bash
celery -A mercury_app worker
exec "$@"
