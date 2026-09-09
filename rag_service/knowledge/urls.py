from django.urls import path
from . import api_views

urlpatterns = [
    path('api/documents/', api_views.DocumentUploadView.as_view(), name='document_upload'),
    path('api/documents/<int:doc_id>/', api_views.DocumentDeleteView.as_view(), name='document_delete'),
    path('api/retrieve/', api_views.RetrieveKnowledgeView.as_view(), name='knowledge_retrieve'),
]
