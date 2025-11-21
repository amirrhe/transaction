#!/bin/sh
set -e

celery -A zibal_task worker -l info
