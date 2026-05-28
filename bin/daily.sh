#!/bin/bash
# daily_task.sh - A script to log execution time

# Define the log file location (use absolute paths in cron scripts)
LOG_FILE="/var/log/my_daily_task.log"
cd /home/amit/code/enphase
pipenv run daily
echo "Task executed successfully at: $CURRENT_TIME" >> "$LOG_FILE"