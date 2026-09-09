from django import forms
from django.contrib.auth import get_user_model
from organizations.models import Organization, OrganizationSettings
from django.db import transaction

User = get_user_model()

class OrganizationSignupForm(forms.Form):
    organization_name = forms.CharField(max_length=255, label='Company Name')
    username = forms.CharField(max_length=150, label='Admin Username')
    email = forms.EmailField(label='Admin Email')
    password = forms.CharField(widget=forms.PasswordInput, label='Password')

    @transaction.atomic
    def save(self):
        # 1. Create Organization
        org = Organization.objects.create(
            name=self.cleaned_data['organization_name']
        )
        
        # 2. Create Organization Settings
        OrganizationSettings.objects.create(organization=org)

        # 3. Create Admin User
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            organization=org
        )
        return user
