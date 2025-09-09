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

# Create startup script inside the working directory
RUN echo '#!/bin/bash\n\
celery -A auth.config.worker worker --loglevel=info --detach\n\
celery -A auth.config.worker beat --loglevel=info --detach\n\
uvicorn app:app --host 0.0.0.0 --port 8000\n\
' > start.sh && chmod +x start.sh

EXPOSE 8000

# Run startup script
CMD ["./start.sh"]
