from django.db import models
from django.conf import settings
from django.utils.text import slugify


class CourseCategory(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    icon = models.CharField(max_length=50, default='fas fa-folder')
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children'
    )

    class Meta:
        verbose_name_plural = "Categories (Tree)"

    def __str__(self):
        return self.name


class VideoQuerySet(models.QuerySet):
    def published(self):
        return self.filter(
            is_active=True,
            moderation_status=Video.ModerationStatus.APPROVED,
        )


class Video(models.Model):
    class ProductType(models.TextChoices):
        PHYSICAL = 'PHYSICAL', 'Physical Product'
        DIGITAL = 'DIGITAL', 'Digital File (PDF/ZIP/EXE)'
        VIDEO_COURSE = 'VIDEO', 'Premium Video Course'
        SERVICE = 'SERVICE', 'Professional Service'

    class ModerationStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending Review'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        CHANGES_REQUESTED = 'CHANGES_REQUESTED', 'Changes Requested'
        SUSPENDED = 'SUSPENDED', 'Suspended'

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    product_type = models.CharField(
        max_length=20, choices=ProductType.choices, default=ProductType.VIDEO_COURSE
    )

    category = models.ForeignKey(
        CourseCategory, on_delete=models.SET_NULL, null=True, related_name='videos'
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='seller_videos'
    )

    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    tags = models.CharField(max_length=255, blank=True, default='')
    demo_url = models.URLField(blank=True, null=True)
    seo_title = models.CharField(max_length=255, blank=True)
    seo_description = models.TextField(blank=True, default='')

    thumbnail = models.ImageField(upload_to='thumbnails/%Y/%m/', blank=True, null=True)
    preview_video = models.FileField(upload_to='previews/%Y/%m/', null=True, blank=True)

    hls_root = models.CharField(max_length=500, blank=True, null=True)
    is_protected = models.BooleanField(default=True)

    views_count = models.PositiveIntegerField(default=0, db_column='views')
    sales_count = models.PositiveIntegerField(default=0, db_column='purchases_count')
    avg_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0, db_column='rating')

    is_active = models.BooleanField(default=True)
    moderation_status = models.CharField(
        max_length=20,
        choices=ModerationStatus.choices,
        default=ModerationStatus.APPROVED,
    )
    moderation_feedback = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = VideoQuerySet.as_manager()

    @property
    def is_published(self):
        return self.is_active and self.moderation_status == self.ModerationStatus.APPROVED

    def __str__(self):
        return self.title


class DigitalFile(models.Model):
    product = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='secure_downloads/%Y/%m/')
    version = models.CharField(max_length=20, default='1.0.0')
    is_main = models.BooleanField(default=True)

    def __str__(self):
        return f"File for {self.product.title}"


class VideoReview(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='reviews', db_column='video_id', null=True, blank=True)
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.rating}★"


class VideoPurchase(models.Model):
    class PaymentStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PAID = 'PAID', 'Paid'
        FAILED = 'FAILED', 'Failed'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Video, on_delete=models.CASCADE, db_column='video_id', null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_status = models.CharField(
        max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PAID
    )
    order_id = models.CharField(max_length=100, blank=True)
    purchased_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} bought {self.product.title}"
