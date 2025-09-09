FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Create startup script
RUN echo '#!/bin/bash\n\
# Start Celery worker in background\n\
celery -A auth.config.worker worker --loglevel=info --detach\n\
\n\
# Start Celery beat scheduler in background\n\
celery -A auth.config.worker beat --loglevel=info --detach\n\
\n\
# Start FastAPI with uvicorn\n\
uvicorn app:app --host 0.0.0.0 --port 8000\n\
' > /app/start.sh && chmod +x /app/start.sh

EXPOSE 8000

CMD ["/app/start.sh"]