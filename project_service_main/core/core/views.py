from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from customers.models import Customer
from core.models import get_current_organization

User = get_user_model()

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = get_current_organization()
        if org:
            context['total_customers'] = Customer.objects.filter(organization=org).count()
            context['total_agents'] = User.objects.filter(organization=org).count()
        else:
            context['total_customers'] = 0
            context['total_agents'] = 0
            
        context['total_calls'] = 0 # Placeholder for Phase 11
        context['ai_resolution_rate'] = "0%" # Placeholder for Phase 12
        return context
