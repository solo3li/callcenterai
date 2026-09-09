import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

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
        "Authorization": f"apikey {settings.CENTRIFUGO_API_KEY}"
    }
    try:
        response = requests.post(settings.CENTRIFUGO_URL, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Centrifugo publish error: {e}")
        return None
