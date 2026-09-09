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

@csrf_exempt
@require_POST
def livekit_webhook(request):
    """
    Receives webhooks from LiveKit Server (e.g. participant_joined, participant_left).
    Updates CampaignLead status and publishes to Centrifugo for Real-time UI.
    """
    try:
        # In production, verify LiveKit Webhook signature using `livekit_api.WebhookReceiver`
        data = json.loads(request.body)
        event = data.get('event')
        room = data.get('room', {})
        participant = data.get('participant', {})
        
        room_name = room.get('name', '')
        
        # We only care about outbound campaign rooms
        if room_name.startswith('outbound_'):
            parts = room_name.split('_')
            if len(parts) >= 3:
                campaign_id = parts[1]
                lead_id = parts[2]
                
                from campaigns.models import CampaignLead
                from cent import Client
                
                try:
                    lead = CampaignLead.objects.get(id=lead_id)
                except CampaignLead.DoesNotExist:
                    return JsonResponse({"status": "ignored", "reason": "lead_not_found"})
                
                new_status = None
                
                # Assume the SIP participant connects and triggers participant_joined
                if event == 'participant_joined' and participant.get('identity', '').startswith('sip_'):
                    new_status = 'ANSWERED'
                elif event == 'participant_left' and participant.get('identity', '').startswith('sip_'):
                    new_status = 'COMPLETED'
                elif event == 'room_finished':
                    # If room finishes and lead wasn't answered, it failed
                    if lead.status != 'ANSWERED' and lead.status != 'COMPLETED':
                        new_status = 'FAILED'
                        
                if new_status:
                    lead.status = new_status
                    lead.save()
                    
                    # Publish to Centrifugo
                    cent_client = Client(settings.CENTRIFUGO_URL, api_key=settings.CENTRIFUGO_API_KEY)
                    channel = f"campaign_{campaign_id}"
                    payload = {
                        "lead_id": lead.id,
                        "status": new_status
                    }
                    cent_client.publish(channel, payload)
                    
        if event == 'egress_ended':
            egress_info = data.get('egressInfo', data.get('egress', {}))
            status = egress_info.get('status')
            
            if status == 3: # EGRESS_COMPLETE
                room_name = egress_info.get('roomName')
                file_results = egress_info.get('fileResults', [])
                
                if room_name and file_results:
                    from campaigns.inngest_client import inngest_client
                    inngest_client.send_sync({
                        "name": "analytics/process_recording",
                        "data": {
                            "room_name": room_name,
                            "egress_id": egress_info.get('egressId'),
                            "files": [f.get('filename') for f in file_results]
                        }
                    })
                    
        return JsonResponse({"status": "ok"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
