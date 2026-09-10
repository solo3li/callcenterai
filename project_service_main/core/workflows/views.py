from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Workflow, WorkflowCredential

class WorkflowListView(LoginRequiredMixin, ListView):
    model = Workflow
    template_name = 'workflows/workflow_list.html'
    context_object_name = 'workflows'

    def get_queryset(self):
        return Workflow.objects.filter(organization=self.request.user.organization)

from django.views.generic import TemplateView
class WorkflowBuilderView(LoginRequiredMixin, TemplateView):
    template_name = 'workflows/workflow_builder.html'

class WorkflowCreateView(LoginRequiredMixin, CreateView):
    model = Workflow
    template_name = 'workflows/workflow_form.html'
    fields = ['name', 'description', 'trigger_type', 'webhook_url', 'is_active']
    success_url = reverse_lazy('workflow_list')

    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        return super().form_valid(form)

class WorkflowUpdateView(LoginRequiredMixin, UpdateView):
    model = Workflow
    template_name = 'workflows/workflow_form.html'
    fields = ['name', 'description', 'trigger_type', 'webhook_url', 'is_active']
    success_url = reverse_lazy('workflow_list')

    def get_queryset(self):
        return Workflow.objects.filter(organization=self.request.user.organization)

class WorkflowDeleteView(LoginRequiredMixin, DeleteView):
    model = Workflow
    template_name = 'workflows/workflow_confirm_delete.html'
    success_url = reverse_lazy('workflow_list')

    def get_queryset(self):
        return Workflow.objects.filter(organization=self.request.user.organization)
