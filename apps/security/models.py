from django.db import models
from django.conf import settings

class BlockedIP(models.Model):
    ip_address = models.GenericIPAddressField(unique=True)
    reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Bloklangan IP"
        verbose_name_plural = "Bloklangan IP manzillar"

    def __str__(self):
        return self.ip_address

class SecurityLog(models.Model):
    class Level(models.TextChoices):
        INFO = "INFO", "Info"
        WARNING = "WARNING", "Warning"
        CRITICAL = "CRITICAL", "Critical"

    level = models.CharField(max_length=10, choices=Level.choices, default=Level.INFO)
    action = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    details = models.JSONField(default=dict)
    
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Xavfsizlik jurnali"
        verbose_name_plural = "Xavfsizlik jurnallari"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.level} - {self.action}"

class AuditLog(models.Model):
    """
    Tracks administrative actions.
    """
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    changes = models.JSONField()
    
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Audit jurnali"
        verbose_name_plural = "Audit jurnallari"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.admin.email} modified {self.model_name}"
