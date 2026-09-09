from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from core.models import get_current_organization
from .models import PhoneNumber

class PhoneNumberListView(LoginRequiredMixin, ListView):
    model = PhoneNumber
    template_name = 'telephony/phone_number_list.html'
    context_object_name = 'phone_numbers'

class PhoneNumberCreateView(LoginRequiredMixin, CreateView):
    model = PhoneNumber
    fields = ['number', 'group', 'is_active']
    template_name = 'telephony/phone_number_form.html'
    success_url = reverse_lazy('phone_number_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        org = get_current_organization()
        from agents.models import AgentGroup
        if org:
            form.fields['group'].queryset = AgentGroup.objects.filter(organization=org)
        else:
            form.fields['group'].queryset = AgentGroup.objects.none()
        return form

class PhoneNumberUpdateView(LoginRequiredMixin, UpdateView):
    model = PhoneNumber
    fields = ['number', 'group', 'is_active']
    template_name = 'telephony/phone_number_form.html'
    success_url = reverse_lazy('phone_number_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        org = get_current_organization()
        from agents.models import AgentGroup
        if org:
            form.fields['group'].queryset = AgentGroup.objects.filter(organization=org)
        else:
            form.fields['group'].queryset = AgentGroup.objects.none()
        return form

class PhoneNumberDeleteView(LoginRequiredMixin, DeleteView):
    model = PhoneNumber
    template_name = 'telephony/phone_number_confirm_delete.html'
    success_url = reverse_lazy('phone_number_list')
