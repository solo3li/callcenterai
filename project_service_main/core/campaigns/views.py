from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
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
        
        # Fire Inngest Event
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
