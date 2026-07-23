#!/bin/bash
# start.sh
# Run the application wrapped in Xvfb so Playwright headless=False works without a real display

# Start Xvfb in the background
Xvfb :99 -screen 0 1280x1024x24 &
export DISPLAY=:99

# Give Xvfb a moment to start
sleep 1

# Start the gunicorn server
echo "Starting Gunicorn..."
exec gunicorn application:app --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120
