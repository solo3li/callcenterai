from django.views.generic import ListView, CreateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import KnowledgeDocument

class KnowledgeDocumentListView(LoginRequiredMixin, ListView):
    model = KnowledgeDocument
    template_name = 'knowledge_base/document_list.html'
    context_object_name = 'documents'

    def get_queryset(self):
        return KnowledgeDocument.objects.filter(organization=self.request.user.organization)

class KnowledgeDocumentCreateView(LoginRequiredMixin, CreateView):
    model = KnowledgeDocument
    template_name = 'knowledge_base/document_form.html'
    fields = ['title', 'file_url', 'document_file']
    success_url = reverse_lazy('knowledge_document_list')

    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        # In a real scenario, you would upload the local file to MinIO here, 
        # and set form.instance.file_url = minio_url.
        # For simplicity, we are accepting the URL directly in this UI mockup.
        return super().form_valid(form)

class KnowledgeDocumentDeleteView(LoginRequiredMixin, DeleteView):
    model = KnowledgeDocument
    template_name = 'knowledge_base/document_confirm_delete.html'
    success_url = reverse_lazy('knowledge_document_list')

    def get_queryset(self):
        return KnowledgeDocument.objects.filter(organization=self.request.user.organization)
