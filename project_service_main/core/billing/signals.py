"""
signals.py — auto-record usage whenever key events happen.
Registered in billing/apps.py → ready()
"""

from django.db.models.signals import post_save
from django.dispatch import receiver


# ─── 1. Call ends → record AI minutes + SIP minutes ───────────────────────────
@receiver(post_save, sender='analytics.CallLog')
def on_call_log_saved(sender, instance, created, **kwargs):
    """
    When a CallLog is saved with a positive duration we record:
      • AI_MINUTES  – if an AI agent handled it
      • SIP_MINUTES – always (telephony cost)
    We guard with `instance.duration > 0` to avoid double-recording.
    """
    from .usage_tracker import record_usage

    if instance.duration and instance.duration > 0:
        org = instance.organization

        # Convert seconds → minutes (float)
        minutes = round(instance.duration / 60, 4)

        # SIP minutes (always)
        record_usage(
            organization=org,
            usage_type='SIP_MINUTES',
            amount=minutes,
            call_log=instance,
            description=f"Call {instance.room_name} — {instance.phone_number}",
        )

        # AI minutes (only if an AI agent was involved)
        if instance.ai_agent_id:
            record_usage(
                organization=org,
                usage_type='AI_MINUTES',
                amount=minutes,
                call_log=instance,
                description=f"AI Agent: {instance.ai_agent}",
            )


# ─── 2. Knowledge document processed → record storage MB ──────────────────────
@receiver(post_save, sender='knowledge_base.KnowledgeDocument')
def on_document_saved(sender, instance, created, **kwargs):
    """Record storage usage when a new document is uploaded."""
    from .usage_tracker import record_usage

    if created and instance.document_file:
        try:
            size_mb = round(instance.document_file.size / (1024 * 1024), 4)
            record_usage(
                organization=instance.organization,
                usage_type='STORAGE_MB',
                amount=size_mb,
                description=f"Document: {instance.title}",
            )
        except Exception:
            pass  # file may not exist on disk yet


# ─── 3. Workflow deployed → record execution ──────────────────────────────────
@receiver(post_save, sender='workflows.Workflow')
def on_workflow_created(sender, instance, created, **kwargs):
    """Record 1 execution unit whenever a new workflow is created/deployed."""
    from .usage_tracker import record_usage

    if created:
        record_usage(
            organization=instance.organization,
            usage_type='WORKFLOW_EXECUTIONS',
            amount=1,
            description=f"Workflow deployed: {instance.name}",
        )
