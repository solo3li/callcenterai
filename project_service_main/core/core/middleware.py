from core.models import set_current_organization

class TenantMiddleware:
    """
    Middleware that determines the current tenant (organization) from the user's session
    or domain, and sets it in the thread-local storage.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Default to None
        set_current_organization(None)

        if request.user.is_authenticated:
            # If the user is authenticated, set their organization as the current tenant
            if hasattr(request.user, 'organization') and request.user.organization:
                set_current_organization(request.user.organization)
                request.organization = request.user.organization

        response = self.get_response(request)

        # Clear the thread-local after the request is processed
        set_current_organization(None)

        return response
