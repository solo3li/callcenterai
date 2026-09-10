from django.db import models
from core.models import TenantAwareModel

class WorkflowCredential(TenantAwareModel):
    name = models.CharField(max_length=150, help_text="e.g., My Telegram Bot")
    credential_type = models.CharField(max_length=100, help_text="n8n credential type e.g., telegramApi")
    n8n_credential_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.credential_type})"

class Workflow(TenantAwareModel):
    TRIGGER_CHOICES = (
        ('PRE_CALL', 'Pre-Call (Context Fetch)'),
        ('MID_CALL', 'Mid-Call (AI Tool/Action)'),
        ('POST_CALL', 'Post-Call (Wrap-up)'),
    )

    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, help_text="Used by AI if MID_CALL to understand when to trigger.")
    trigger_type = models.CharField(max_length=20, choices=TRIGGER_CHOICES, default='POST_CALL')
    
    n8n_workflow_id = models.CharField(max_length=255, blank=True, null=True, help_text="ID of the workflow in n8n")
    webhook_url = models.URLField(max_length=1000, blank=True, null=True, help_text="The n8n webhook URL to trigger this workflow")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_trigger_type_display()})"
