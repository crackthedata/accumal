FROM python:3.11-slim

WORKDIR /app

# Install cron
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Setup cron job
# 1. Init DB, 2. Fetch GSC, 3. Fetch Competitors, 4. Fetch Authority, 5. Export Reports
# Commands are wrapped in parentheses so all output is redirected to the Docker container logs.
RUN echo "0 2 * * * root cd /app && (/usr/local/bin/python src/db.py && /usr/local/bin/python src/gsc_fetcher.py && /usr/local/bin/python src/competitor_analyzer.py && /usr/local/bin/python src/authority_fetcher.py && /usr/local/bin/python src/export_reports.py) > /proc/1/fd/1 2>/proc/1/fd/2" > /etc/cron.d/seo_cron

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/seo_cron

# Apply cron job
RUN crontab /etc/cron.d/seo_cron

# Run cron in the foreground as default command
CMD ["cron", "-f"]
