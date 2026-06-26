from django.db import models
from django.conf import settings

class Notification(models.Model):
    class Type(models.TextChoices):
        ORDER_NEW = "ORDER_NEW", "Yangi buyurtma"
        ORDER_PAID = "ORDER_PAID", "To'lov tasdiqlandi"
        ORDER_CANCELLED = "ORDER_CANCELLED", "Buyurtma bekor qilindi"
        WITHDRAWAL_APPROVED = "WITHDRAWAL_APPROVED", "Yechib olish tasdiqlandi"
        WITHDRAWAL_REJECTED = "WITHDRAWAL_REJECTED", "Yechib olish rad etildi"
        WALLET_TOPUP = "WALLET_TOPUP", "Hamyon to'ldirildi"
        WALLET_PAYMENT_FAILED = "WALLET_PAYMENT_FAILED", "Hamyon to'lovi xatolik bilan yakunlandi"
        WALLET_PAYMENT_CANCELLED = "WALLET_PAYMENT_CANCELLED", "Hamyon to'lovi bekor qilindi"
        SUPPORT_NEW = "SUPPORT_NEW", "Yangi support ticket"
        SUPPORT_REPLY = "SUPPORT_REPLY", "Admin javobi (support)"
        FREELANCE_PROPOSAL_NEW = "FREELANCE_PROPOSAL_NEW", "Yangi freelance taklif"
        FREELANCE_PROPOSAL_ACCEPTED = "FREELANCE_PROPOSAL_ACCEPTED", "Freelance taklif qabul qilindi"
        FREELANCE_PROPOSAL_REJECTED = "FREELANCE_PROPOSAL_REJECTED", "Freelance taklif rad etildi"
        FREELANCE_MILESTONE_DUE = "FREELANCE_MILESTONE_DUE", "Milestone muddati"
        FREELANCE_PAYMENT_PENDING = "FREELANCE_PAYMENT_PENDING", "Freelance to'lov kutilmoqda"
        FREELANCE_ESCROW_RELEASED = "FREELANCE_ESCROW_RELEASED", "Escrow to'lov o'tkazildi"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    notif_type = models.CharField(max_length=30, choices=Type.choices)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    target_url = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"
