from django.db import models
from core.models import TenantAwareModel
from core.rag_client import upload_document_to_rag, delete_document_from_rag

class KnowledgeDocument(TenantAwareModel):
    title = models.CharField(max_length=255)
    file_url = models.URLField(max_length=1000)
    
    # Optional relation to AIAgent: if we want to restrict knowledge per agent.
    # We can also do ManyToMany from AIAgent to KnowledgeDocument.
    # We will add ManyToMany on AIAgent model later if needed.
    
    rag_document_id = models.IntegerField(null=True, blank=True, help_text="ID of the document in the isolated RAG Microservice")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and self.file_url:
            try:
                tenant_id = f"tenant_{self.organization.id}"
                response = upload_document_to_rag(tenant_id, self.file_url, self.title)
                self.rag_document_id = response.get('document_id')
                super().save(update_fields=['rag_document_id'])
            except Exception as e:
                print(f"Failed to sync with RAG service: {e}")

    def delete(self, *args, **kwargs):
        if self.rag_document_id:
            try:
                tenant_id = f"tenant_{self.organization.id}"
                delete_document_from_rag(tenant_id, self.rag_document_id)
            except Exception as e:
                print(f"Failed to delete from RAG service: {e}")
        super().delete(*args, **kwargs)
