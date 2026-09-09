import json
import redis
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import PhoneNumber

@csrf_exempt
@require_POST
def inbound_webhook(request):
    try:
        data = json.loads(request.body)
        called_number = data.get('to_number', '')
        caller_number = data.get('from_number', '')
        
        # 1. Lookup the number
        try:
            phone_record = PhoneNumber.objects.select_related('group').get(number=called_number, is_active=True)
        except PhoneNumber.DoesNotExist:
            return JsonResponse({"action": "reject", "reason": "number_not_found"}, status=404)
            
        group = phone_record.group
        if not group:
            return JsonResponse({"action": "reject", "reason": "no_routing_group"}, status=404)
            
        # 2. Routing Logic
        if group.group_type == 'AI' and group.ai_agent:
            ai = group.ai_agent
            room_name = f"room_{caller_number.strip('+')}_{called_number.strip('+')}"
            
            # Publish to Redis for ai_worker to pick up
            r = redis.from_url(settings.REDIS_URL)
            payload = {
                "room_name": room_name,
                "caller_number": caller_number,
                "called_number": called_number,
                "system_prompt": ai.system_prompt,
                "voice": ai.gemini_voice,
                "language": ai.language,
                "temperature": ai.temperature,
            }
            r.publish("ai_call_queue", json.dumps(payload))
            
            return JsonResponse({
                "action": "join_livekit_room",
                "room_name": room_name,
                "message": "AI agent is joining the room"
            })
            
        elif group.group_type == 'HUMAN':
            return JsonResponse({
                "action": "enqueue",
                "queue_name": group.name,
                "message": "Routing to human queue"
            })
            
        return JsonResponse({"action": "reject", "reason": "invalid_group_configuration"}, status=400)
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
