from django.db import models
from core.models import TenantAwareModel

class SIPTrunk(TenantAwareModel):
    name = models.CharField(max_length=100, help_text="e.g., Twilio Primary, Local PBX")
    provider = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., Twilio, Vonage")
    host = models.CharField(max_length=255, help_text="SIP URI or IP Address")
    port = models.IntegerField(default=5060)
    username = models.CharField(max_length=100, blank=True, null=True)
    password = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.host})"

class PhoneNumber(TenantAwareModel):
    number = models.CharField(max_length=20, unique=True, help_text="Enter phone number in E.164 format (e.g. +1234567890)")
    sip_trunk = models.ForeignKey(SIPTrunk, on_delete=models.CASCADE, related_name='phone_numbers', null=True, blank=True, help_text="The SIP Trunk this number belongs to")
    group = models.ForeignKey('agents.AgentGroup', on_delete=models.SET_NULL, null=True, blank=True, related_name='phone_numbers', help_text="The Agent Group (AI or Human) that will receive calls to this number.")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.number
