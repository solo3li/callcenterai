from django.contrib import admin
from .models import AIAgent, AgentGroup, AgentProfile

@admin.register(AIAgent)
class AIAgentAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'language', 'gemini_voice', 'is_active', 'created_at')
    list_filter = ('is_active', 'language', 'gemini_voice', 'organization')
    search_fields = ('name',)
    filter_horizontal = ('knowledge_documents', 'actions', 'workflows')

@admin.register(AgentGroup)
class AgentGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'group_type', 'ai_agent')
    list_filter = ('group_type', 'organization')
    search_fields = ('name',)

@admin.register(AgentProfile)
class AgentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'state', 'last_state_change')
    list_filter = ('state',)