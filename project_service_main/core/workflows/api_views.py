import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.mixins import LoginRequiredMixin
from .integrations import CURATED_INTEGRATIONS
from .models import Workflow
from .n8n_client import N8NClient

class IntegrationsListView(APIView):
    """
    Returns the curated list of integrations for the frontend builder.
    """
    def get(self, request):
        # We don't need to return n8n_mapping to the frontend, just the UI schema
        sanitized_integrations = []
        for integration in CURATED_INTEGRATIONS:
            sanitized = {
                "id": integration["id"],
                "name": integration["name"],
                "icon": integration["icon"],
                "color": integration["color"],
                "description": integration["description"],
                "fields": integration["fields"]
            }
            sanitized_integrations.append(sanitized)
            
        return Response(sanitized_integrations)

class DeployWorkflowView(APIView):
    """
    Receives the simplified visual workflow from the frontend,
    translates it to n8n JSON format, and deploys it.
    """
    def post(self, request):
        nodes = request.data.get('nodes', [])
        trigger_type = request.data.get('trigger_type', 'POST_CALL')
        
        if not nodes:
            return Response({"error": "No nodes provided"}, status=status.HTTP_400_BAD_REQUEST)
            
        # 1. Translate our linear nodes to n8n nodes format
        n8n_nodes = []
        n8n_connections = {"main": [[]]} # Linear workflow connection structure
        
        # Build the Webhook Trigger node (entry point)
        webhook_node = {
            "parameters": {
                "httpMethod": "POST",
                "path": f"ai_trigger_{trigger_type.lower()}",
                "responseMode": "onReceived",
                "options": {}
            },
            "name": "AI Trigger",
            "type": "n8n-nodes-base.webhook",
            "typeVersion": 1,
            "position": [250, 300]
        }
        n8n_nodes.append(webhook_node)
        
        # Keep track of previous node name to build connections
        prev_node_name = webhook_node["name"]
        
        current_x = 450
        connections_dict = {
            webhook_node["name"]: {"main": [[ ]]}
        }
        
        for idx, ui_node in enumerate(nodes):
            integration_id = ui_node.get('integration_id')
            node_data = ui_node.get('data', {})
            
            # Find the integration schema
            schema = next((item for item in CURATED_INTEGRATIONS if item["id"] == integration_id), None)
            if not schema:
                continue
                
            # Build the n8n parameter payload based on n8n_mapping
            parameters = {}
            for key, val in schema["n8n_mapping"].items():
                if isinstance(val, str) and val.startswith("{{data.") and val.endswith("}}"):
                    # Resolve data binding
                    data_key = val.replace("{{data.", "").replace("}}", "")
                    parameters[key] = node_data.get(data_key, "")
                else:
                    parameters[key] = val
                    
            node_name = f"{schema['name']} {idx+1}"
            n8n_node = {
                "parameters": parameters,
                "name": node_name,
                "type": schema["n8n_node_type"],
                "typeVersion": 1,
                "position": [current_x, 300]
            }
            n8n_nodes.append(n8n_node)
            
            # Connect previous node to this node
            connections_dict[prev_node_name]["main"][0].append({
                "node": node_name,
                "type": "main",
                "index": 0
            })
            
            # Initialize connections for this node
            connections_dict[node_name] = {"main": [[]]}
            
            prev_node_name = node_name
            current_x += 200
            
        n8n_payload = {
            "name": f"Workflow {trigger_type} - {request.user.organization.name}",
            "nodes": n8n_nodes,
            "connections": connections_dict,
            "active": True
        }
        
        # 2. Deploy to n8n
        from .n8n_client import N8NClient
        client = N8NClient()
        try:
            n8n_workflow = client.create_workflow(
                name=f"Workflow {trigger_type} - {request.user.organization.name}",
                nodes=n8n_nodes,
                connections=connections_dict
            )
            
            if not n8n_workflow:
                raise Exception("n8n API returned None")
                
            workflow_id = n8n_workflow.get('id')
            
            # Construct the webhook URL (assuming default n8n paths)
            webhook_url = f"http://localhost:5678/webhook/ai_trigger_{trigger_type.lower()}"
            
            # 3. Save to Django DB
            Workflow.objects.create(
                organization=request.user.organization,
                name=f"Curated {trigger_type} Workflow",
                trigger_type=trigger_type,
                n8n_workflow_id=workflow_id,
                webhook_url=webhook_url
            )
            
            return Response({"status": "success", "workflow_id": workflow_id, "webhook_url": webhook_url})
        except Exception as e:
            print(f"Deploy error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
