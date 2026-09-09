from django.db import models
from pgvector.django import VectorField

class Document(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    )

    tenant_id = models.CharField(max_length=100, db_index=True)
    file_name = models.CharField(max_length=255)
    file_url = models.URLField(max_length=1000)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.tenant_id}] {self.file_name} ({self.status})"

class DocumentChunk(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    tenant_id = models.CharField(max_length=100, db_index=True) # Duplicated for easier filtering
    text = models.TextField()
    # OpenAI text-embedding-3-small uses 1536 dimensions
    embedding = VectorField(dimensions=1536)

    def __str__(self):
        return f"Chunk {self.id} of {self.document.file_name}"
