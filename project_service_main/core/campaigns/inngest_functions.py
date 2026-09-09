import json
import redis
from django.conf import settings
from asgiref.sync import sync_to_async

from inngest import step
from .inngest_client import inngest_client
from .models import OutboundCampaign, CampaignLead

@sync_to_async
def get_pending_leads(campaign_id):
    leads = CampaignLead.objects.filter(campaign_id=campaign_id, status='PENDING')
    return list(leads.values('id', 'phone_number'))

@sync_to_async
def get_campaign_info(campaign_id):
    campaign = OutboundCampaign.objects.select_related('agent_group__ai_agent').get(id=campaign_id)
    return campaign

@sync_to_async
def update_lead_status(lead_id, status):
    CampaignLead.objects.filter(id=lead_id).update(status=status)

@inngest_client.create_function(
    fn_id="run-campaign-workflow",
    trigger={"event": "campaign/start"}
)
async def run_campaign_workflow(ctx, step):
    campaign_id = ctx.event.data["campaign_id"]
    
    leads = await step.run("get-pending-leads", lambda: get_pending_leads(campaign_id))
    
    if not leads:
        return {"status": "no_leads_found"}

    events = []
    for lead in leads:
        events.append({
            "name": "call/dial_lead",
            "data": {
                "campaign_id": campaign_id,
                "lead_id": lead["id"],
                "phone_number": lead["phone_number"]
            }
        })
    
    # Fan-out: Send all events to Inngest to trigger individual dials
    await step.send_event("fan-out-calls", events)
    
    return {"status": "started", "leads_queued": len(events)}

@inngest_client.create_function(
    fn_id="dial-lead-workflow",
    trigger={"event": "call/dial_lead"}
)
async def dial_lead_workflow(ctx, step):
    lead_id = ctx.event.data["lead_id"]
    campaign_id = ctx.event.data["campaign_id"]
    phone_number = ctx.event.data["phone_number"]
    
    # Optional pacing: sleep for a short duration to not overwhelm the SIP provider
    await step.sleep("pacing", "2s")
    
    # Mark lead as calling
    await step.run("mark-lead-calling", lambda: update_lead_status(lead_id, 'CALLING'))
    
    async def execute_dial():
        campaign = await get_campaign_info(campaign_id)
        if not campaign.agent_group or not campaign.agent_group.ai_agent:
            return {"status": "failed", "reason": "no_ai_agent"}
        
        ai = campaign.agent_group.ai_agent
        room_name = f"outbound_{campaign_id}_{lead_id}"
        
        # 1. Trigger SIP Dial via LiveKit Server (Mocked logic here until full SIP API integration)
        # For example: livekit_api.RoomServiceClient(...).create_sip_participant(sip_trunk_id, phone_number, room_name)
        
        # 2. Publish to Redis to summon the AI Worker to this room
        r = redis.from_url(settings.REDIS_URL)
        payload = {
            "room_name": room_name,
            "caller_number": phone_number,
            "called_number": "campaign_dialer",
            "system_prompt": ai.system_prompt,
            "voice": ai.gemini_voice,
            "language": ai.language,
            "temperature": ai.temperature,
        }
        r.publish("ai_call_queue", json.dumps(payload))
        return {"status": "success", "room_name": room_name}

    result = await step.run("execute-dial", execute_dial)
    return result
