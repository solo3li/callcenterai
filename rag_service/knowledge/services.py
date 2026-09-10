import os
import requests
from google import genai
from google.genai import types
from django.conf import settings
from .models import Document, DocumentChunk

# Gemini embeddings require a task_type per call: documents are embedded as
# RETRIEVAL_DOCUMENT and queries as RETRIEVAL_QUERY. Mixing them up silently
# degrades retrieval quality.
TASK_TYPE_DOCUMENT = "RETRIEVAL_DOCUMENT"
TASK_TYPE_QUERY = "RETRIEVAL_QUERY"

# gemini-embedding-001 outputs 3072 dims by default; MRL truncation is used to
# keep the pgvector column at 1536 dims (no schema migration needed).
EMBED_BATCH_SIZE = 100


def _embed_client():
    return genai.Client(api_key=settings.GEMINI_API_KEY)


def embed_texts(texts, task_type=TASK_TYPE_DOCUMENT):
    """Embed a batch of texts with Gemini, returning a list of 1536-dim vectors."""
    client = _embed_client()
    vectors = []
    for i in range(0, len(texts), EMBED_BATCH_SIZE):
        batch = texts[i:i + EMBED_BATCH_SIZE]
        response = client.models.embed_content(
            model=settings.EMBEDDING_MODEL,
            contents=batch,
            config=types.EmbedContentConfig(
                task_type=task_type,
                output_dimensionality=settings.EMBEDDING_DIMENSIONS,
            ),
        )
        vectors.extend([e.values for e in response.embeddings])
    return vectors


def extract_text_from_file(file_url):
    """
    Downloads file from MinIO/URL and passes it to Apache Tika for text extraction.
    """
    # 1. Download file content
    response = requests.get(file_url)
    response.raise_for_status()
    file_content = response.content

    # 2. Send to Tika Server
    tika_url = f"{settings.TIKA_URL}/tika"
    headers = {
        'Accept': 'text/plain',
    }
    tika_response = requests.put(tika_url, data=file_content, headers=headers)
    tika_response.raise_for_status()

    return tika_response.text

def chunk_text(text, chunk_size=1000, overlap=200):
    """
    Splits long text into overlapping chunks.
    """
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk_words = words[i:i + chunk_size]
        chunks.append(" ".join(chunk_words))
        i += chunk_size - overlap
        if i >= len(words) - overlap: # Prevent infinite loop on last small chunk
            break
    return chunks

def process_document(document_id):
    """
    End-to-end processing: Extract -> Chunk -> Embed -> Save
    """
    doc = Document.objects.get(id=document_id)
    doc.status = 'PROCESSING'
    doc.save()

    try:
        # Extract text
        raw_text = extract_text_from_file(doc.file_url)

        # Chunk text
        chunks = chunk_text(raw_text, chunk_size=200, overlap=50) # 200 words per chunk approx
        chunks = [c for c in chunks if c.strip()]
        if not chunks:
            raise ValueError("No text could be extracted from the document.")

        # Embed chunks with Gemini as retrieval documents (batched)
        vectors = embed_texts(chunks, task_type=TASK_TYPE_DOCUMENT)

        # Save to pgvector
        for text_chunk, embedding_vector in zip(chunks, vectors):
            DocumentChunk.objects.create(
                document=doc,
                tenant_id=doc.tenant_id,
                text=text_chunk,
                embedding=embedding_vector
            )

        doc.status = 'COMPLETED'
        doc.save()

    except Exception as e:
        print(f"Error processing document {document_id}: {e}")
        doc.status = 'FAILED'
        doc.save()

def retrieve_relevant_chunks(tenant_id, query, top_k=5, document_ids=None):
    """
    Embeds the user query and performs cosine similarity search.
    """
    query_embedding = embed_texts([query], task_type=TASK_TYPE_QUERY)[0]

    # Perform vector search strictly within the tenant's boundaries
    qs = DocumentChunk.objects.filter(tenant_id=tenant_id)

    if document_ids:
        qs = qs.filter(document_id__in=document_ids)

    chunks = qs.order_by(
        DocumentChunk.embedding.cosine_distance(query_embedding)
    )[:top_k]

    return [{"text": c.text, "document": c.document.file_name} for c in chunks]
