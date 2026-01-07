#!/bin/bash
# Scheduler for processing recurring invoices
# Runs the management command once per day at the specified time

# Default to running at 6:00 AM
SCHEDULE_HOUR=${SCHEDULE_HOUR:-6}
SCHEDULE_MINUTE=${SCHEDULE_MINUTE:-0}

echo "Recurring invoice scheduler started"
echo "Will check for due invoices daily at ${SCHEDULE_HOUR}:${SCHEDULE_MINUTE}"

while true; do
    # Get current time
    CURRENT_HOUR=$(date +%H)
    CURRENT_MINUTE=$(date +%M)
    
    # Check if it's time to run (within the same minute)
    if [ "$CURRENT_HOUR" -eq "$SCHEDULE_HOUR" ] && [ "$CURRENT_MINUTE" -eq "$SCHEDULE_MINUTE" ]; then
        echo ""
        echo "=========================================="
        echo "Running recurring invoice check at $(date)"
        echo "=========================================="
        
        python manage.py process_recurring_invoices
        
        echo "=========================================="
        echo "Completed at $(date)"
        echo "=========================================="
        
        # Sleep for 60 seconds to avoid running multiple times in the same minute
        sleep 60
    fi
    
    # Check every 30 seconds
    sleep 30
done
