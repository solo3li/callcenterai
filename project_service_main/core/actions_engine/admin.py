from django.contrib import admin
from .models import ActionDefinition

@admin.register(ActionDefinition)
class ActionDefinitionAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'method', 'endpoint_url', 'is_active')
    list_filter = ('method', 'is_active', 'organization')
    search_fields = ('name', 'endpoint_url')