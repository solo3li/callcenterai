from django.db import models
from core.models import TenantAwareModel

class PhoneNumber(TenantAwareModel):
    number = models.CharField(max_length=20, unique=True, help_text="Enter phone number in E.164 format (e.g. +1234567890)")
    group = models.ForeignKey('agents.AgentGroup', on_delete=models.SET_NULL, null=True, blank=True, related_name='phone_numbers', help_text="The Agent Group (AI or Human) that will receive calls to this number.")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.number
