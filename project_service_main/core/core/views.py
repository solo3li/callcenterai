from rest_framework import viewsets
from core.models import get_current_organization

class TenantBaseViewSet(viewsets.ModelViewSet):
    """
    A base ViewSet for DRF that automatically restricts QuerySets to the 
    user's current organization, and injects the organization upon creation.
    """
    def get_queryset(self):
        # The core TenantManager might already filter this if we use Model.objects.all(),
        # but overriding get_queryset provides a double-layer of security for DRF.
        queryset = super().get_queryset()
        org = get_current_organization()
        if org:
            return queryset.filter(organization=org)
        return queryset.none() # Return nothing if no org is found to be safe

    def perform_create(self, serializer):
        # Automatically inject the organization when creating via API
        org = get_current_organization()
        if org:
            serializer.save(organization=org)
        else:
            # Depending on business logic, you might raise an exception here
            serializer.save()
