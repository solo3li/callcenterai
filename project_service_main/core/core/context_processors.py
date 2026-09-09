def current_organization(request):
    """
    A context processor to make the current organization available to all templates.
    """
    if hasattr(request, 'organization') and request.organization:
        return {'current_organization': request.organization}
    return {'current_organization': None}
