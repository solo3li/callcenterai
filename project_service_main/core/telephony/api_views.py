import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import PhoneNumber

@csrf_exempt
def inbound_webhook(request):
    """
    Webhook endpoint for external Telephony providers (LiveKit SIP / Twilio).
    Expects a POST request with the 'To' number.
    Returns routing instructions (Room name, AI agent details, or Human queue).
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            to_number = data.get('To', '') # e.g. +1234567890
            
            # Find the number in our database
            try:
                phone_record = PhoneNumber.objects.get(number=to_number, is_active=True)
            except PhoneNumber.DoesNotExist:
                return JsonResponse({'error': 'Number not found or inactive', 'action': 'reject'}, status=404)
            
            group = phone_record.group
            if not group:
                return JsonResponse({'error': 'No routing group assigned', 'action': 'reject'}, status=400)
            
            # Routing Logic
            if group.group_type == 'AI':
                ai_agent = group.ai_agent
                if not ai_agent or not ai_agent.is_active:
                    return JsonResponse({'error': 'AI Agent unavailable', 'action': 'reject'}, status=400)
                
                # Instruct telephony provider to connect to LiveKit WebRTC room
                # and spawn the specific AI persona
                response_data = {
                    'action': 'connect_ai',
                    'room_prefix': f"org_{phone_record.organization.id}_call_",
                    'ai_config': {
                        'persona_id': ai_agent.id,
                        'voice': ai_agent.gemini_voice,
                        'language': ai_agent.language,
                        'system_prompt': ai_agent.system_prompt,
                        'temperature': ai_agent.temperature
                    }
                }
                return JsonResponse(response_data, status=200)
            
            elif group.group_type == 'HUMAN':
                # Instruct telephony provider to route to Human queue
                response_data = {
                    'action': 'connect_human',
                    'queue_id': group.id
                }
                return JsonResponse(response_data, status=200)
                
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    return JsonResponse({'error': 'Method not allowed'}, status=405)
