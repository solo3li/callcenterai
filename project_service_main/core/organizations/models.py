from django.db import models
from django.utils.translation import gettext_lazy as _

class Organization(models.Model):
    name = models.CharField(_("Organization Name"), max_length=255)
    domain = models.CharField(_("Domain"), max_length=255, unique=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class OrganizationSettings(models.Model):
    organization = models.OneToOneField(Organization, on_delete=models.CASCADE, related_name='settings')
    timezone = models.CharField(max_length=50, default='UTC')
    ai_greeting = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.organization.name} Settings"
