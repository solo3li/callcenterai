from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ('username', 'email', 'organization', 'role', 'is_active', 'is_staff', 'is_superuser')
    list_filter   = ('role', 'is_active', 'is_staff', 'organization')
    search_fields = ('username', 'email')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Call Center', {'fields': ('organization', 'role')}),
    )
