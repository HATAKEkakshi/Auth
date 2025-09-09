import requests
from dotenv import load_dotenv
load_dotenv()
import os

"""This function is used to integrate Watchman logging service with other services."""
"""Watchman is an AI-powered log monitoring platform that revolutionizes log analysis and system monitoring.

    AI Chat Interface
    Query logs using natural language

    Real-time Monitoring
    Instant alerts and notifications


    Key Features
        - For DevOps Teams
        - Centralized log aggregation
        -  Real-time log analysis
        -  Error pattern detection
        -  Log-based alerting
        - For Developers
        -  Application log debugging
        -  Performance log insights
        -  Multi-language support
        -  Log ingestion APIs
    """

def logger(service:str,integration:str,level:str,priority:str,message:str):
    try:
        response = requests.post(
            'http://logger:8000/logger/log',
            json={
                'account_id': os.getenv('Account_id'), ## Fetching account id from environment variable
                'service': service,
                'integration': integration,
                'level': level,
                "priority": priority,
                'message': message
            },
            headers={
                'WATCHMAN-API-KEY': os.getenv('Access_token'), ## Fetching access token from environment variable
                'Content-Type': 'application/json'
            },
            timeout=5
        )
    except requests.exceptions.ConnectionError as e:
        print(f"Logger service connection failed: {e}")
    except Exception as e:
        print(f"Logger error: {e}")