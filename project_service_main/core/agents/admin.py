from django.contrib import admin
from .models import AgentGroup, AIAgent, AgentProfile

@admin.register(AgentGroup)
class AgentGroupAdmin(admin.ModelAdmin):
    pass

@admin.register(AIAgent)
class AIAgentAdmin(admin.ModelAdmin):
    pass

@admin.register(AgentProfile)
class AgentProfileAdmin(admin.ModelAdmin):
    pass