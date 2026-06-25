from django.conf import settings
from django.db import models


class FreelanceFile(models.Model):
    class FileType(models.TextChoices):
        DELIVERABLE = "DELIVERABLE", "Deliverable"
        CHAT = "CHAT", "Chat Attachment"
        CONTRACT = "CONTRACT", "Contract"

    project = models.ForeignKey(
        "freelance.FreelanceProject", on_delete=models.CASCADE, related_name="files"
    )
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    file = models.FileField(upload_to="freelance/files/")
    file_type = models.CharField(max_length=20, choices=FileType.choices, default=FileType.DELIVERABLE)
    original_name = models.CharField(max_length=255, blank=True)
    file_size = models.PositiveIntegerField(default=0)
    mime_type = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.original_name or self.file.name
