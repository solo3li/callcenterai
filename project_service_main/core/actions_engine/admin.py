from django.contrib import admin
from .models import ActionDefinition

@admin.register(ActionDefinition)
class ActionDefinitionAdmin(admin.ModelAdmin):
    pass