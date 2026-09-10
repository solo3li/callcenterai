import time
import requests

RAG_URL = "http://localhost:8002/api"
HEADERS = {
    "Authorization": "Bearer my_secure_internal_key",
    "Content-Type": "application/json"
}

TENANT_ID = 1

TEST_FILE_URL = "https://raw.githubusercontent.com/docker/compose/master/README.md"
print("Uploading document...")

response = requests.post(
    f"{RAG_URL}/documents/",
    headers=HEADERS,
    json={
        "tenant_id": TENANT_ID,
        "file_url": TEST_FILE_URL,
        "file_name": "Docker Compose Readme"
    }
)
print("Upload response:", response.status_code, response.text)
if response.status_code != 200:
    exit(1)

doc_id = response.json().get("document_id")

print("Waiting 10 seconds for document processing (embedding generation)...")
time.sleep(10)

print("Querying the RAG service...")
query_response = requests.post(
    f"{RAG_URL}/retrieve/",
    headers=HEADERS,
    json={
        "tenant_id": TENANT_ID,
        "query": "What is Compose?",
    }
)
print("Query response:", query_response.status_code, query_response.text)
