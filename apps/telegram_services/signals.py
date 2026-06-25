from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import TelegramProduct


@receiver(post_save, sender=TelegramProduct)
def invalidate_product_cache(sender, instance, created, **kwargs):
    """Invalidate cache when product is saved"""
    cache.delete(f'product_{instance.id}')
    cache.delete('products_list')
    cache.delete(f'category_{instance.category.name}_products')


@receiver(post_delete, sender=TelegramProduct)
def invalidate_cache_on_delete(sender, instance, **kwargs):
    """Invalidate cache when product is deleted"""
    cache.delete(f'product_{instance.id}')
    cache.delete('products_list')
    cache.delete(f'category_{instance.category.name}_products')
