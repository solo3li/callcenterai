import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import CallLog

@csrf_exempt
def save_transcript(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            room_name = data.get("room_name")
            transcript = data.get("transcript")
            agent_id = data.get("agent_id") # To link to POST_CALL workflows

            if not room_name or not transcript:
                return JsonResponse({"error": "Missing room_name or transcript"}, status=400)

            log, created = CallLog.objects.get_or_create(
                room_name=room_name,
                defaults={"direction": "OUTBOUND"}
            )
            log.transcript = transcript
            log.save()
            
            # Send an event to Inngest to analyze the transcript using Gemini!
            from inngest import Event
            from campaigns.inngest_client import inngest_client
            
            inngest_client.send_sync(
                Event(
                    name="analytics/analyze_transcript",
                    data={
                        "call_log_id": log.id,
                        "agent_id": agent_id
                    }
                )
            )

            return JsonResponse({"status": "success", "id": log.id})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)
