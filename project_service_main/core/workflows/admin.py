from django.contrib import admin
from .models import Workflow, WorkflowCredential

@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'trigger_type', 'is_active', 'n8n_workflow_id')
    list_filter = ('trigger_type', 'is_active', 'organization')
    search_fields = ('name',)

@admin.register(WorkflowCredential)
class WorkflowCredentialAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'credential_type')
    list_filter = ('credential_type', 'organization')
    search_fields = ('name',)