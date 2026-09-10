from django.contrib import admin
from .models import CallLog, CallEvent

@admin.register(CallLog)
class CallLogAdmin(admin.ModelAdmin):
    pass

@admin.register(CallEvent)
class CallEventAdmin(admin.ModelAdmin):
    pass