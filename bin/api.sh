#!/bin/bash
# api.sh - Script to run the Enphase Flask API server
# This script starts the Flask server on port 5000.

LOG_DIR="/home/amit/code/enphase/production/logs"
mkdir -p "$LOG_DIR"

LOG_FILE="$LOG_DIR/api.log"
CURRENT_TIME=$(date "+%Y-%m-%d %H:%M:%S")

cd /home/amit/code/enphase

echo "[$CURRENT_TIME] Starting Flask API server on port 5000..." >> "$LOG_FILE"
exec pipenv run api >> "$LOG_FILE" 2>&1
