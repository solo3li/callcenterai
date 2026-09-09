import json
import requests
import asyncio
import websockets
from jsonpath_ng import parse
from django.template import Template, Context

def resolve_template(template_str, context_dict):
    """
    Resolves Django template variables in strings safely.
    e.g. {{user_id}} -> 123
    """
    if not template_str:
        return ""
    # Safe template rendering without access to sensitive Django globals
    template = Template(template_str)
    return template.render(Context(context_dict))

def extract_response(json_data, extractor_path):
    """
    Uses JSONPath to extract specific data to save tokens.
    """
    if not extractor_path or not json_data:
        return json.dumps(json_data)
        
    try:
        jsonpath_expr = parse(extractor_path)
        matches = [match.value for match in jsonpath_expr.find(json_data)]
        if not matches:
            return "No matching data found."
        # If single match, return it directly, else return list
        result = matches[0] if len(matches) == 1 else matches
        return json.dumps(result)
    except Exception as e:
        return f"Extraction Error: {e}"

async def execute_websocket(url, payload, timeout=10):
    """
    Connects to a websocket, sends the payload, waits for the FIRST response, and closes.
    """
    try:
        async with websockets.connect(url, close_timeout=timeout) as websocket:
            await websocket.send(payload)
            response = await asyncio.wait_for(websocket.recv(), timeout=timeout)
            return response
    except Exception as e:
        return f"WebSocket Error: {e}"

def execute_action(action, params_dict):
    """
    The Main Executor Engine
    """
    # 1. Resolve URL and Headers
    resolved_url = resolve_template(action.endpoint_url, params_dict)
    
    # Headers are usually JSON dicts. Resolve them recursively or just as strings.
    resolved_headers = {}
    for k, v in action.headers.items():
        resolved_headers[k] = resolve_template(str(v), params_dict)
        
    # 2. Resolve Body
    resolved_body = resolve_template(action.body_template, params_dict)
    
    response_text = ""
    max_attempts = action.retry_count + 1
    
    for attempt in range(max_attempts):
        try:
            if action.protocol == 'HTTP':
                method = action.http_method.upper() if action.http_method else 'POST'
                kwargs = {'headers': resolved_headers, 'timeout': action.timeout_seconds}
                if method in ['POST', 'PUT'] and resolved_body:
                    kwargs['data'] = resolved_body
                    if 'Content-Type' not in [k.title() for k in resolved_headers.keys()]:
                        resolved_headers['Content-Type'] = 'application/json'
                
                resp = requests.request(method, resolved_url, **kwargs)
                resp.raise_for_status()
                
                try:
                    json_resp = resp.json()
                    response_text = extract_response(json_resp, action.response_extractor)
                except ValueError:
                    response_text = resp.text[:1000]
                    
            elif action.protocol == 'GRAPHQL':
                resolved_headers['Content-Type'] = 'application/json'
                try:
                    payload = json.loads(resolved_body)
                except json.JSONDecodeError:
                    payload = {"query": resolved_body, "variables": params_dict}
                    
                resp = requests.post(resolved_url, json=payload, headers=resolved_headers, timeout=action.timeout_seconds)
                resp.raise_for_status()
                response_text = extract_response(resp.json(), action.response_extractor)
                
            elif action.protocol == 'WEBSOCKET':
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                ws_resp = loop.run_until_complete(
                    execute_websocket(resolved_url, resolved_body, timeout=action.timeout_seconds)
                )
                loop.close()
                try:
                    json_resp = json.loads(ws_resp)
                    response_text = extract_response(json_resp, action.response_extractor)
                except:
                    response_text = str(ws_resp)
                    
            elif action.protocol == 'GRPC':
                # gRPC requires Server Reflection to be enabled on the target server 
                # to dynamically invoke methods without compiled .proto files.
                # In a full production env, we'd use grpc_requests or similar reflection clients here.
                response_text = "gRPC reflection is partially implemented. Expecting dynamic JSON to Protobuf serialization."
                
            # If we reach here, execution was successful
            return response_text
            
        except Exception as e:
            if attempt == max_attempts - 1:
                return f"Action Execution Failed after {max_attempts} attempts: {str(e)}"
            # Wait briefly before retrying
            import time
            time.sleep(1)
            
    return response_text
