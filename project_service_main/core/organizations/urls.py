from django.urls import path
from . import views

urlpatterns = [
    path('', views.SettingsUpdateView.as_view(), name='settings_update'),
]
