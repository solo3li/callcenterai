"""
usage_tracker.py
================
Single public function: record_usage(org, usage_type, amount, **kwargs)

Called from:
  - analytics/signals.py  → after a CallLog is saved with an end_time
  - knowledge_base/signals.py → after a document is processed
  - workflows/signals.py  → after a workflow execution is logged
  - actions_engine/api_views.py → after an action is executed (RAG query)
"""

from .models import UsageRecord


def record_usage(organization, usage_type, amount, call_log=None, description=''):
    """
    Create a UsageRecord row for `organization`.

    :param organization: Organization instance
    :param usage_type:   One of UsageRecord.USAGE_TYPES keys
    :param amount:       Float value (seconds / MB / count)
    :param call_log:     Optional CallLog FK
    :param description:  Human-readable note
    """
    UsageRecord.objects.create(
        organization=organization,
        usage_type=usage_type,
        amount=amount,
        call_log=call_log,
        description=description,
    )
