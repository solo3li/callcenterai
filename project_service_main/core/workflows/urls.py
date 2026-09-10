from django.urls import path
from . import views

urlpatterns = [
    path('', views.WorkflowListView.as_view(), name='workflow_list'),
    path('builder/', views.WorkflowBuilderView.as_view(), name='workflow_builder'),
    path('new/', views.WorkflowCreateView.as_view(), name='workflow_create'),
    path('<int:pk>/edit/', views.WorkflowUpdateView.as_view(), name='workflow_update'),
    path('<int:pk>/delete/', views.WorkflowDeleteView.as_view(), name='workflow_delete'),
]
