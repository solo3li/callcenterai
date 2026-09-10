from django.contrib import admin
from .models import UsageRecord

@admin.register(UsageRecord)
class UsageRecordAdmin(admin.ModelAdmin):
    pass