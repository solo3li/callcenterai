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

    # Configure Gemini Multimodal Live via GoogleLLMService in Pipecat
    # Note: Using standard GoogleLLMService for this architecture
    llm = GoogleLLMService(model="gemini-1.5-flash") # Pipecat translates this internally

    # Set up the context
    context = [{"role": "system", "content": system_prompt}]

    # In a full pipecat pipeline, you'd have STT -> LLM -> TTS.
    # Since the user requested Gemini Live (multimodal), we would configure that specific Pipecat class here.
    # For now, we stub the pipeline setup:
    
    pipeline = Pipeline([
        transport.input(),
        # STT, LLM, TTS would go here
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
                "transcript": transcript_text
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
