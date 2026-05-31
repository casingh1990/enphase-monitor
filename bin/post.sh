#!/bin/bash
# post.sh - Script to update WordPress with solar production data
# This script uploads daily graphs and posts production/consumption data.
# Call this every 15-30 minutes via cron.

# Define log directory and file named according to the current date
LOG_DIR="/home/amit/code/enphase/production/logs"
mkdir -p "$LOG_DIR"

LOG_DATE=$(date "+%Y%m%d")
LOG_FILE="$LOG_DIR/post_${LOG_DATE}.log"
CURRENT_TIME=$(date "+%Y-%m-%d %H:%M:%S")

cd /home/amit/code/enphase

# Run the WordPress update script via pipenv
echo "[$CURRENT_TIME] Starting WordPress post update..." >> "$LOG_FILE"
if pipenv run python -c "from utils.update_post import post_solar_update; post_solar_update(include_images=True)" >> "$LOG_FILE" 2>&1; then
    echo "[$CURRENT_TIME] WordPress post updated successfully." >> "$LOG_FILE"
else
    echo "[$CURRENT_TIME] ❌ WordPress post update failed." >> "$LOG_FILE"
fi

# Clean up logs older than 14 days
find "$LOG_DIR" -name "post_*.log" -type f -mtime +14 -delete
