from django.contrib import admin
from .models import KnowledgeDocument

@admin.register(KnowledgeDocument)
class KnowledgeDocumentAdmin(admin.ModelAdmin):
    pass