import uuid

from django.conf import settings
from django.db import models


class PlatformCommission(models.Model):
    name = models.CharField(max_length=100, default="Default")
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_active", "-created_at"]

    def __str__(self):
        return f"{self.name} ({self.percentage}%)"


class FreelanceEscrowTransaction(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        RELEASED = "RELEASED", "Released"

    class Provider(models.TextChoices):
        MANUAL_SCREENSHOT = "MANUAL_SCREENSHOT", "Manual Screenshot"
        CLICK = "CLICK", "Click"
        PAYME = "PAYME", "Payme"
        UZUM = "UZUM", "Uzum Bank"
        BALANCE = "BALANCE", "Balance"

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    project = models.ForeignKey(
        "freelance.FreelanceProject", on_delete=models.CASCADE, related_name="escrow_transactions"
    )
    milestone = models.ForeignKey(
        "freelance.Milestone",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="escrow_payments",
    )
    payer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="escrow_payments_made"
    )
    payee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="escrow_payments_received",
        null=True,
        blank=True,
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    commission_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    provider = models.CharField(
        max_length=30, choices=Provider.choices, default=Provider.MANUAL_SCREENSHOT
    )
    payment_method = models.CharField(max_length=50, blank=True)
    screenshot = models.ImageField(upload_to="freelance/payments/", null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    admin_note = models.TextField(blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="escrow_approvals",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "project"]),
        ]

    def __str__(self):
        return f"Escrow {self.uuid} - {self.amount} ({self.status})"


class FreelanceContract(models.Model):
    project = models.OneToOneField(
        "freelance.FreelanceProject", on_delete=models.CASCADE, related_name="contract"
    )
    content_html = models.TextField()
    pdf_file = models.FileField(upload_to="freelance/contracts/", null=True, blank=True)
    client_signed_at = models.DateTimeField(null=True, blank=True)
    freelancer_signed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Contract for {self.project.title}"


class FreelanceInvoice(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SENT = "SENT", "Sent"
        PAID = "PAID", "Paid"
        CANCELLED = "CANCELLED", "Cancelled"

    invoice_number = models.CharField(max_length=50, unique=True)
    project = models.ForeignKey(
        "freelance.FreelanceProject", on_delete=models.CASCADE, related_name="invoices"
    )
    milestone = models.ForeignKey(
        "freelance.Milestone",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoices",
    )
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="freelance_invoices_client"
    )
    freelancer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="freelance_invoices_freelancer"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    commission = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    pdf_file = models.FileField(upload_to="freelance/invoices/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.invoice_number
