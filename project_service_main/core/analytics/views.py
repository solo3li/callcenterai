from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import CallLog
from django.db.models import Q

class CallLogListView(LoginRequiredMixin, ListView):
    model = CallLog
    template_name = 'analytics/call_list.html'
    context_object_name = 'calls'
    paginate_by = 20

    def get_queryset(self):
        qs = CallLog.objects.filter(organization=self.request.user.organization).order_by('-start_time')
        
        # Simple search
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(
                Q(phone_number__icontains=q) | 
                Q(outcome__icontains=q) |
                Q(room_name__icontains=q)
            )
            
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
            
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_q'] = self.request.GET.get('q', '')
        context['status_filter'] = self.request.GET.get('status', '')
        return context

class CallLogDetailView(LoginRequiredMixin, DetailView):
    model = CallLog
    template_name = 'analytics/call_detail.html'
    context_object_name = 'call'

    def get_queryset(self):
        # Ensure users can only view calls from their own organization
        return CallLog.objects.filter(organization=self.request.user.organization)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass the related events ordered by timestamp
        context['events'] = self.object.events.all().order_by('timestamp')
        return context
