from django.contrib import admin
from .models import Document, DocumentChunk

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    pass

@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    pass
