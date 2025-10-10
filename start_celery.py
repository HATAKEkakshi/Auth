#!/usr/bin/env python3
"""
Celery worker startup script for Auth system
"""
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    # Start Celery worker with proper command
    os.system("celery -A auth.config.worker worker --loglevel=info")