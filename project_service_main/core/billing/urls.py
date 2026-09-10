from django.urls import path
from .views import UsageDashboardView

urlpatterns = [
    path('usage/', UsageDashboardView.as_view(), name='usage_dashboard'),
]
