from django.urls import path
from . import views
from . import api_views

urlpatterns = [
    path('', views.AgentListView.as_view(), name='agent_list'),
    path('new/', views.AgentCreateView.as_view(), name='agent_create'),
    path('<int:pk>/edit/', views.AgentUpdateView.as_view(), name='agent_update'),
    path('<int:pk>/delete/', views.AgentDeleteView.as_view(), name='agent_delete'),
    
    # Groups
    path('groups/', views.AgentGroupListView.as_view(), name='agent_group_list'),
    path('groups/new/', views.AgentGroupCreateView.as_view(), name='agent_group_create'),
    path('groups/<int:pk>/edit/', views.AgentGroupUpdateView.as_view(), name='agent_group_update'),
    path('groups/<int:pk>/delete/', views.AgentGroupDeleteView.as_view(), name='agent_group_delete'),

    # AI Agents
    path('ai-agents/', views.AIAgentListView.as_view(), name='ai_agent_list'),
    path('ai-agents/new/', views.AIAgentCreateView.as_view(), name='ai_agent_create'),
    path('ai-agents/<int:pk>/edit/', views.AIAgentUpdateView.as_view(), name='ai_agent_update'),
    path('ai-agents/<int:pk>/delete/', views.AIAgentDeleteView.as_view(), name='ai_agent_delete'),

    # API endpoints for Human Support (Phase 5)
    path('api/me/state/', api_views.AgentStateAPIView.as_view(), name='api_agent_state'),
    path('api/transfer/', api_views.TransferCallAPIView.as_view(), name='api_agent_transfer'),
]
