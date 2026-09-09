from django.db import models
from core.models import TenantAwareModel
from agents.models import AgentGroup
from telephony.models import SIPTrunk

class OutboundCampaign(TenantAwareModel):
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('RUNNING', 'Running'),
        ('PAUSED', 'Paused'),
        ('COMPLETED', 'Completed'),
    )

    name = models.CharField(max_length=255)
    agent_group = models.ForeignKey(AgentGroup, on_delete=models.CASCADE, related_name='campaigns')
    sip_trunk = models.ForeignKey(SIPTrunk, on_delete=models.SET_NULL, null=True, blank=True, related_name='campaigns')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')

    def __str__(self):
        return self.name

class CampaignLead(TenantAwareModel):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('CALLING', 'Calling'),
        ('ANSWERED', 'Answered'),
        ('FAILED', 'Failed'),
    )

    campaign = models.ForeignKey(OutboundCampaign, on_delete=models.CASCADE, related_name='leads')
    phone_number = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.phone_number} - {self.campaign.name}"
