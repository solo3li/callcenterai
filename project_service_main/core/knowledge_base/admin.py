from django.contrib import admin
from .models import KnowledgeDocument

@admin.register(KnowledgeDocument)
class KnowledgeDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'organization', 'document_url', 'created_at')
    search_fields = ('title',)
    list_filter = ('organization',)