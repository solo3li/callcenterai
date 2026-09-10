from django.db import models
from core.models import TenantAwareModel


class UsageRecord(TenantAwareModel):
    """
    Each row records one usage event for an organization.
    Aggregated queries on this table power the Usage Dashboard.
    """

    USAGE_TYPES = (
        ('AI_MINUTES',          'AI Minutes'),
        ('SIP_MINUTES',         'SIP / PSTN Minutes'),
        ('STORAGE_MB',          'Storage (MB)'),
        ('RAG_QUERIES',         'RAG / Knowledge Queries'),
        ('WORKFLOW_EXECUTIONS', 'Workflow Executions (n8n)'),
    )

    usage_type  = models.CharField(max_length=30, choices=USAGE_TYPES, db_index=True)
    amount      = models.FloatField(help_text="Unit depends on usage_type (seconds, MB, count …)")
    recorded_at = models.DateTimeField(auto_now_add=True, db_index=True)

    # Optional back-references so we can drill down
    call_log    = models.ForeignKey(
        'analytics.CallLog',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='usage_records',
    )
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-recorded_at']

    def __str__(self):
        return f"{self.get_usage_type_display()} | {self.amount} | {self.recorded_at:%Y-%m-%d}"
