import asyncio
import json
import logging
import os
import time

import aiohttp
import redis.asyncio as redis
from livekit import api

from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.frames.frames import EndFrame, LLMTextFrame, TranscriptionFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.worker import PipelineWorker
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.services.google.gemini_live.llm import GeminiLiveLLMService
from pipecat.transports.base_transport import TransportParams
from pipecat.transports.livekit.transport import LiveKitTransport

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai_worker")

# Environment Variables
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379")
LIVEKIT_URL = os.environ.get("LIVEKIT_URL", "ws://livekit-server:7880")
LIVEKIT_API_KEY = os.environ.get("LIVEKIT_API_KEY", "devkey")
LIVEKIT_API_SECRET = os.environ.get("LIVEKIT_API_SECRET", "secret")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_LIVE_MODEL = os.environ.get(
    "GEMINI_LIVE_MODEL", "models/gemini-2.5-flash-native-audio-preview-12-2025"
)


class TranscriptTap(FrameProcessor):
    """Collects conversation text flowing through the pipeline.

    Gemini Live pushes the caller's speech as TranscriptionFrame upstream
    (toward transport.input()) and its own replies as LLMTextFrame downstream
    (toward transport.output()), so one tap sits on each side of the LLM.
    """

    def __init__(self, role: str, transcript: list):
        super().__init__()
        self._role = role
        self._transcript = transcript

    async def process_frame(self, frame, direction: FrameDirection):
        if isinstance(frame, TranscriptionFrame) and direction == FrameDirection.UPSTREAM:
            self._transcript.append((time.time(), self._role, frame.text))
        elif isinstance(frame, LLMTextFrame) and frame.text.strip():
            self._transcript.append((time.time(), self._role, frame.text))
        await self.push_frame(frame, direction)


def render_transcript(transcript: list) -> str:
    return "\n".join(
        f"{role}: {text.strip()}" for _, role, text in sorted(transcript, key=lambda e: e[0])
    )


