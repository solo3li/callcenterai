import json
from asgiref.sync import sync_to_async
from django.conf import settings
from google import genai
from pydantic import BaseModel
from inngest import Step
from campaigns.inngest_client import inngest_client
from .models import CallLog

class CallAnalysis(BaseModel):
    summary: str
    sentiment: str
    outcome: str

@sync_to_async
def get_call_log(log_id):
    try:
        return CallLog.objects.get(id=log_id)
    except CallLog.DoesNotExist:
        return None

@sync_to_async
def update_call_log_analysis(log_id, analysis_data):
    CallLog.objects.filter(id=log_id).update(
        summary=analysis_data.summary,
        sentiment=analysis_data.sentiment,
        outcome=analysis_data.outcome
    )

@inngest_client.create_function(
    fn_id="analyze-call-transcript",
    trigger={"event": "analytics/analyze_transcript"}
)
async def analyze_transcript_workflow(ctx, step: Step):
    call_log_id = ctx.event.data["call_log_id"]
    
    log = await step.run("get-call-log", lambda: get_call_log(call_log_id))
    if not log or not log.transcript:
        return {"status": "skipped", "reason": "no_transcript"}

    async def analyze_with_gemini():
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        
        prompt = f"""
        Analyze the following call transcript. 
        Extract a brief summary, the overall sentiment (e.g. POSITIVE, NEUTRAL, NEGATIVE), 
        and the call outcome (e.g. INTERESTED, NOT_INTERESTED, VOICEMAIL, FOLLOW_UP_REQUIRED).

        Transcript:
        {log.transcript}
        """

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={
                'response_mime_type': 'application/json',
                'response_schema': CallAnalysis,
            },
        )
        return response.text

    analysis_json_str = await step.run("call-gemini", analyze_with_gemini)
    
    try:
        analysis_data = CallAnalysis.model_validate_json(analysis_json_str)
        await step.run("update-call-log", lambda: update_call_log_analysis(call_log_id, analysis_data))
        return {"status": "success", "analysis": analysis_data.model_dump()}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
