from django.conf import settings
from django.db import models


class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    category = models.ForeignKey(
        "marketplace.Category", on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class FreelancerProfile(models.Model):
    class Availability(models.TextChoices):
        FULL_TIME = "FULL_TIME", "Full Time"
        PART_TIME = "PART_TIME", "Part Time"
        CONTRACT = "CONTRACT", "Contract"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="freelancer_profile"
    )
    bio = models.TextField(blank=True)
    title = models.CharField(max_length=255, blank=True)
    hourly_rate = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    experience_years = models.PositiveSmallIntegerField(default=0)
    availability = models.CharField(
        max_length=20, choices=Availability.choices, default=Availability.CONTRACT
    )
    phone = models.CharField(max_length=20, blank=True)
    telegram = models.CharField(max_length=100, blank=True)
    is_top_rated = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    completed_projects = models.PositiveIntegerField(default=0)
    total_earnings = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["is_top_rated"]),
            models.Index(fields=["hourly_rate"]),
        ]

    def __str__(self):
        return f"Profile: {self.user.username}"

    @property
    def is_verified(self):
        return self.verified_at is not None


class FreelancerSkill(models.Model):
    profile = models.ForeignKey(FreelancerProfile, on_delete=models.CASCADE, related_name="skills")
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    level = models.PositiveSmallIntegerField(default=3)

    class Meta:
        unique_together = [("profile", "skill")]

    def __str__(self):
        return f"{self.profile.user.username} - {self.skill.name} ({self.level})"


class PortfolioItem(models.Model):
    profile = models.ForeignKey(FreelancerProfile, on_delete=models.CASCADE, related_name="portfolio")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="freelance/portfolio/", null=True, blank=True)
    url = models.URLField(blank=True)
    skills = models.ManyToManyField(Skill, blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "-created_at"]

    def __str__(self):
        return self.title
