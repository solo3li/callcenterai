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
                "type": "custom_action",
                "id": act.id,
                "name": act.name,
                "description": act.description,
                "input_schema": act.input_schema
            })
            
        workflows = agent.workflows.filter(trigger_type='MID_CALL', is_active=True)
        for wf in workflows:
            result.append({
                "type": "n8n_workflow",
                "id": wf.id,
                # Sanitize name for Gemini function name constraints (alphanumeric and underscores only)
                "name": f"workflow_{wf.name.replace(' ', '_').replace('-', '_').lower()}",
                "description": wf.description or "Triggers a background workflow process.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "instructions": {
                            "type": "string",
                            "description": "Any extracted instructions or variables the workflow might need"
                        }
                    }
                }
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
        
        action_type = request.data.get('type', 'custom_action')
        
        if action_type == 'n8n_workflow':
            try:
                agent = AIAgent.objects.get(id=agent_id)
                workflow_id = request.data.get('action_id') # We should pass ID to be safe
                wf = agent.workflows.get(id=workflow_id, trigger_type='MID_CALL')
                
                # Execute n8n webhook
                if wf.webhook_url:
                    import requests
                    resp = requests.post(wf.webhook_url, json=params, timeout=10)
                    resp.raise_for_status()
                    result_text = f"Workflow completed. Result: {resp.text}"
                else:
                    result_text = "Workflow URL not configured."
            except Exception as e:
                result_text = f"Workflow failed: {str(e)}"
                
        else:
            try:
                agent = AIAgent.objects.get(id=agent_id)
                action = agent.actions.get(name=action_name)
            except (AIAgent.DoesNotExist, ActionDefinition.DoesNotExist):
                return Response({"error": "Action not permitted for this agent."}, status=status.HTTP_403_FORBIDDEN)
                
            # Execute custom action
            result_text = execute_action(action, params)
        
        return Response({"result": result_text})
