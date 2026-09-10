import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'callcenter_project.settings')
django.setup()

from analytics.models import CallLog

# Update existing demo calls to add tags
calls = CallLog.objects.all()
tags_map = ['Order Inquiry', 'Complaint', 'Sales', 'Technical Support', 'Billing', 'Account Management']
import random
for i, call in enumerate(calls):
    call.tags = random.sample(tags_map, 2)
    call.save()

print(f'Updated {calls.count()} calls with tags')
