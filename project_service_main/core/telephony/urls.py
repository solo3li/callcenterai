from django.urls import path
from . import views
from . import api_views

urlpatterns = [
    path('numbers/', views.PhoneNumberListView.as_view(), name='phone_number_list'),
    path('numbers/new/', views.PhoneNumberCreateView.as_view(), name='phone_number_create'),
    path('numbers/<int:pk>/edit/', views.PhoneNumberUpdateView.as_view(), name='phone_number_update'),
    path('numbers/<int:pk>/delete/', views.PhoneNumberDeleteView.as_view(), name='phone_number_delete'),
    
    # APIs
    path('api/inbound-webhook/', api_views.inbound_webhook, name='inbound_webhook'),

    # SIP Trunks
    path('trunks/', views.SIPTrunkListView.as_view(), name='sip_trunk_list'),
    path('trunks/new/', views.SIPTrunkCreateView.as_view(), name='sip_trunk_create'),
    path('trunks/<int:pk>/edit/', views.SIPTrunkUpdateView.as_view(), name='sip_trunk_update'),
    path('trunks/<int:pk>/delete/', views.SIPTrunkDeleteView.as_view(), name='sip_trunk_delete'),
]
