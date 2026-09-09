from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import AgentProfile, AgentGroup
from core.centrifugo_client import publish
import logging

logger = logging.getLogger(__name__)

class AgentStateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, _ = AgentProfile.objects.get_or_create(user=request.user)
        # Mocking analytics data for the dashboard chart
        analytics = {
            "calls_today": 12,
            "avg_handle_time_mins": 4.5,
            "calls_this_week": [10, 15, 8, 12, 0, 0, 0] # Mon-Sun
        }
        return Response({
            "user_id": request.user.id,
            "state": profile.state,
            "last_state_change": profile.last_state_change,
            "analytics": analytics
        })

    def patch(self, request):
        profile, _ = AgentProfile.objects.get_or_create(user=request.user)
        new_state = request.data.get('state')
        if new_state in [choice[0] for choice in AgentProfile._meta.get_field('state').choices]:
            profile.state = new_state
            profile.last_state_change = timezone.now()
            profile.save()
            return Response({"state": profile.state})
        return Response({"error": "Invalid state"}, status=status.HTTP_400_BAD_REQUEST)

class TransferCallAPIView(APIView):
    # Depending on how the AI service calls this, it could be authenticated via a service token.
    # We will use AllowAny for the prototype but it should be restricted.
    permission_classes = [] 

    def post(self, request):
        group_id = request.data.get('group_id')
        summary = request.data.get('summary', 'No summary provided')
        caller_id = request.data.get('caller_id', 'Unknown')
        
        if not group_id:
            return Response({"error": "group_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            group = AgentGroup.objects.get(id=group_id)
        except AgentGroup.DoesNotExist:
            return Response({"error": "Group not found"}, status=status.HTTP_404_NOT_FOUND)

        # Find longest idle available agent
        available_agents = AgentProfile.objects.filter(
            user__agent_groups=group,
            state='AVAILABLE'
        ).order_by('last_state_change')

        agent = available_agents.first()

        if not agent:
            return Response({
                "status": "failed",
                "reason": "no_agents_available"
            }, status=status.HTTP_200_OK) # returning 200 so AI can handle gracefully
            
        # Agent found! Reserve them and notify
        agent.state = 'BUSY'
        agent.last_state_change = timezone.now()
        agent.save()
        
        # Publish to centrifugo
        channel = f"agent:user_{agent.user.id}"
        event_data = {
            "type": "incoming_transfer",
            "caller_id": caller_id,
            "summary": summary
        }
        publish(channel, event_data)
        
        return Response({
            "status": "success",
            "assigned_agent": agent.user.username,
            "agent_id": agent.user.id
        })
