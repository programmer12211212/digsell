from django.db import models
from django.conf import settings
from apps.marketplace.models import Product
from apps.orders.models import Order

class SupportTicket(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        RESOLVED = "RESOLVED", "Resolved"
        CLOSED = "CLOSED", "Closed"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tickets")
    subject = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    priority = models.IntegerField(default=1) # 1: Low, 2: Medium, 3: High
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Ticket #{self.id} - {self.subject}"

class Dispute(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="dispute")
    reason = models.TextField()
    evidence = models.FileField(upload_to="disputes/", blank=True, null=True)
    is_resolved = models.BooleanField(default=False)
    resolution_details = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Dispute for Order #{self.order.id}"

class TicketReply(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='replies')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    is_staff_reply = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Reply to #{self.ticket_id}"


class Announcement(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    target_role = models.CharField(max_length=20, blank=True, null=True, help_text="Empty for all")
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
