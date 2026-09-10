from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from users import views as user_views
from core.views import DashboardView

urlpatterns = [
    path('admin/', admin.site.urls),
    # Authentication
    path('accounts/login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('accounts/signup/', user_views.signup_view, name='signup'),
    
    # Apps
    path('customers/', include('customers.urls')),
    path('agents/', include('agents.urls')),
    path('settings/', include('organizations.urls')),
    path('telephony/', include('telephony.urls')),
    path('campaigns/', include('campaigns.urls')),
    path('analytics/', include('analytics.urls')),
    path('knowledge/', include('knowledge_base.urls')),
    path('actions/', include('actions_engine.urls')),
    path('workflows/', include('workflows.urls')),
    
    # Dashboard
    path('', DashboardView.as_view(), name='dashboard'),
]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
