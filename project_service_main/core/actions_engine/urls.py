from django.urls import path
from . import api_views
from . import views

urlpatterns = [
    # API endpoints for Pipecat AI worker
    path('api/internal/actions/', api_views.ActionDefinitionListView.as_view(), name='internal_actions_list'),
    path('api/internal/actions/execute/', api_views.ActionExecuteView.as_view(), name='internal_actions_execute'),
    
    # Dashboard UI endpoints
    path('', views.ActionDefinitionListView.as_view(), name='action_definition_list'),
    path('new/', views.ActionDefinitionCreateView.as_view(), name='action_definition_create'),
    path('<int:pk>/edit/', views.ActionDefinitionUpdateView.as_view(), name='action_definition_update'),
    path('<int:pk>/delete/', views.ActionDefinitionDeleteView.as_view(), name='action_definition_delete'),
]
