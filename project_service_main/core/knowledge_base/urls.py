from django.urls import path
from . import views

urlpatterns = [
    path('', views.KnowledgeDocumentListView.as_view(), name='knowledge_document_list'),
    path('new/', views.KnowledgeDocumentCreateView.as_view(), name='knowledge_document_create'),
    path('<int:pk>/delete/', views.KnowledgeDocumentDeleteView.as_view(), name='knowledge_document_delete'),
]
