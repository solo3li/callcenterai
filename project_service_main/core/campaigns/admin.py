from django.contrib import admin
from .models import OutboundCampaign, CampaignLead

@admin.register(OutboundCampaign)
class OutboundCampaignAdmin(admin.ModelAdmin):
    pass

@admin.register(CampaignLead)
class CampaignLeadAdmin(admin.ModelAdmin):
    pass