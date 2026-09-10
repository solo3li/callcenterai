from django.urls import path
from . import views
from . import api_views

urlpatterns = [
    # UI Views
    path('', views.WorkflowListView.as_view(), name='workflow_list'),
    path('builder/', views.WorkflowBuilderView.as_view(), name='workflow_builder'),
    path('new/', views.WorkflowCreateView.as_view(), name='workflow_create'),
    path('<int:pk>/edit/', views.WorkflowUpdateView.as_view(), name='workflow_update'),
    path('<int:pk>/delete/', views.WorkflowDeleteView.as_view(), name='workflow_delete'),
    
    # API Views for the Builder
    path('api/integrations/', api_views.IntegrationsListView.as_view(), name='api_integrations_list'),
    path('api/deploy/', api_views.DeployWorkflowView.as_view(), name='api_deploy_workflow'),
]
