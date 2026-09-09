import jwt
import time
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.conf import settings
from django.utils import timezone
from .models import AgentProfile

class CentrifugoTokenAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Generate a JWT for Centrifugo. The subject (sub) must be the user ID as string.
        payload = {
            "sub": str(request.user.id),
            "exp": int(time.time()) + 24 * 3600  # Token expires in 24 hours
        }
        token = jwt.encode(payload, settings.CENTRIFUGO_SECRET, algorithm="HS256")
        return Response({"token": token})

class CentrifugoDisconnectWebhookAPIView(APIView):
    permission_classes = [AllowAny] # Webhook called by Centrifugo
    
    def post(self, request):
        user_id = request.data.get("user")
        if user_id:
            try:
                profile = AgentProfile.objects.get(user__id=user_id)
                profile.state = 'OFFLINE'
                profile.last_state_change = timezone.now()
                profile.save()
            except AgentProfile.DoesNotExist:
                pass
                
        return Response({}) # Empty JSON {} confirms receipt to Centrifugo
