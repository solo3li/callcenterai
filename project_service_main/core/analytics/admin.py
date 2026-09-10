from django.contrib import admin
from .models import CallLog, CallEvent

@admin.register(CallLog)
class CallLogAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'direction', 'status', 'duration', 'ai_agent', 'organization', 'start_time')
    list_filter = ('direction', 'status', 'organization')
    search_fields = ('phone_number', 'room_name')
    readonly_fields = ('start_time',)

@admin.register(CallEvent)
class CallEventAdmin(admin.ModelAdmin):
    list_display = ('call', 'event_type', 'description', 'timestamp')
    list_filter = ('event_type',)