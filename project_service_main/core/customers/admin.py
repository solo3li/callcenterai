from django.contrib import admin
from .models import Customer

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'email', 'organization')
    search_fields = ('name', 'phone_number', 'email')
    list_filter = ('organization',)