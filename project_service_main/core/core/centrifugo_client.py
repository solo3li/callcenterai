import requests
import json
import logging

logger = logging.getLogger(__name__)

CENTRIFUGO_API_URL = "http://localhost:8000/api"
CENTRIFUGO_API_KEY = "my_api_key" # Replace with actual from centrifugo.json

def publish(channel: str, data: dict):
    payload = {
        "method": "publish",
        "params": {
            "channel": channel,
            "data": data
        }
    }
    headers = {
        "Content-type": "application/json",
        "Authorization": f"apikey {CENTRIFUGO_API_KEY}"
    }
    try:
        response = requests.post(CENTRIFUGO_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Centrifugo publish error: {e}")
        return None
