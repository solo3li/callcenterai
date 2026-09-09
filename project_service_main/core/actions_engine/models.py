from django.db import models
from django.core.validators import RegexValidator
from core.models import TenantAwareModel

class ActionDefinition(TenantAwareModel):
    PROTOCOL_CHOICES = (
        ('HTTP', 'HTTP (REST)'),
        ('GRAPHQL', 'GraphQL'),
        ('WEBSOCKET', 'WebSocket'),
        ('GRPC', 'gRPC'),
    )
    
    METHOD_CHOICES = (
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('DELETE', 'DELETE'),
    )

    version = models.CharField(max_length=10, default='v1', help_text='API Version e.g., v1')

    # Function name format for LLM tools
    name = models.CharField(
        max_length=64, 
        validators=[RegexValidator(r'^[a-zA-Z0-9_]+$', 'Only alphanumeric characters and underscores are allowed.')],
        help_text="Unique name for the AI to call. e.g., 'check_order_status'"
    )
    description = models.TextField(help_text="Instructions for the AI on WHEN to use this action.")
    
    protocol = models.CharField(max_length=20, choices=PROTOCOL_CHOICES, default='HTTP')
    endpoint_url = models.CharField(max_length=1000, help_text="e.g., https://api.example.com/v1/users/{{user_id}}")
    http_method = models.CharField(max_length=10, choices=METHOD_CHOICES, default='POST', blank=True, null=True)
    
    headers = models.JSONField(default=dict, blank=True, help_text='{"Authorization": "Bearer token"}')
    body_template = models.TextField(blank=True, help_text="JSON or GraphQL template with {{variables}}")
    
    # JSON Schema definition for inputs
    input_schema = models.JSONField(
        default=dict, 
        blank=True, 
        help_text='JSON Schema defining the exact parameters the AI needs to ask the user for.'
    )
    
    # Extractor
    response_extractor = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        help_text="JSONPath to extract data. e.g. '$.data.status'"
    )
    
    timeout_seconds = models.IntegerField(default=10)
    retry_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('organization', 'name')

    def __str__(self):
        return f"{self.name} ({self.protocol})"
