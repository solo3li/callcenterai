from django.db import models
from core.models import TenantAwareModel

class AgentGroup(TenantAwareModel):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name