def build_tools(agent_id, tenant_id, document_ids, dynamic_actions, internal_key, django_url):
    """Build Gemini function declarations for RAG retrieval and dynamic actions."""

    async def search_company_knowledge(params):
        query = params.arguments.get("query", "")
        try:
            rag_url = os.environ.get("RAG_SERVICE_URL", "http://host.docker.internal:8002")
            rag_key = os.environ.get("RAG_INTERNAL_API_KEY", "my_secure_internal_key")
            async with aiohttp.ClientSession() as session:
                req_payload = {
                    "tenant_id": tenant_id,
                    "query": query,
                    "document_ids": document_ids,
                }
                headers = {"Authorization": f"Bearer {rag_key}"}
                async with session.post(
                    f"{rag_url}/api/retrieve/", json=req_payload, headers=headers
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        results = data.get("results", [])
                        if not results:
                            result = "No relevant information found."
                        else:
                            result = "\n\n".join(f"Source: {r['text']}" for r in results)
                    else:
                        result = "Error accessing knowledge base."
        except Exception as e:
            result = f"Error: {e}"
        await params.result_callback(result)

    tools = [
        FunctionSchema(
            name="search_company_knowledge",
            description=(
                "Search the company knowledge base for policies, prices, rules "
                "or details about the business. Use before answering such questions."
            ),
            properties={
                "query": {
                    "type": "string",
                    "description": "The search query to look up in the knowledge base.",
                }
            },
            required=["query"],
            handler=search_company_knowledge,
        )
    ]

    for act in dynamic_actions:
        # input_schema is a JSON Schema object: {"properties": {...}, "required": [...]}
        schema = act.get("input_schema") or {}
        action_name = act["name"]
        action_id = act.get("id")

        async def execute_action(params, _act_name=action_name, _action_id=action_id):
            logger.info(f"AI executing dynamic tool: {_act_name} with args: {params.arguments}")
            try:
                async with aiohttp.ClientSession() as session:
                    req_payload = {
                        "action_name": _act_name,
                        "agent_id": agent_id,
                        "params": params.arguments,
                        "type": "custom_action",
                        "action_id": _action_id,
                    }
                    headers = {"Authorization": f"Bearer {internal_key}"}
                    async with session.post(
                        f"{django_url}/actions/api/internal/actions/execute/",
                        json=req_payload,
                        headers=headers,
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            result = data.get("result", "Success")
                        else:
                            result = "Execution failed on the backend."
            except Exception as e:
                result = f"Error executing tool: {e}"
            await params.result_callback(result)

        tools.append(
            FunctionSchema(
                name=action_name,
                description=act.get("description", ""),
                properties=schema.get("properties", {}),
                required=schema.get("required", []),
                handler=execute_action,
            )
        )

    return tools


async def save_transcript(django_url, room_name, agent_id, transcript_text):
    logger.info(f"Call ended for {room_name}. Saving transcript...")
    try:
        async with aiohttp.ClientSession() as session:
            data = {
                "room_name": room_name,
                "transcript": transcript_text,
                "agent_id": agent_id,
            }
            async with session.post(
                f"{django_url}/analytics/api/save-transcript/", json=data
            ) as resp:
                if resp.status != 200:
                    logger.error(f"Failed to save transcript: HTTP {resp.status}")
                else:
                    logger.info("Transcript saved successfully.")
    except Exception as e:
        logger.error(f"Error saving transcript: {e}")


async def handle_call(payload):
    room_name = payload.get("room_name")
    system_prompt = payload.get("system_prompt", "You are a helpful assistant.")
    voice = payload.get("voice", "Aoede")
    language = payload.get("language", "en-US")
    temperature = payload.get("temperature")

    logger.info(f"Starting AI Agent for room: {room_name}")

    # Generate token for the AI to join the LiveKit room
    token = (
        api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity("ai-assistant")
        .with_name("AI Assistant")
        .with_grants(api.VideoGrants(room_join=True, room=room_name))
        .to_jwt()
    )

    transport = LiveKitTransport(
        url=LIVEKIT_URL,
        token=token,
        room_name=room_name,
        params=TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            video_in_enabled=False,
            video_out_enabled=False,
        ),
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
            async with session.get(
                f"{django_url}/actions/api/internal/actions/?agent_id={agent_id}",
                headers=headers,
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    dynamic_actions = data.get("actions", [])
    except Exception as e:
        logger.error(f"Failed to fetch actions: {e}")

    # 2. Compose the system prompt (persona + RAG policy + dynamic tools)
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

    # 3. Gemini Live session: speech-to-speech with native turn detection,
    #    interruption handling and transcription (input + output enabled by default).
    settings = GeminiLiveLLMService.Settings(
        model=GEMINI_LIVE_MODEL,
        voice=voice,
        language=language,
        system_instruction=full_prompt,
        **({"temperature": temperature} if temperature is not None else {}),
    )

    llm_service = GeminiLiveLLMService(
        api_key=GEMINI_API_KEY,
        settings=settings,
        tools=build_tools(
            agent_id, tenant_id, document_ids, dynamic_actions, internal_key, django_url
        ),
    )

    # 4. Live transcript taps around the LLM
    transcript = []
    user_tap = TranscriptTap("Caller", transcript)
    ai_tap = TranscriptTap("AI", transcript)

    pipeline = Pipeline(
        [transport.input(), user_tap, llm_service, ai_tap, transport.output()]
    )

    task = PipelineWorker(pipeline)

    @transport.event_handler("on_participant_connected")
    async def on_participant_connected(transport, participant):
        logger.info(f"Participant connected: {participant.identity}")

    @transport.event_handler("on_participant_disconnected")
    async def on_participant_disconnected(transport, participant):
        logger.info(f"Participant disconnected: {participant.identity}")
        await task.queue_frames([EndFrame()])

    runner = PipelineRunner()
    await runner.run(task)

    # 5. After the call ends, send the live transcript to the Django backend
    transcript_text = render_transcript(transcript)
    await save_transcript(django_url, room_name, agent_id, transcript_text)


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
