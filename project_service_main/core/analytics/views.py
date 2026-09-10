import csv
from django.views.generic import ListView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.db.models import Q, Count, Avg, Sum
from django.db.models.functions import TruncDate, TruncWeek
from django.utils import timezone
from datetime import timedelta
from .models import CallLog


class CallLogListView(LoginRequiredMixin, ListView):
    model = CallLog
    template_name = 'analytics/call_list.html'
    context_object_name = 'calls'
    paginate_by = 20

    def get_queryset(self):
        qs = CallLog.objects.filter(organization=self.request.user.organization).order_by('-start_time')
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(
                Q(phone_number__icontains=q) |
                Q(outcome__icontains=q) |
                Q(room_name__icontains=q)
            )
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
        return CallLog.objects.filter(organization=self.request.user.organization)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['events'] = self.object.events.all().order_by('timestamp')
        return context


class AnalyticsDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'analytics/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.request.user.organization
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)

        # --- Base queryset for the org's calls (last 30 days) ---
        calls = CallLog.objects.filter(organization=org, start_time__gte=thirty_days_ago)
        all_calls = CallLog.objects.filter(organization=org)

        # --- KPI Cards ---
        total_calls = all_calls.count()
        calls_this_month = calls.count()
        completed = calls.filter(status='COMPLETED').count()
        transferred = calls.filter(status='TRANSFERRED').count()
        failed = calls.filter(status='FAILED').count()
        avg_duration = calls.aggregate(avg=Avg('duration'))['avg'] or 0

        ai_resolution_rate = round((completed / calls_this_month * 100), 1) if calls_this_month > 0 else 0
        transfer_rate = round((transferred / calls_this_month * 100), 1) if calls_this_month > 0 else 0

        context['total_calls'] = total_calls
        context['calls_this_month'] = calls_this_month
        context['ai_resolution_rate'] = ai_resolution_rate
        context['transfer_rate'] = transfer_rate
        context['avg_duration'] = round(avg_duration)
        context['failed_calls'] = failed

        # --- Chart: Daily call volume (last 30 days) ---
        daily_data = (
            calls
            .annotate(day=TruncDate('start_time'))
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )
        context['chart_labels'] = [str(d['day']) for d in daily_data]
        context['chart_data'] = [d['count'] for d in daily_data]

        # --- Chart: Call Status Breakdown (pie chart) ---
        context['pie_completed'] = completed
        context['pie_transferred'] = transferred
        context['pie_failed'] = failed
        context['pie_inprogress'] = calls.filter(status='IN_PROGRESS').count()

        # --- Chart: Inbound vs Outbound ---
        context['inbound_count'] = calls.filter(direction='INBOUND').count()
        context['outbound_count'] = calls.filter(direction='OUTBOUND').count()

        # --- Chart: Top AI Agents by call count ---
        top_agents = (
            all_calls
            .filter(ai_agent__isnull=False)
            .values('ai_agent__name')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )
        context['agent_labels'] = [a['ai_agent__name'] for a in top_agents]
        context['agent_data'] = [a['count'] for a in top_agents]

        # --- Recent 5 calls ---
        context['recent_calls'] = all_calls.order_by('-start_time')[:5]

        return context


class ExportCallsCSVView(LoginRequiredMixin, ListView):
    """Export all call logs as a CSV file."""

    def get(self, request, *args, **kwargs):
        org = request.user.organization
        calls = CallLog.objects.filter(organization=org).order_by('-start_time')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="call_logs.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Phone Number', 'Direction', 'Status',
            'Duration (s)', 'Outcome', 'Sentiment', 'Tags',
            'AI Agent', 'Start Time', 'End Time'
        ])

        for call in calls:
            writer.writerow([
                call.id,
                call.phone_number,
                call.direction,
                call.status,
                call.duration,
                call.outcome,
                call.sentiment,
                ', '.join(call.tags) if call.tags else '',
                call.ai_agent.name if call.ai_agent else '',
                call.start_time.strftime('%Y-%m-%d %H:%M'),
                call.end_time.strftime('%Y-%m-%d %H:%M') if call.end_time else '',
            ])

        return response
