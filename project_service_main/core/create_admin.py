import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'callcenter_project.settings')
django.setup()

from organizations.models import Organization, OrganizationSettings
from django.contrib.auth import get_user_model

User = get_user_model()
org, _ = Organization.objects.get_or_create(name='Solo Company')
OrganizationSettings.objects.get_or_create(organization=org)
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(username='admin', email='admin@test.com', password='password123', organization=org)
    print('Admin user created successfully!')
else:
    print('Admin user already exists.')
