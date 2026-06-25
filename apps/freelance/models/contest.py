import uuid
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from apps.marketplace.models import Category
from apps.freelance.models.finance import FreelanceEscrowTransaction


class Contest(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        SELECTING = "SELECTING", "Selecting Winner"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="contests_created"
    )
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=300, blank=True, unique=True)
    description = models.TextField()
    reward = models.DecimalField(max_digits=12, decimal_places=2)
    deadline = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    winner = models.ForeignKey(
        "ContestSubmission", on_delete=models.SET_NULL, null=True, blank=True, related_name="contest_won"
    )
    escrow_transaction = models.ForeignKey(
        FreelanceEscrowTransaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contests",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or f"contest-{uuid.uuid4().hex[:8]}"
            slug = base
            counter = 1
            while Contest.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class ContestSubmission(models.Model):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name="submissions")
    freelancer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="contest_submissions"
    )
    description = models.TextField(blank=True)
    file = models.FileField(upload_to="freelance/contests/")
    is_winner = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = [("contest", "freelancer")]

    def __str__(self):
        return f"Submission by {self.freelancer.username} for {self.contest.title}"
