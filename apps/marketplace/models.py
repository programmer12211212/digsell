from django.db import models
from django.conf import settings
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    icon = models.CharField(max_length=50, help_text="Lucide icon name", blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"

    def __str__(self):
        return self.name

class Product(models.Model):
    class ProductType(models.TextChoices):
        PHYSICAL = "PHYSICAL", "Jismoniy mahsulot"
        DIGITAL = "DIGITAL", "Raqamli mahsulot"
        VIDEO_COURSE = "VIDEO_COURSE", "Video kurs"
        EBOOK = "EBOOK", "E-kitob (PDF)"
        SOFTWARE = "SOFTWARE", "Dastur"
        SERVICE = "SERVICE", "Xizmat"
        SOURCE_CODE = "SOURCE_CODE", "Source Code"
        MOBILE_APP = "MOBILE_APP", "Mobil ilova"
        PLUGIN = "PLUGIN", "Plugin"

    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="products")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="products")
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    product_type = models.CharField(max_length=20, choices=ProductType.choices)
    
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    preview_image = models.ImageField(upload_to="products/previews/")
    demo_url = models.URLField(blank=True, null=True)
    
    tags = models.CharField(max_length=255, help_text="Comma separated tags")
    
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    is_sold = models.BooleanField(default=False)
    sales_count = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Mahsulot"
        verbose_name_plural = "Mahsulotlar"
        ordering = ['-created_at']

    def _generate_unique_slug(self):
        slug_base = slugify(self.title)
        slug = slug_base
        counter = 1
        while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{slug_base}-{counter}"
            counter += 1
        return slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class ProductFile(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="files")
    file = models.FileField(upload_to="products/files/")
    version = models.CharField(max_length=20, default="1.0.0")
    changelog = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Mahsulot fayli"
        verbose_name_plural = "Mahsulot fayllari"

    def __str__(self):
        return f"{self.product.title} - {self.version}"


class VideoWishlist(models.Model):
    """Video (asosiy katalog) uchun sevimlilar."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="video_wishlists")
    video = models.ForeignKey('videos.Video', on_delete=models.CASCADE, related_name="wishlisted_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'video')
        verbose_name = "Video istaklar"
        verbose_name_plural = "Video istaklar"

    def __str__(self):
        return f"{self.user.username} - {self.video.title}"


class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wishlists")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wishlisted_by")
    notify_on_discount = models.BooleanField(default=True)
    notify_on_update = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        verbose_name = "Istaklar ro'yxati"
        verbose_name_plural = "Istaklar ro'yxati"

    def __str__(self):
        return f"{self.user.username} - {self.product.title}"
