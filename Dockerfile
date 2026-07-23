FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=application.py

# Set work directory
WORKDIR /app

# Install OS dependencies, including Xvfb for Playwright
RUN apt-get update && apt-get install -y \
    xvfb \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright dependencies and browsers
RUN playwright install-deps chromium
RUN playwright install chromium

# Copy the application code
COPY . /app/

# Copy the start script and make it executable
COPY start.sh /app/
RUN chmod +x /app/start.sh

# Expose port
EXPOSE 8000

# Start the application via the entrypoint script
CMD ["/app/start.sh"]
