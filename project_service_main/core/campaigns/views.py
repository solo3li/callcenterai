import csv
import io
import jwt
import time
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.conf import settings
from .models import OutboundCampaign, CampaignLead
from agents.models import AgentGroup
from telephony.models import SIPTrunk
from .inngest_client import inngest_client

class CampaignListView(LoginRequiredMixin, ListView):
    model = OutboundCampaign
    template_name = 'campaigns/campaign_list.html'
    context_object_name = 'campaigns'

    def get_queryset(self):
        return OutboundCampaign.objects.filter(organization=self.request.user.organization)

class CampaignDetailView(LoginRequiredMixin, DetailView):
    model = OutboundCampaign
    template_name = 'campaigns/campaign_detail.html'
    context_object_name = 'campaign'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['leads'] = self.object.leads.all()
        
        # Generate Centrifugo JWT for the frontend
        # Payload must have 'sub' (subject) according to Centrifugo docs
        payload = {
            "sub": str(self.request.user.id),
            "exp": int(time.time()) + 3600  # Token valid for 1 hour
        }
        centrifugo_token = jwt.encode(payload, settings.CENTRIFUGO_SECRET, algorithm="HS256")
        
        context['centrifugo_token'] = centrifugo_token
        context['centrifugo_url'] = settings.CENTRIFUGO_URL.replace('http', 'ws').replace('/api', '/connection/websocket')
        context['channel_name'] = f"campaign_{self.object.id}"
        
        return context

class CampaignCreateView(LoginRequiredMixin, CreateView):
    model = OutboundCampaign
    template_name = 'campaigns/campaign_form.html'
    fields = ['name', 'agent_group', 'sip_trunk']
    success_url = reverse_lazy('campaign-list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['agent_group'].queryset = AgentGroup.objects.filter(
            organization=self.request.user.organization, 
            group_type='AI'
        )
        form.fields['sip_trunk'].queryset = SIPTrunk.objects.filter(
            organization=self.request.user.organization
        )
        return form

    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        return super().form_valid(form)

def start_campaign(request, pk):
    campaign = get_object_or_404(OutboundCampaign, pk=pk, organization=request.user.organization)
    
    if campaign.status != 'RUNNING':
        campaign.status = 'RUNNING'
        campaign.save()
        
        inngest_client.send(
            name="campaign/start",
            data={
                "campaign_id": campaign.id
            }
        )
        messages.success(request, f"Campaign '{campaign.name}' started successfully!")
    else:
        messages.warning(request, "Campaign is already running.")
        
    return redirect('campaign-detail', pk=pk)

def upload_leads(request, pk):
    campaign = get_object_or_404(OutboundCampaign, pk=pk, organization=request.user.organization)
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'This is not a CSV file')
            return redirect('campaign-detail', pk=pk)
            
        data_set = csv_file.read().decode('UTF-8')
        io_string = io.StringIO(data_set)
        next(io_string) # Skip header
        
        leads_to_create = []
        for column in csv.reader(io_string, delimiter=',', quotechar='"'):
            if column: # Ensure row is not empty
                phone_number = column[0].strip()
                leads_to_create.append(
                    CampaignLead(campaign=campaign, phone_number=phone_number, status='PENDING')
                )
                
        # Bulk create for maximum efficiency
        CampaignLead.objects.bulk_create(leads_to_create, ignore_conflicts=True)
        messages.success(request, f"Successfully uploaded {len(leads_to_create)} leads.")
        
    return redirect('campaign-detail', pk=pk)
