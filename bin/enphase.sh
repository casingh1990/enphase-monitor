#!/bin/bash
# enphase.sh - Script to run the Enphase solar export
# This script is called every minute via cron.

# Define log directory and file named according to the current date
LOG_DIR="/home/amit/code/enphase/production/logs"
mkdir -p "$LOG_DIR"

LOG_DATE=$(date "+%Y%m%d")
LOG_FILE="$LOG_DIR/enphase_${LOG_DATE}.log"
CURRENT_TIME=$(date "+%Y-%m-%d %H:%M:%S")

cd /home/amit/code/enphase

# Run the enphase export script via pipenv
if pipenv run enphase >> "$LOG_FILE" 2>&1; then
    echo "[$CURRENT_TIME] Enphase data fetched successfully." >> "$LOG_FILE"
else
    echo "[$CURRENT_TIME] ❌ Enphase data fetch failed." >> "$LOG_FILE"
fi

# Clean up logs older than 14 days
find "$LOG_DIR" -name "enphase_*.log" -type f -mtime +14 -delete
