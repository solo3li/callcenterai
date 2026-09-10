import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class N8NClient:
    """
    Client for interacting with the Headless n8n instance.
    By default uses Docker networking hostname 'http://n8n:5678'.
    """
    def __init__(self):
        self.base_url = getattr(settings, 'N8N_API_URL', 'http://n8n:5678/api/v1')
        self.internal_url = getattr(settings, 'N8N_INTERNAL_URL', 'http://n8n:5678/rest')
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        # In a real setup, add X-N8N-API-KEY here if authentication is enabled.
        api_key = getattr(settings, 'N8N_API_KEY', None)
        if api_key:
            self.headers['X-N8N-API-KEY'] = api_key

    def get_node_types(self):
        """Fetches the massive JSON registry of all n8n node types for custom UI builders."""
        try:
            response = requests.get(f"{self.internal_url}/node-types", headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch n8n node types: {e}")
            return {"data": []}

    def get_credential_types(self):
        """Fetches the registry of all credential types for custom UI builders."""
        try:
            response = requests.get(f"{self.internal_url}/credentials-types", headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch n8n credential types: {e}")
            return {"data": []}

    def create_credential(self, name, credential_type, data):
        """
        Creates a credential securely in n8n.
        :param data: Dict of sensitive data (e.g. {"botToken": "..."})
        """
        payload = {
            "name": name,
            "type": credential_type,
            "nodesAccess": [],
            "data": data
        }
        try:
            response = requests.post(f"{self.base_url}/credentials", json=payload, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create n8n credential: {e}")
            return None

    def create_workflow(self, name, nodes, connections):
        """
        Creates or updates a workflow via the API.
        """
        payload = {
            "name": name,
            "nodes": nodes,
            "connections": connections,
            "active": True
        }
        try:
            response = requests.post(f"{self.base_url}/workflows", json=payload, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create n8n workflow: {e}")
            return None
