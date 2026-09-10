from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta

from .models import UsageRecord


class UsageDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'billing/usage_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.request.user.organization
        now = timezone.now()

        # ── Period from URL param (default: 30 days) ──────────────────────────
        period = int(self.request.GET.get('period', 30))
        since  = now - timedelta(days=period)

        qs = UsageRecord.objects.filter(organization=org, recorded_at__gte=since)

        # ── Summary totals ─────────────────────────────────────────────────────
        def total(usage_type):
            return qs.filter(usage_type=usage_type).aggregate(s=Sum('amount'))['s'] or 0

        context['period']          = period
        context['ai_minutes']      = round(total('AI_MINUTES'), 2)
        context['sip_minutes']     = round(total('SIP_MINUTES'), 2)
        context['storage_mb']      = round(total('STORAGE_MB'), 2)
        context['rag_queries']     = int(total('RAG_QUERIES'))
        context['wf_executions']   = int(total('WORKFLOW_EXECUTIONS'))

        # ── Daily AI-minutes trend (for line chart) ────────────────────────────
        daily_ai = (
            qs.filter(usage_type='AI_MINUTES')
            .annotate(day=TruncDate('recorded_at'))
            .values('day')
            .annotate(total=Sum('amount'))
            .order_by('day')
        )
        context['trend_labels'] = [str(d['day']) for d in daily_ai]
        context['trend_data']   = [round(d['total'], 2) for d in daily_ai]

        # ── Usage type breakdown for doughnut chart ───────────────────────────
        breakdown = (
            qs.values('usage_type')
            .annotate(total=Sum('amount'))
            .order_by('-total')
        )
        type_labels = {k: v for k, v in UsageRecord.USAGE_TYPES}
        context['breakdown_labels'] = [type_labels.get(b['usage_type'], b['usage_type']) for b in breakdown]
        context['breakdown_data']   = [round(b['total'], 2) for b in breakdown]

        # ── Recent 20 events log ──────────────────────────────────────────────
        context['recent_events'] = qs.select_related('call_log').order_by('-recorded_at')[:20]

        return context
