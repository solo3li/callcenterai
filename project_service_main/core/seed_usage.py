import os, django, datetime, random
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'callcenter_project.settings')
django.setup()

from billing.usage_tracker import record_usage
from analytics.models import CallLog
from organizations.models import Organization
from django.utils import timezone

org = Organization.objects.first()
if not org:
    print('No org found')
    exit()

calls = CallLog.objects.filter(organization=org)

# Back-fill usage for existing calls
for call in calls:
    mins = round(call.duration / 60, 4)
    record_usage(org, 'SIP_MINUTES', mins, call_log=call, description=f'Call {call.phone_number}')
    if call.ai_agent_id:
        record_usage(org, 'AI_MINUTES', mins, call_log=call, description=f'AI: {call.ai_agent}')

# Seed some extra data for chart variety
base = timezone.now()
for i in range(25):
    day_offset = random.randint(0, 28)
    dt = base - datetime.timedelta(days=day_offset, minutes=random.randint(0, 1440))
    mins = round(random.uniform(1, 15), 2)
    r = record_usage(org, 'AI_MINUTES', mins, description=f'Demo call #{i}')

record_usage(org, 'STORAGE_MB',          5.2,  description='knowledge.pdf')
record_usage(org, 'STORAGE_MB',          1.8,  description='product_manual.docx')
record_usage(org, 'RAG_QUERIES',         37,   description='Knowledge base lookups')
record_usage(org, 'WORKFLOW_EXECUTIONS', 4,    description='n8n workflows deployed')

print('Demo usage data seeded OK')
