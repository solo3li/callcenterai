import asyncio
import json
import logging
import os
import aiohttp
import redis.asyncio as redis
from livekit import api

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.transports.network.livekit import LiveKitTransport, LiveKitTransportParams
from pipecat.models.google import GoogleLLMService
from pipecat.frames.frames import EndFrame

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai_worker")

# Environment Variables
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379")
LIVEKIT_URL = os.environ.get("LIVEKIT_URL", "ws://livekit-server:7880")
LIVEKIT_API_KEY = os.environ.get("LIVEKIT_API_KEY", "devkey")
LIVEKIT_API_SECRET = os.environ.get("LIVEKIT_API_SECRET", "secret")

async def handle_call(payload):
    room_name = payload.get("room_name")
    system_prompt = payload.get("system_prompt", "You are a helpful assistant.")
    voice = payload.get("voice", "Aoede")
    
    logger.info(f"Starting AI Agent for room: {room_name}")

    # Generate token for the AI to join the LiveKit room
    token = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET) \
        .with_identity("ai-assistant") \
        .with_name("AI Assistant") \
        .with_grants(api.VideoGrants(room_join=True, room=room_name)) \
        .to_jwt()

    # Configure LiveKit Transport
    transport = LiveKitTransport(
        token=token,
        url=LIVEKIT_URL,
        params=LiveKitTransportParams(
            audio_out_enabled=True,
            camera_out_enabled=False,
            vad_enabled=True
        )
    )

    tenant_id = payload.get("tenant_id")
    document_ids = payload.get("document_ids", [])
    
    agent_id = payload.get("agent_id")
    
    # 1. Fetch Dynamic Actions from Core
    dynamic_actions = []
    django_url = os.environ.get("DJANGO_URL", "http://host.docker.internal:8000")
    internal_key = os.environ.get("INTERNAL_API_KEY", "my_secure_internal_key")
    
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {internal_key}"}
            async with session.get(f"{django_url}/actions/api/internal/actions/?agent_id={agent_id}", headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    dynamic_actions = data.get("actions", [])
    except Exception as e:
        logger.error(f"Failed to fetch actions: {e}")

    # Update system prompt
    action_instructions = ""
    if dynamic_actions:
        action_instructions = "\n\nYou also have access to the following dynamic tools:\n"
        for act in dynamic_actions:
            action_instructions += f"- {act['name']}: {act['description']}\n"

    full_prompt = (
        f"{system_prompt}\n\n"
        "You have access to a tool called 'search_company_knowledge'. "
        "If the user asks about specific policies, prices, rules, or details about the company, "
        "you MUST use this tool to search the company's knowledge base before replying. "
        "Do not guess. Give the answer based strictly on the retrieved information."
        f"{action_instructions}"
    )

    context = [{"role": "system", "content": full_prompt}]

    llm = GoogleLLMService(model="gemini-1.5-flash")

    # Native Knowledge Tool
    async def search_company_knowledge(query: str) -> str:
        # (Existing RAG implementation)
        try:
            rag_url = os.environ.get("RAG_SERVICE_URL", "http://host.docker.internal:8002")
            rag_key = os.environ.get("RAG_INTERNAL_API_KEY", "my_secure_internal_key")
            async with aiohttp.ClientSession() as session:
                req_payload = {"tenant_id": tenant_id, "query": query, "document_ids": document_ids}
                headers = {"Authorization": f"Bearer {rag_key}"}
                async with session.post(f"{rag_url}/api/retrieve/", json=req_payload, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        results = data.get("results", [])
                        if not results:
                            return "No relevant information found."
                        return "\n\n".join([f"Source: {r['text']}" for r in results])
                    return "Error accessing knowledge base."
        except Exception as e:
            return f"Error: {e}"
            
    llm.register_function("search_company_knowledge", search_company_knowledge)

    # Factory for dynamic functions
    def create_dynamic_tool(action_def):
        async def dynamic_tool(**kwargs) -> str:
            logger.info(f"AI executing dynamic tool: {action_def['name']} with args: {kwargs}")
            try:
                async with aiohttp.ClientSession() as session:
                    req_payload = {
                        "action_name": action_def['name'],
                        "agent_id": agent_id,
                        "params": kwargs,
                        "type": action_def.get("type", "custom_action"),
                        "action_id": action_def.get("id")
                    }
                    headers = {"Authorization": f"Bearer {internal_key}"}
                    async with session.post(f"{django_url}/actions/api/internal/actions/execute/", json=req_payload, headers=headers) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            return data.get("result", "Success")
                        return "Execution failed on the backend."
            except Exception as e:
                return f"Error executing tool: {e}"
                
        # Attach the schema dynamically to the wrapper function for Gemini to understand
        dynamic_tool.__name__ = action_def['name']
        dynamic_tool.__doc__ = action_def['description']
        # Note: In a real Pipecat setup, we'd map action_def['input_schema'] to OpenAI/Gemini tool format properly
        # For simplicity in this implementation, we assume Pipecat reads the type hints or we inject the JSON schema.
        
        return dynamic_tool

    # Register all dynamic actions
    for act in dynamic_actions:
        tool_func = create_dynamic_tool(act)
        llm.register_function(act['name'], tool_func)

    pipeline = Pipeline([
        transport.input(),
        # STT -> LLM -> TTS ...
        transport.output()
    ])

    task = PipelineTask(pipeline, PipelineParams(allow_interruptions=True))
    
    @transport.event_handler("on_participant_connected")
    async def on_participant_connected(participant):
        logger.info(f"Participant connected: {participant.identity}")
        # Could send an initial greeting frame here

    runner = PipelineRunner()
    await runner.run(task)

    # After the call ends, send the transcript to the Django backend
    logger.info(f"Call ended for {room_name}. Saving transcript...")
    try:
        # Depending on how the context object is structured in pipecat, extract the strings
        # Currently context is a list. If it becomes a proper LLMContext, use .get_messages()
        messages = context if isinstance(context, list) else context.get_messages()
        transcript_text = "\n".join([f"{m.get('role', 'unknown')}: {m.get('content', '')}" for m in messages])
        
        async with aiohttp.ClientSession() as session:
            data = {
                "room_name": room_name,
                "transcript": transcript_text,
                "agent_id": agent_id
            }
            # Assuming 'web' is the hostname of the django container in docker-compose
            # or we can use an environment variable for the django URL
            django_url = os.environ.get("DJANGO_URL", "http://host.docker.internal:8000")
            async with session.post(f"{django_url}/api/analytics/save-transcript/", json=data) as resp:
                if resp.status != 200:
                    logger.error(f"Failed to save transcript: HTTP {resp.status}")
                else:
                    logger.info("Transcript saved successfully.")
    except Exception as e:
        logger.error(f"Error saving transcript: {e}")

async def main():
    logger.info("Connecting to Redis...")
    r = redis.from_url(REDIS_URL, decode_responses=True)
    pubsub = r.pubsub()
    await pubsub.subscribe("ai_call_queue")
    logger.info("Subscribed to 'ai_call_queue'. Waiting for calls...")

    async for message in pubsub.listen():
        if message["type"] == "message":
            payload = json.loads(message["data"])
            logger.info(f"Received call request: {payload}")
            # Spawn task so we don't block listening to new calls
            asyncio.create_task(handle_call(payload))

if __name__ == "__main__":
    asyncio.run(main())
