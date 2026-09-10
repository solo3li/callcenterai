from django.urls import path
from . import api_views
from . import views

from inngest.django import serve
from campaigns.inngest_client import inngest_client
from .inngest_functions import analyze_transcript_workflow

urlpatterns = [
    path('api/save-transcript/', api_views.save_transcript, name='save_transcript'),
    serve(inngest_client, [analyze_transcript_workflow]),
    path('logs/', views.CallLogListView.as_view(), name='call_log_list'),
    path('logs/<int:pk>/', views.CallLogDetailView.as_view(), name='call_log_detail'),
]
