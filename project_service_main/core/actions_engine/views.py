from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import ActionDefinition

class ActionDefinitionListView(LoginRequiredMixin, ListView):
    model = ActionDefinition
    template_name = 'actions_engine/action_list.html'
    context_object_name = 'actions'

    def get_queryset(self):
        return ActionDefinition.objects.filter(organization=self.request.user.organization)

class ActionDefinitionCreateView(LoginRequiredMixin, CreateView):
    model = ActionDefinition
    template_name = 'actions_engine/action_form.html'
    fields = [
        'name', 'description', 'protocol', 'version', 
        'endpoint_url', 'http_method', 'headers', 
        'body_template', 'input_schema', 'response_extractor', 
        'timeout_seconds', 'retry_count'
    ]
    success_url = reverse_lazy('action_definition_list')

    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        return super().form_valid(form)

class ActionDefinitionUpdateView(LoginRequiredMixin, UpdateView):
    model = ActionDefinition
    template_name = 'actions_engine/action_form.html'
    fields = [
        'name', 'description', 'protocol', 'version', 
        'endpoint_url', 'http_method', 'headers', 
        'body_template', 'input_schema', 'response_extractor', 
        'timeout_seconds', 'retry_count'
    ]
    success_url = reverse_lazy('action_definition_list')

    def get_queryset(self):
        return ActionDefinition.objects.filter(organization=self.request.user.organization)

class ActionDefinitionDeleteView(LoginRequiredMixin, DeleteView):
    model = ActionDefinition
    template_name = 'actions_engine/action_confirm_delete.html'
    success_url = reverse_lazy('action_definition_list')

    def get_queryset(self):
        return ActionDefinition.objects.filter(organization=self.request.user.organization)
