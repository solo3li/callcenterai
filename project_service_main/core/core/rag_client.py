import requests
from django.conf import settings

def upload_document_to_rag(tenant_id, file_url, file_name):
    url = f"{settings.RAG_SERVICE_URL}/api/documents/"
    headers = {"Authorization": f"Bearer {settings.RAG_INTERNAL_API_KEY}"}
    payload = {
        "tenant_id": tenant_id,
        "file_url": file_url,
        "file_name": file_name
    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()

def delete_document_from_rag(tenant_id, document_id):
    url = f"{settings.RAG_SERVICE_URL}/api/documents/{document_id}/"
    headers = {"Authorization": f"Bearer {settings.RAG_INTERNAL_API_KEY}"}
    payload = {"tenant_id": tenant_id}
    response = requests.delete(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()

def retrieve_knowledge(tenant_id, query, document_ids=None):
    url = f"{settings.RAG_SERVICE_URL}/api/retrieve/"
    headers = {"Authorization": f"Bearer {settings.RAG_INTERNAL_API_KEY}"}
    payload = {
        "tenant_id": tenant_id,
        "query": query
    }
    if document_ids:
        payload["document_ids"] = document_ids
        
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json().get('results', [])
