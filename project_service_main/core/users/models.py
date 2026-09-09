from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    # For a multi-tenant B2B SaaS, users typically belong to one organization at a time.
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='users',
        help_text=_("The organization this user belongs to.")
    )

    def __str__(self):
        return f"{self.username} ({self.organization.name if self.organization else 'No Org'})"
