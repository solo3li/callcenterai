from django.contrib import admin
from .models import WorkflowCredential, Workflow

@admin.register(WorkflowCredential)
class WorkflowCredentialAdmin(admin.ModelAdmin):
    pass

@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    pass