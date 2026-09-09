import os
import requests
from openai import OpenAI
from django.conf import settings
from .models import Document, DocumentChunk

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
        
        # Embed chunks using OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        for text_chunk in chunks:
            if not text_chunk.strip():
                continue
                
            # Get embedding
            response = client.embeddings.create(
                input=text_chunk,
                model="text-embedding-3-small"
            )
            embedding_vector = response.data[0].embedding
            
            # Save to pgvector
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

def retrieve_relevant_chunks(tenant_id, query, top_k=5):
    """
    Embeds the user query and performs cosine similarity search.
    """
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.embeddings.create(
        input=query,
        model="text-embedding-3-small"
    )
    query_embedding = response.data[0].embedding
    
    # Perform vector search strictly within the tenant's boundaries
    # pgvector provides an l2_distance or cosine_distance
    # Django pgvector allows order_by(EmbeddingField.cosine_distance(query_embedding))
    
    chunks = DocumentChunk.objects.filter(tenant_id=tenant_id).order_by(
        DocumentChunk.embedding.cosine_distance(query_embedding)
    )[:top_k]
    
    return [{"text": c.text, "document": c.document.file_name} for c in chunks]
