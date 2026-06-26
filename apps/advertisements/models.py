"""
Advertisement System Models
Supports multiple banner types with scheduling, priority, and targeting.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
import uuid


class BannerType(models.TextChoices):
    """All supported advertisement banner types."""
    HERO_SLIDER = 'hero_slider', 'Hero Slider'
    PROMOTION = 'promotion', 'Promotion Banner'
    CARD = 'card', 'Advertisement Card'
    ALERT = 'alert', 'Alert Banner'
    CAROUSEL = 'carousel', 'Carousel Banner'
    SIDEBAR = 'sidebar', 'Sidebar Banner'
    CATEGORY = 'category', 'Category Banner'
    PRODUCT = 'product', 'Product Banner'
    MARKETPLACE = 'marketplace', 'Marketplace Banner'
    ANNOUNCEMENT = 'announcement', 'Announcement Banner'
    DISCOUNT = 'discount', 'Discount Banner'
    FULL_WIDTH = 'full_width', 'Full Width Banner'
    INLINE = 'inline', 'Inline Banner'
    FLOATING = 'floating', 'Floating Banner'
    POPUP = 'popup', 'Popup Campaign'


class AlertType(models.TextChoices):
    """Alert banner types."""
    SUCCESS = 'success', 'Success'
    INFO = 'info', 'Info'
    WARNING = 'warning', 'Warning'
    DANGER = 'danger', 'Danger'
    ANNOUNCEMENT = 'announcement', 'Announcement'
    SYSTEM = 'system', 'System Update'
    MAINTENANCE = 'maintenance', 'Maintenance'
    PROMOTION = 'promotion', 'Promotion'


class DisplayPosition(models.TextChoices):
    """Where banners can be displayed."""
    TOP = 'top', 'Top of Page'
    HERO = 'hero', 'Hero Section'
    ABOVE_CONTENT = 'above_content', 'Above Content'
    SIDEBAR_TOP = 'sidebar_top', 'Sidebar Top'
    SIDEBAR_MIDDLE = 'sidebar_middle', 'Sidebar Middle'
    SIDEBAR_BOTTOM = 'sidebar_bottom', 'Sidebar Bottom'
    INLINE_CONTENT = 'inline_content', 'Inline Content'
    BELOW_CONTENT = 'below_content', 'Below Content'
    FOOTER_TOP = 'footer_top', 'Footer Top'
    FOOTER = 'footer', 'Footer'
    FLOATING = 'floating', 'Floating'
    MODAL = 'modal', 'Modal/Popup'
    MARKETPLACE_TOP = 'marketplace_top', 'Marketplace Top'
    MARKETPLACE_SIDEBAR = 'marketplace_sidebar', 'Marketplace Sidebar'
    CATEGORY_TOP = 'category_top', 'Category Top'
    PRODUCT_TOP = 'product_top', 'Product Top'


class DeviceTarget(models.TextChoices):
    """Target devices for displaying banners."""
    ALL = 'all', 'All Devices'
    DESKTOP = 'desktop', 'Desktop Only'
    TABLET = 'tablet', 'Tablet Only'
    MOBILE = 'mobile', 'Mobile Only'
    MOBILE_TABLET = 'mobile_tablet', 'Mobile & Tablet'
    DESKTOP_TABLET = 'desktop_tablet', 'Desktop & Tablet'


class Advertisement(models.Model):
    """
    Main Advertisement/Banner model.
    Supports all banner types with dynamic scheduling and targeting.
    """
    
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'
        ARCHIVED = 'archived', 'Archived'
    
    # Basic Info
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, help_text="Banner title (internal use)")
    description = models.TextField(blank=True, help_text="Internal notes about this banner")
    
    # Banner Type & Position
    banner_type = models.CharField(
        max_length=30,
        choices=BannerType.choices,
        default=BannerType.HERO_SLIDER,
        help_text="Type of banner"
    )
    position = models.CharField(
        max_length=30,
        choices=DisplayPosition.choices,
        default=DisplayPosition.TOP,
        help_text="Where this banner appears"
    )
    
    # Content
    heading = models.CharField(
        max_length=200,
        blank=True,
        help_text="Main heading text"
    )
    subheading = models.CharField(
        max_length=300,
        blank=True,
        help_text="Subheading text"
    )
    content = models.TextField(
        blank=True,
        help_text="Main content/description"
    )
    
    # Images
    image = models.ImageField(
        upload_to='banners/%Y/%m/',
        blank=True,
        null=True,
        help_text="Main banner image (desktop)"
    )
    mobile_image = models.ImageField(
        upload_to='banners/mobile/%Y/%m/',
        blank=True,
        null=True,
        help_text="Mobile-optimized image"
    )
    thumbnail = models.ImageField(
        upload_to='banners/thumbnails/%Y/%m/',
        blank=True,
        null=True,
        help_text="Thumbnail for carousel/card"
    )
    
    # CTA Button
    cta_text = models.CharField(
        max_length=100,
        blank=True,
        default="Click Here",
        help_text="Button text"
    )
    cta_url = models.URLField(
        blank=True,
        help_text="Button link URL"
    )
    cta_target_blank = models.BooleanField(
        default=False,
        help_text="Open link in new tab"
    )
    
    # Styling & Animation
    background_color = models.CharField(
        max_length=7,
        blank=True,
        default="#0a0a1a",
        help_text="Background color (hex code)"
    )
    gradient = models.CharField(
        max_length=255,
        blank=True,
        help_text="CSS gradient (e.g., 'from-violet-500 to-indigo-600')"
    )
    text_color = models.CharField(
        max_length=7,
        blank=True,
        default="#ffffff",
        help_text="Text color (hex code)"
    )
    animation_style = models.CharField(
        max_length=50,
        blank=True,
        default="fade",
        choices=[
            ('fade', 'Fade In'),
            ('slide-left', 'Slide Left'),
            ('slide-right', 'Slide Right'),
            ('slide-up', 'Slide Up'),
            ('slide-down', 'Slide Down'),
            ('scale', 'Scale'),
            ('bounce', 'Bounce'),
            ('pulse', 'Pulse'),
            ('glow', 'Glow'),
        ],
        help_text="Animation style"
    )
    animation_duration = models.IntegerField(
        default=500,
        help_text="Animation duration in milliseconds"
    )
    
    # Alert-specific
    alert_type = models.CharField(
        max_length=20,
        choices=AlertType.choices,
        blank=True,
        default=AlertType.INFO,
        help_text="Alert type (for alert banners)"
    )
    is_closable = models.BooleanField(
        default=True,
        help_text="Allow user to close alert"
    )
    
    # Promotion-specific
    discount_label = models.CharField(
        max_length=50,
        blank=True,
        help_text="Discount badge text (e.g., '50% OFF')"
    )
    has_countdown = models.BooleanField(
        default=False,
        help_text="Show countdown timer"
    )
    countdown_text = models.CharField(
        max_length=100,
        blank=True,
        default="Offer ends in",
        help_text="Countdown label"
    )
    
    # Scheduling
    start_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When banner becomes active"
    )
    end_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When banner expires"
    )
    
    # Targeting
    device_target = models.CharField(
        max_length=20,
        choices=DeviceTarget.choices,
        default=DeviceTarget.ALL,
        help_text="Target specific devices"
    )
    target_category = models.ForeignKey(
        'marketplace.Category',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="Show only in this category"
    )
    target_product = models.ForeignKey(
        'videos.Video',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="Show only for this product"
    )
    
    # Priority & Display
    priority = models.IntegerField(
        default=0,
        help_text="Higher = shown first (0-100)"
    )
    display_order = models.IntegerField(
        default=0,
        help_text="Order within same priority"
    )
    max_impressions = models.IntegerField(
        blank=True,
        null=True,
        help_text="Max times to show (leave empty for unlimited)"
    )
    current_impressions = models.IntegerField(
        default=0,
        editable=False,
        help_text="Current impression count"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        help_text="Banner status"
    )
    
    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_advertisements'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-priority', 'display_order', '-created_at']
        indexes = [
            models.Index(fields=['status', '-priority']),
            models.Index(fields=['position', 'status']),
            models.Index(fields=['banner_type', 'status']),
        ]
        verbose_name = "Advertisement"
        verbose_name_plural = "Advertisements"
    
    def __str__(self):
        return f"{self.title} ({self.get_banner_type_display()})"
    
    def is_active(self):
        """Check if banner is currently active based on schedule and status."""
        if self.status != self.Status.ACTIVE:
            return False
        
        now = timezone.now()
        
        if self.start_date and now < self.start_date:
            return False
        
        if self.end_date and now > self.end_date:
            return False
        
        if self.max_impressions and self.current_impressions >= self.max_impressions:
            return False
        
        return True
    
    def increment_impression(self):
        """Increment impression count."""
        self.current_impressions += 1
        self.save(update_fields=['current_impressions'])
    
    def save(self, *args, **kwargs):
        """Set created_by if not set."""
        super().save(*args, **kwargs)
    
    def get_device_css_class(self):
        """Get CSS class for device targeting."""
        device_classes = {
            DeviceTarget.ALL: '',
            DeviceTarget.DESKTOP: 'hidden lg:block',
            DeviceTarget.TABLET: 'hidden md:block lg:hidden',
            DeviceTarget.MOBILE: 'block md:hidden',
            DeviceTarget.MOBILE_TABLET: 'block lg:hidden',
            DeviceTarget.DESKTOP_TABLET: 'hidden md:block',
        }
        return device_classes.get(self.device_target, '')


class BannerGroup(models.Model):
    """
    Group related banners together.
    Useful for hero sliders, carousels, and related promotions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="Group name (e.g., 'Homepage Hero Slider')")
    description = models.TextField(blank=True)
    banner_type = models.CharField(
        max_length=30,
        choices=BannerType.choices,
        help_text="Type of banners in this group"
    )
    position = models.CharField(
        max_length=30,
        choices=DisplayPosition.choices,
        help_text="Display position"
    )
    banners = models.ManyToManyField(
        Advertisement,
        related_name='groups',
        help_text="Banners in this group"
    )
    
    # Carousel/Slider settings
    autoplay = models.BooleanField(default=True)
    autoplay_delay = models.IntegerField(
        default=5000,
        help_text="Delay in milliseconds"
    )
    loop_enabled = models.BooleanField(default=True)
    show_navigation = models.BooleanField(default=True)
    show_indicators = models.BooleanField(default=True)
    animation_duration = models.IntegerField(default=500)
    
    status = models.CharField(
        max_length=20,
        choices=Advertisement.Status.choices,
        default=Advertisement.Status.ACTIVE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['banner_type', 'name']
        verbose_name = "Banner Group"
        verbose_name_plural = "Banner Groups"
    
    def __str__(self):
        return f"{self.name} ({self.banner_type})"
    
    def get_active_banners(self):
        """Get all active banners in this group."""
        return self.banners.filter(
            status=Advertisement.Status.ACTIVE
        ).filter(
            models.Q(start_date__isnull=True) | models.Q(start_date__lte=timezone.now())
        ).filter(
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=timezone.now())
        ).order_by('-priority', 'display_order')


class AdvertisementClick(models.Model):
    """Track banner clicks for analytics."""
    advertisement = models.ForeignKey(
        Advertisement,
        on_delete=models.CASCADE,
        related_name='clicks'
    )
    clicked_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    user_ip = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-clicked_at']
        verbose_name = "Advertisement Click"
        verbose_name_plural = "Advertisement Clicks"
    
    def __str__(self):
        return f"{self.advertisement.title} - {self.clicked_at}"


class AdvertisementImpression(models.Model):
    """Track banner impressions for analytics."""
    advertisement = models.ForeignKey(
        Advertisement,
        on_delete=models.CASCADE,
        related_name='impressions'
    )
    viewed_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    user_ip = models.GenericIPAddressField(blank=True, null=True)
    device = models.CharField(max_length=20, blank=True)
    
    class Meta:
        ordering = ['-viewed_at']
        verbose_name = "Advertisement Impression"
        verbose_name_plural = "Advertisement Impressions"
    
    def __str__(self):
        return f"{self.advertisement.title} - {self.viewed_at}"
