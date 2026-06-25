from django.db import models
from django.conf import settings

class AIInteraction(models.Model):
    class Type(models.TextChoices):
        CONTENT_GEN = "CONTENT_GEN", "Content Generation"
        MODERATION = "MODERATION", "Moderation"
        ANALYTICS = "ANALYTICS", "Analytics"
        SUPPORT = "SUPPORT", "Support Chat"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="ai_interactions")
    interaction_type = models.CharField(max_length=20, choices=Type.choices)
    
    prompt = models.TextField()
    response = models.TextField()
    
    tokens_used = models.PositiveIntegerField(default=0)
    cost = models.DecimalField(max_digits=10, decimal_places=5, default=0.0)
    
    status = models.CharField(max_length=20, default="SUCCESS")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.interaction_type} - {self.created_at}"

class AIConfig(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.key
