from django.urls import path
from . import api_views

urlpatterns = [
    path('api/internal/actions/', api_views.ActionDefinitionListView.as_view(), name='internal_actions_list'),
    path('api/internal/actions/execute/', api_views.ActionExecuteView.as_view(), name='internal_actions_execute'),
]
