import os
import boto3
import subprocess
from openai import OpenAI
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

@inngest_client.create_function(
    fn_id="process-call-recording",
    trigger={"event": "analytics/process_recording"}
)
async def process_recording_workflow(ctx, step: Step):
    room_name = ctx.event.data["room_name"]
    files = ctx.event.data.get("files", [])
    
    # Normally we'd find the 3 files (composite, customer track, agent track)
    # Let's assume LiveKit saved them with suffixes
    composite_file = next((f for f in files if "composite" in f), None)
    customer_file = next((f for f in files if "customer" in f), None)
    agent_file = next((f for f in files if "agent" in f), None)
    
    if not customer_file or not agent_file:
        return {"status": "skipped", "reason": "missing_isolated_tracks"}

    def download_compress_transcribe():
        # Setup OpenAI
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "sk-mock"))
        
        def process_track(filename, speaker_label):
            local_path = f"/tmp/{filename}"
            compressed_path = f"/tmp/compressed_{filename}.mp3"
            
            # Download from MinIO
            s3_client.download_file(MINIO_BUCKET, filename, local_path)
            
            # Compress using FFmpeg
            subprocess.run([
                "ffmpeg", "-y", "-i", local_path, 
                "-ac", "1", "-ar", "16000", "-b:a", "32k", 
                compressed_path
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Transcribe with Whisper
            with open(compressed_path, "rb") as audio_file:
                # Assuming valid API key in production
                try:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1", 
                        file=audio_file, 
                        response_format="verbose_json"
                    )
                    segments = transcript.segments
                except Exception as e:
                    # Mock segments if API fails or key is missing
                    print("OpenAI Whisper Error:", e)
                    segments = [{"start": 0.0, "text": f"Mock {speaker_label} text due to missing key"}]
                    
            # Cleanup
            os.remove(local_path)
            os.remove(compressed_path)
            # Delete from MinIO to save space
            s3_client.delete_object(Bucket=MINIO_BUCKET, Key=filename)
            
            return [{"speaker": speaker_label, "start": s['start'], "text": s['text']} for s in segments]
        
        # Process both
        customer_segments = process_track(customer_file, "Customer")
        agent_segments = process_track(agent_file, "Agent")
        
        # Merge by timestamp
        all_segments = customer_segments + agent_segments
        all_segments.sort(key=lambda x: x["start"])
        
        # Format
        final_transcript = "\n".join([f"[{s['start']:.1f}s] {s['speaker']}: {s['text'].strip()}" for s in all_segments])
        return final_transcript
        
    transcript = await step.run("download-compress-transcribe", download_compress_transcribe)
    
    # Finalize
    recording_url = f"http://localhost:9000/{MINIO_BUCKET}/{composite_file}" if composite_file else ""
    await step.run("update-call-log", lambda: update_call_log(room_name, transcript, recording_url))
    
    return {"status": "success", "transcript_length": len(transcript)}
