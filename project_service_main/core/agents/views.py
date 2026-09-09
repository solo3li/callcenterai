from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django import forms
from core.models import get_current_organization

User = get_user_model()

class AgentForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password', 'agent_groups']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter agent_groups so it only shows groups from the current organization
        from core.models import get_current_organization
        from .models import AgentGroup
        org = get_current_organization()
        if org:
            self.fields['agent_groups'].queryset = AgentGroup.objects.filter(organization=org)
        else:
            self.fields['agent_groups'].queryset = AgentGroup.objects.none()
        
        self.fields['agent_groups'].widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        org = get_current_organization()
        if org:
            user.organization = org
        if commit:
            user.save()
        return user

class AgentListView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'agents/agent_list.html'
    context_object_name = 'agents'

    def get_queryset(self):
        org = get_current_organization()
        if org:
            return User.objects.filter(organization=org)
        return User.objects.none()

class AgentCreateView(LoginRequiredMixin, CreateView):
    model = User
    form_class = AgentForm
    template_name = 'agents/agent_form.html'
    success_url = reverse_lazy('agent_list')

class AgentUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'agent_groups']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from core.models import get_current_organization
        from .models import AgentGroup
        org = get_current_organization()
        if org:
            self.fields['agent_groups'].queryset = AgentGroup.objects.filter(organization=org)
        else:
            self.fields['agent_groups'].queryset = AgentGroup.objects.none()
        
        self.fields['agent_groups'].widget.attrs.update({'class': 'form-control'})

class AgentUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = AgentUpdateForm
    template_name = 'agents/agent_form.html'
    success_url = reverse_lazy('agent_list')

    def get_queryset(self):
        org = get_current_organization()
        if org:
            return User.objects.filter(organization=org)
        return User.objects.none()

class AgentDeleteView(LoginRequiredMixin, DeleteView):
    model = User
    template_name = 'agents/agent_confirm_delete.html'
    success_url = reverse_lazy('agent_list')

    def get_queryset(self):
        org = get_current_organization()
        if org:
            return User.objects.filter(organization=org)
        return User.objects.none()

from .models import AgentGroup

class AgentGroupListView(LoginRequiredMixin, ListView):
    model = AgentGroup
    template_name = 'agents/agent_group_list.html'
    context_object_name = 'groups'

class AgentGroupCreateView(LoginRequiredMixin, CreateView):
    model = AgentGroup
    fields = ['name', 'description']
    template_name = 'agents/agent_group_form.html'
    success_url = reverse_lazy('agent_group_list')

class AgentGroupUpdateView(LoginRequiredMixin, UpdateView):
    model = AgentGroup
    fields = ['name', 'description']
    template_name = 'agents/agent_group_form.html'
    success_url = reverse_lazy('agent_group_list')

class AgentGroupDeleteView(LoginRequiredMixin, DeleteView):
    model = AgentGroup
    template_name = 'agents/agent_group_confirm_delete.html'
    success_url = reverse_lazy('agent_group_list')
