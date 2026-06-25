from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
import uuid

from apps.marketplace.models import Category


class FreelanceProject(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"
        DISPUTED = "DISPUTED", "Disputed"

    class ProjectType(models.TextChoices):
        FIXED = "FIXED", "Fixed Price"
        HOURLY = "HOURLY", "Hourly"

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="projects_created"
    )
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    assigned_freelancer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects_assigned",
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=300, blank=True, db_index=True)
    description = models.TextField()
    project_type = models.CharField(
        max_length=10, choices=ProjectType.choices, default=ProjectType.FIXED
    )
    budget = models.DecimalField(max_digits=12, decimal_places=2)
    hourly_rate = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    estimated_hours = models.PositiveIntegerField(null=True, blank=True)
    deadline = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    skills_required = models.ManyToManyField("freelance.Skill", blank=True, related_name="projects")
    seo_title = models.CharField(max_length=255, blank=True)
    seo_description = models.TextField(blank=True)
    progress_percent = models.PositiveSmallIntegerField(default=0)
    video_meeting_url = models.URLField(blank=True)
    is_featured = models.BooleanField(default=False)
    view_count = models.PositiveIntegerField(default=0)
    is_moderated = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["category", "status"]),
            models.Index(fields=["budget"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or f"project-{uuid.uuid4().hex[:8]}"
            slug = base
            counter = 1
            while FreelanceProject.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        if not self.seo_title:
            self.seo_title = self.title[:255]
        super().save(*args, **kwargs)


class Proposal(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SHORTLISTED = "SHORTLISTED", "Shortlisted"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"
        WITHDRAWN = "WITHDRAWN", "Withdrawn"

    project = models.ForeignKey(FreelanceProject, on_delete=models.CASCADE, related_name="proposals")
    freelancer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="proposals_sent"
    )
    cover_letter = models.TextField()
    bid_amount = models.DecimalField(max_digits=12, decimal_places=2)
    delivery_days = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    is_accepted = models.BooleanField(default=False)
    ai_match_score = models.FloatField(null=True, blank=True)
    is_flagged_spam = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = [("project", "freelancer")]
        indexes = [
            models.Index(fields=["project", "status"]),
            models.Index(fields=["freelancer", "status"]),
        ]

    def __str__(self):
        return f"Proposal for {self.project.title} by {self.freelancer.email}"


class Milestone(models.Model):
    project = models.ForeignKey(FreelanceProject, on_delete=models.CASCADE, related_name="milestones")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    order_index = models.PositiveSmallIntegerField(default=0)
    due_date = models.DateTimeField(null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    deliverable_file = models.FileField(upload_to="freelance/deliverables/", null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    escrow_transaction = models.ForeignKey(
        "freelance.FreelanceEscrowTransaction",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="milestones",
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["order_index", "id"]

    def __str__(self):
        return f"{self.title} - {self.amount}"
