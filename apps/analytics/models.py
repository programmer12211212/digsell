from django.db import models
from django.conf import settings

class PlatformAnalytics(models.Model):
    date = models.DateField(auto_now_add=True)
    total_users = models.PositiveIntegerField(default=0)
    total_sellers = models.PositiveIntegerField(default=0)
    total_sales = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_orders = models.PositiveIntegerField(default=0)
    
    ai_interactions_count = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"Analytics for {self.date}"

class SellerAnalytics(models.Model):
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="seller_stats")
    date = models.DateField(auto_now_add=True)
    revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    orders_count = models.PositiveIntegerField(default=0)
    product_views = models.PositiveIntegerField(default=0)
    
    ai_insight = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.seller.email} stats - {self.date}"
