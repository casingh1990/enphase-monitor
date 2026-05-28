#!/bin/bash
# hqst.sh - Script to run the HQST solar charge controller export

# Define log directory and file named according to the current date
LOG_DIR="/home/amit/code/enphase/production/logs"
mkdir -p "$LOG_DIR"

LOG_DATE=$(date "+%Y%m%d")
LOG_FILE="$LOG_DIR/hqst_${LOG_DATE}.log"
CURRENT_TIME=$(date "+%Y-%m-%d %H:%M:%S")

cd /home/amit/code/enphase

# Run the hqst export script via pipenv
if pipenv run hqst >> "$LOG_FILE" 2>&1; then
    echo "[$CURRENT_TIME] HQST data fetched successfully." >> "$LOG_FILE"
else
    echo "[$CURRENT_TIME] ❌ HQST data fetch failed." >> "$LOG_FILE"
fi

# Clean up logs older than 14 days
find "$LOG_DIR" -name "hqst_*.log" -type f -mtime +14 -delete
