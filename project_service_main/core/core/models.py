import threading
from django.db import models

# Thread-local storage to keep track of the current tenant (organization) during a request
_thread_locals = threading.local()

def get_current_organization():
    return getattr(_thread_locals, 'organization', None)

def set_current_organization(organization):
    _thread_locals.organization = organization

class TenantManager(models.Manager):
    def get_queryset(self):
        # Automatically filter by current organization
        org = get_current_organization()
        if org:
            return super().get_queryset().filter(organization=org)
        return super().get_queryset()

class TenantAwareModel(models.Model):
    """
    An abstract base class that ensures all objects are tied to a specific organization.
    """
    organization = models.ForeignKey(
        'organizations.Organization', 
        on_delete=models.CASCADE, 
        related_name='%(class)s_set'
    )

    objects = TenantManager()
    all_objects = models.Manager() # Bypasses tenant filtering if needed for superusers

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.organization_id:
            org = get_current_organization()
            if org:
                self.organization = org
        super().save(*args, **kwargs)
