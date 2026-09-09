from django.urls import path
from inngest.django import serve
from .inngest_client import inngest_client
from .inngest_functions import run_campaign_workflow, dial_lead_workflow
from . import views

urlpatterns = [
    path('', views.CampaignListView.as_view(), name='campaign-list'),
    path('create/', views.CampaignCreateView.as_view(), name='campaign-create'),
    path('<int:pk>/', views.CampaignDetailView.as_view(), name='campaign-detail'),
    path('<int:pk>/start/', views.start_campaign, name='campaign-start'),
    path('<int:pk>/upload-leads/', views.upload_leads, name='campaign-upload-leads'),
    serve(inngest_client, [run_campaign_workflow, dial_lead_workflow]),
]
