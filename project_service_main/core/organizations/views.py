from django.urls import reverse_lazy
from django.views.generic import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import OrganizationSettings
from core.models import get_current_organization

class SettingsUpdateView(LoginRequiredMixin, UpdateView):
    model = OrganizationSettings
    fields = ['timezone', 'ai_greeting']
    template_name = 'organizations/settings_form.html'
    success_url = reverse_lazy('settings_update')

    def get_object(self, queryset=None):
        org = get_current_organization()
        # Ensure the settings object exists
        settings, _ = OrganizationSettings.objects.get_or_create(organization=org)
        return settings
