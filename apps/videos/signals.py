from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Video
from .tasks import convert_video_to_hls_enterprise

@receiver(post_save, sender=Video)
def enqueue_hls_conversion(sender, instance, created, **kwargs):
    """
    Auto-triggers HLS conversion when a new Video Course is added.
    """
    if created and instance.product_type == 'VIDEO' and not instance.hls_root:
        try:
            convert_video_to_hls_enterprise.delay(instance.id)
        except Exception:
            # For production: use proper logging
            pass
