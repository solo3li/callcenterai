import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from analytics.models import CallLog
from campaigns.inngest_client import inngest_client

class LiveKitEgressWebhookView(APIView):
    permission_classes = [AllowAny] # Ideally secure with LiveKit API Secret

    def post(self, request):
        # Webhook payload from LiveKit Egress
        data = request.data
        
        # Determine if it's an egress completion event
        event_type = data.get('event')
        
        if event_type == 'egress_ended':
            egress_info = data.get('egress', {})
            status = egress_info.get('status')
            
            if status == 3: # 3 means EGRESS_COMPLETE in LiveKit protobuf
                room_name = egress_info.get('roomName')
                
                # Get the uploaded file info
                file_results = egress_info.get('fileResults', [])
                
                if room_name and file_results:
                    # In our architecture, we assume 3 egresses are fired per room:
                    # 1. Composite (mixed)
                    # 2. Agent Track
                    # 3. Customer Track
                    # To process them efficiently, we wait for all 3, but in a real scenario,
                    # we trigger the workflow which will check MinIO for the 3 files.
                    
                    # Send to Inngest Background Worker
                    inngest_client.send_sync({
                        "name": "analytics/process_recording",
                        "data": {
                            "room_name": room_name,
                            "egress_id": egress_info.get('egressId')
                        }
                    })
                    
        return Response({"status": "received"})
