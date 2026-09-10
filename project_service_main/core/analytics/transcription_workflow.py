import os
import time

import boto3
from google import genai
from google.genai import types
from inngest import Step
from asgiref.sync import sync_to_async
from django.conf import settings
from campaigns.inngest_client import inngest_client
from .models import CallLog

s3_client = boto3.client(
    's3',
    endpoint_url='http://localhost:9000', # MinIO locally
    aws_access_key_id='minioadmin',
    aws_secret_access_key='minioadmin'
)
MINIO_BUCKET = "call-recordings"

TRANSCRIPTION_MODEL = os.environ.get("GEMINI_TRANSCRIPTION_MODEL", "gemini-2.5-flash")

MIME_TYPES = {
    ".mp4": "video/mp4",
    ".m4a": "audio/mp4",
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".ogg": "audio/ogg",
    ".webm": "audio/webm",
}

TRANSCRIPT_PROMPT = (
    "Transcribe this call recording verbatim. Format every line as "
    "'[MM:SS] Speaker: text'. Identify the two speakers as 'Customer' and "
    "'Agent' based on who initiates the call and the content of the "
    "conversation — if a dedicated audio track per speaker is provided, its "
    "speaker is '{speaker}'. Output only the transcript, no commentary."
)

@sync_to_async
def update_call_log(room_name, transcript, recording_url):
    try:
        log, created = CallLog.objects.get_or_create(
            room_name=room_name,
            defaults={"phone_number": "unknown", "direction": "INBOUND"}
        )
        log.transcript = transcript
        log.recording_url = recording_url
        log.save()
    except Exception as e:
        print(f"Error updating call log: {e}")

def _transcribe_with_gemini(filename, speaker_label):
    """Download a recording from MinIO and transcribe it with Gemini.

    Gemini consumes the audio directly through the Files API (no ffmpeg
    preprocessing) and diarizes the speakers itself when given a composite
    track.
    """
    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    local_path = f"/tmp/{filename}"
    s3_client.download_file(MINIO_BUCKET, filename, local_path)

    try:
        ext = os.path.splitext(filename)[1].lower()
        mime_type = MIME_TYPES.get(ext, "video/mp4")
        audio_file = client.files.upload(
            file=local_path,
            config=types.UploadFileConfig(mime_type=mime_type),
        )
        while audio_file.state == types.FileState.PROCESSING:
            time.sleep(3)
            audio_file = client.files.get(name=audio_file.name)
        if audio_file.state == types.FileState.FAILED:
            raise RuntimeError(f"Gemini Files API failed to process {filename}")

        prompt = TRANSCRIPT_PROMPT.format(speaker=speaker_label)
        response = client.models.generate_content(
            model=TRANSCRIPTION_MODEL,
            contents=[prompt, audio_file],
        )
        return response.text or ""
    finally:
        os.remove(local_path)
        # Delete from MinIO to save space
        s3_client.delete_object(Bucket=MINIO_BUCKET, Key=filename)

@inngest_client.create_function(
    fn_id="process-call-recording",
    trigger={"event": "analytics/process_recording"}
)
async def process_recording_workflow(ctx, step: Step):
    room_name = ctx.event.data["room_name"]
    files = ctx.event.data.get("files", [])

    # Prefer isolated per-speaker tracks when the egress produced them;
    # otherwise fall back to the composite recording and let Gemini diarize.
    customer_file = next((f for f in files if "customer" in f), None)
    agent_file = next((f for f in files if "agent" in f), None)
    composite_file = next((f for f in files if "composite" in f), None)

    def transcribe_all():
        if not settings.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is not configured")
        sections = []
        if customer_file and agent_file:
            sections.append(_transcribe_with_gemini(customer_file, "Customer"))
            sections.append(_transcribe_with_gemini(agent_file, "Agent"))
            return "\n".join(sections)
        if composite_file:
            return _transcribe_with_gemini(composite_file, "Agent")
        raise FileNotFoundError("No recording files found in the event payload")

    transcript = await step.run("transcribe-recordings", transcribe_all)

    # Finalize
    recording_url = f"http://localhost:9000/{MINIO_BUCKET}/{composite_file}" if composite_file else ""
    await step.run("update-call-log", lambda: update_call_log(room_name, transcript, recording_url))

    return {"status": "success", "transcript_length": len(transcript)}
