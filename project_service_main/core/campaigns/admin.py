from django.contrib import admin
from .models import OutboundCampaign

@admin.register(OutboundCampaign)
class OutboundCampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'status', 'ai_agent', 'created_at')
    list_filter = ('status', 'organization')
    search_fields = ('name',)