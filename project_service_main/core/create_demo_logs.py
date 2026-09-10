import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'callcenter_project.settings')
django.setup()

from analytics.models import CallLog, CallEvent
from organizations.models import Organization
from users.models import User
from django.utils import timezone
import datetime

org = Organization.objects.first()
user = User.objects.first()

if org:
    c = CallLog.objects.create(
        organization=org,
        room_name='demo-room-1',
        phone_number='+14155552671',
        direction='INBOUND',
        status='COMPLETED',
        duration=124,
        transcript="Agent: Hello, how can I help you today?\\nUser: I need to check my order status.\\nAgent: Sure, can I have your order number?\\nUser: It is 12345.\\nAgent: Your order is on the way. Is there anything else?\\nUser: No, thanks.\\nAgent: Goodbye!",
        summary="Customer checked the status of order 12345. Order was confirmed to be on the way.",
        sentiment="Positive",
        outcome="Order Status Checked",
        start_time=timezone.now() - datetime.timedelta(hours=2)
    )
    CallEvent.objects.create(call=c, event_type='AI_START', description='AI agent connected to audio stream', timestamp=timezone.now() - datetime.timedelta(hours=2, seconds=-2))
    CallEvent.objects.create(call=c, event_type='TOOL_CALL', description='Called get_order_status', metadata={'order_id': '12345'}, timestamp=timezone.now() - datetime.timedelta(hours=2, seconds=-45))
    CallEvent.objects.create(call=c, event_type='CALL_END', description='Customer disconnected', timestamp=timezone.now() - datetime.timedelta(hours=2, minutes=-2, seconds=-4))

    CallLog.objects.create(
        organization=org,
        room_name='demo-room-2',
        phone_number='+447712345678',
        direction='OUTBOUND',
        status='TRANSFERRED',
        duration=340,
        transcript="Agent: Hi, this is Acme Corp calling about your invoice.\\nUser: I am very angry, I want to speak to a manager!\\nAgent: I understand you are frustrated, let me transfer you.",
        summary="Customer was angry about an invoice. Escalated and transferred to human agent.",
        sentiment="Negative",
        outcome="Transferred to human",
        start_time=timezone.now() - datetime.timedelta(days=1)
    )
print('Demo logs created')
