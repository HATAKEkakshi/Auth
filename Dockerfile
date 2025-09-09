# syntax=docker/dockerfile:1.4

# -------- Build Stage --------
FROM ubuntu:rolling AS builder
LABEL AUTHOR="HEMANT KUMAR"
LABEL VERSION="1.0"

RUN apt-get update && apt-get install -y git openssh-client

WORKDIR /usr/src/app

# Copy the local project files into the image
COPY . Auth/

# -------- Runtime Stage --------
FROM python:3.9.23-trixie

# Set workdir to project root
WORKDIR /usr/src/app/Auth

# Copy code from builder stage
COPY --from=builder /usr/src/app/Auth ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

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