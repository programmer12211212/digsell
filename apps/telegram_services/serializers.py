from rest_framework import serializers
from .models import (
    TelegramProduct, TelegramProductCategory, TelegramOrder,
    TelegramPayment, TelegramNotification, TelegramProvider, TelegramGift
)


class TelegramProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramProductCategory
        fields = ['id', 'name', 'display_name', 'icon', 'color']


class TelegramProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.display_name', read_only=True)
    is_available = serializers.SerializerMethodField()
    
    class Meta:
        model = TelegramProduct
        fields = [
            'id', 'name', 'description', 'category_name', 'quantity', 'unit',
            'price_uzs', 'price_usd', 'icon', 'is_available', 'is_featured',
            'created_at'
        ]
    
    def get_is_available(self, obj):
        return obj.is_available


class TelegramOrderSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = TelegramOrder
        fields = [
            'id', 'unique_code', 'product_name', 'status', 'telegram_username',
            'base_price', 'unique_amount', 'payment_method', 'created_at',
            'completed_at', 'user_email'
        ]
        read_only_fields = ['id', 'unique_code', 'status', 'created_at']


class TelegramPaymentSerializer(serializers.ModelSerializer):
    order_code = serializers.CharField(source='order.unique_code', read_only=True)
    
    class Meta:
        model = TelegramPayment
        fields = [
            'id', 'order_code', 'amount', 'currency', 'payment_status',
            'payment_method', 'created_at', 'confirmed_at'
        ]
        read_only_fields = ['id', 'created_at']


class TelegramNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramNotification
        fields = [
            'id', 'notification_type', 'title', 'message', 'is_read',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class TelegramGiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramGift
        fields = [
            'id', 'name', 'description', 'image', 'price_uzs',
            'provider', 'is_active', 'created_at'
        ]


class TelegramProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramProvider
        fields = [
            'id', 'name', 'is_active', 'is_test', 'balance',
            'stars_balance', 'premium_balance', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
