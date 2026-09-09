from django.db import models
from core.models import TenantAwareModel

class AgentGroup(TenantAwareModel):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

GEMINI_VOICES = [
    ('Aoede', 'Aoede (Female, smooth)'),
    ('Charon', 'Charon (Male, deep)'),
    ('Fenrir', 'Fenrir (Male, energetic)'),
    ('Kore', 'Kore (Female, clear)'),
    ('Puck', 'Puck (Male, friendly)'),
]

GEMINI_LANGUAGES = [
    ('ar-EG', 'Arabic (Egypt)'),
    ('ar-SA', 'Arabic (Saudi Arabia)'),
    ('ar-AE', 'Arabic (UAE)'),
    ('ar-KW', 'Arabic (Kuwait)'),
    ('en-US', 'English (US)'),
    ('en-GB', 'English (UK)'),
    ('es-ES', 'Spanish (Spain)'),
    ('fr-FR', 'French (France)'),
    ('de-DE', 'German (Germany)'),
]

class AIAgent(TenantAwareModel):
    name = models.CharField(max_length=255)
    system_prompt = models.TextField(help_text="Instructions defining the AI persona and constraints.")
    gemini_voice = models.CharField(max_length=50, choices=GEMINI_VOICES, default='Aoede')
    language = models.CharField(max_length=20, choices=GEMINI_LANGUAGES, default='ar-EG')
    temperature = models.FloatField(default=0.7, help_text="Values from 0.0 (Strict) to 1.0 (Creative)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
