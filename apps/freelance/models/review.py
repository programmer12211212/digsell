from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class FreelanceReview(models.Model):
    project = models.ForeignKey(
        "freelance.FreelanceProject", on_delete=models.CASCADE, related_name="reviews"
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="freelance_reviews_given"
    )
    freelancer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="freelance_reviews_received"
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("project", "reviewer")]
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["freelancer", "rating"]),
        ]

    def __str__(self):
        return f"Review {self.rating}/5 for {self.freelancer.username}"
