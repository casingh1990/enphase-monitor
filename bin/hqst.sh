#!/bin/bash
# hqst.sh - Script to run the HQST solar charge controller export

# Define the log file location
LOG_FILE="/home/amit/code/enphase/hqst_cron.log"
CURRENT_TIME=$(date "+%Y-%m-%d %H:%M:%S")

cd /home/amit/code/enphase

# Run the hqst export script via pipenv
if pipenv run hqst >> "$LOG_FILE" 2>&1; then
    echo "[$CURRENT_TIME] HQST data fetched successfully." >> "$LOG_FILE"
else
    echo "[$CURRENT_TIME] ❌ HQST data fetch failed." >> "$LOG_FILE"
fi
