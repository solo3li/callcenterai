from django.db import models
from core.models import TenantAwareModel
from campaigns.models import OutboundCampaign

class CallLog(TenantAwareModel):
    DIRECTION_CHOICES = (
        ('INBOUND', 'Inbound'),
        ('OUTBOUND', 'Outbound'),
    )

    room_name = models.CharField(max_length=255, unique=True)
    phone_number = models.CharField(max_length=50)
    direction = models.CharField(max_length=20, choices=DIRECTION_CHOICES)
    
    campaign = models.ForeignKey(OutboundCampaign, on_delete=models.SET_NULL, null=True, blank=True, related_name='call_logs')
    
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration = models.IntegerField(default=0, help_text="Duration in seconds")
    
    recording_url = models.CharField(max_length=500, blank=True)
    transcript = models.TextField(blank=True, help_text="Full text conversation")
    
    # Post-Call AI Analysis
    summary = models.TextField(blank=True)
    sentiment = models.CharField(max_length=50, blank=True)
    outcome = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.direction} Call - {self.phone_number} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"
