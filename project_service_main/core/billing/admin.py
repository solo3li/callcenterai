from django.contrib import admin
from .models import UsageRecord

@admin.register(UsageRecord)
class UsageRecordAdmin(admin.ModelAdmin):
    list_display = ('usage_type', 'amount', 'organization', 'description', 'recorded_at')
    list_filter = ('usage_type', 'organization')
    search_fields = ('description',)
    readonly_fields = ('recorded_at',)