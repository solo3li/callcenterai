from django.contrib import admin
from .models import SIPTrunk, PhoneNumber

@admin.register(SIPTrunk)
class SIPTrunkAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'sip_server', 'is_active')
    list_filter = ('is_active', 'organization')
    search_fields = ('name', 'sip_server')

@admin.register(PhoneNumber)
class PhoneNumberAdmin(admin.ModelAdmin):
    list_display = ('number', 'organization', 'sip_trunk', 'ai_agent', 'is_active')
    list_filter = ('is_active', 'organization')
    search_fields = ('number',)