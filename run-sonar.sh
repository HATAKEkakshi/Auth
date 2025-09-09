#!/bin/bash

# SonarQube Scanner Script for Enterprise Auth System

echo "🔍 Starting SonarQube Analysis..."

# Install dependencies if not present
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt

# Run tests with coverage
echo "🧪 Running tests with coverage..."
pytest --cov=auth --cov-report=xml --cov-report=html --junitxml=test-results.xml

# Run SonarQube scanner
echo "Running SonarQube analysis..."
sonar-scanner \
  -Dsonar.projectKey=enterprise-auth-system \
  -Dsonar.sources=auth \
  -Dsonar.host.url=${SONAR_HOST_URL:-http://localhost:9000} \
  -Dsonar.login=${SONAR_TOKEN}

echo "SonarQube analysis completed!"