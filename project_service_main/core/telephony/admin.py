from django.contrib import admin
from .models import SIPTrunk, PhoneNumber

@admin.register(SIPTrunk)
class SIPTrunkAdmin(admin.ModelAdmin):
    pass

@admin.register(PhoneNumber)
class PhoneNumberAdmin(admin.ModelAdmin):
    pass