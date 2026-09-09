from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .models import ActionDefinition
from .executor import execute_action
from agents.models import AIAgent

class InternalAuthMixin:
    def validate_key(self, request):
        api_key = request.headers.get('Authorization')
        if not api_key or api_key != f"Bearer {settings.INTERNAL_API_KEY}":
            return False
        return True

class ActionDefinitionListView(APIView, InternalAuthMixin):
    """
    Returns all allowed actions and their JSON schemas for a specific AI Agent.
    Used by Pipecat to register tools dynamically.
    """
    def get(self, request):
        if not self.validate_key(request):
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
            
        agent_id = request.query_params.get('agent_id')
        if not agent_id:
            return Response({"error": "agent_id required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            agent = AIAgent.objects.get(id=agent_id)
        except AIAgent.DoesNotExist:
            return Response({"error": "Agent not found"}, status=status.HTTP_404_NOT_FOUND)
            
        actions = agent.actions.all()
        
        result = []
        for act in actions:
            result.append({
                "id": act.id,
                "name": act.name,
                "description": act.description,
                "input_schema": act.input_schema
            })
            
        return Response({"actions": result})

class ActionExecuteView(APIView, InternalAuthMixin):
    """
    Executes a specific action securely from the backend.
    """
    def post(self, request):
        if not self.validate_key(request):
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
            
        action_name = request.data.get('action_name')
        agent_id = request.data.get('agent_id')
        params = request.data.get('params', {})
        
        try:
            agent = AIAgent.objects.get(id=agent_id)
            action = agent.actions.get(name=action_name)
        except (AIAgent.DoesNotExist, ActionDefinition.DoesNotExist):
            return Response({"error": "Action not permitted for this agent."}, status=status.HTTP_403_FORBIDDEN)
            
        # Execute it
        result_text = execute_action(action, params)
        
        return Response({"result": result_text})
