from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .models import Document
from .services import process_document, retrieve_relevant_chunks
import threading

class InternalAuthMixin:
    """
    Validates that the request comes from the trusted core service
    """
    def validate_key(self, request):
        api_key = request.headers.get('Authorization')
        if not api_key or api_key != f"Bearer {settings.INTERNAL_API_KEY}":
            return False
        return True

class DocumentUploadView(APIView, InternalAuthMixin):
    def post(self, request):
        if not self.validate_key(request):
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
            
        tenant_id = request.data.get('tenant_id')
        file_url = request.data.get('file_url')
        file_name = request.data.get('file_name', 'Unknown')
        
        if not tenant_id or not file_url:
            return Response({"error": "tenant_id and file_url are required"}, status=status.HTTP_400_BAD_REQUEST)
            
        doc = Document.objects.create(
            tenant_id=tenant_id,
            file_url=file_url,
            file_name=file_name
        )
        
        # Trigger background processing (using simple threading for now, can be upgraded to Celery/Inngest)
        thread = threading.Thread(target=process_document, args=(doc.id,))
        thread.start()
        
        return Response({"status": "processing", "document_id": doc.id})

class DocumentDeleteView(APIView, InternalAuthMixin):
    def delete(self, request, doc_id):
        if not self.validate_key(request):
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
            
        tenant_id = request.data.get('tenant_id')
        
        try:
            doc = Document.objects.get(id=doc_id, tenant_id=tenant_id)
            # The CASCADE delete on DocumentChunk will automatically delete all vector embeddings
            doc.delete()
            return Response({"status": "deleted"})
        except Document.DoesNotExist:
            return Response({"error": "Document not found"}, status=status.HTTP_404_NOT_FOUND)

class RetrieveKnowledgeView(APIView, InternalAuthMixin):
    def post(self, request):
        if not self.validate_key(request):
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
            
        tenant_id = request.data.get('tenant_id')
        query = request.data.get('query')
        document_ids = request.data.get('document_ids')
        
        if not tenant_id or not query:
            return Response({"error": "tenant_id and query are required"}, status=status.HTTP_400_BAD_REQUEST)
            
        chunks = retrieve_relevant_chunks(tenant_id, query, document_ids=document_ids)
        
        return Response({"results": chunks})
