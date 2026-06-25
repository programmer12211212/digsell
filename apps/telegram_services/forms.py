from django import forms
from django.core.exceptions import ValidationError
from .models import TelegramOrder, TelegramProduct
import re


class TelegramOrderForm(forms.ModelForm):
    """Form for creating Telegram Orders"""
    
    telegram_username = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '@username',
            'autocomplete': 'off',
        }),
        help_text='Enter your Telegram username without @'
    )
    
    class Meta:
        model = TelegramOrder
        fields = ['telegram_username']
    
    def clean_telegram_username(self):
        username = self.cleaned_data.get('telegram_username', '')
        
        # Remove @ if present
        if username.startswith('@'):
            username = username[1:]
        
        # Validate format
        if not re.match(r'^\w{5,32}$', username):
            raise ValidationError(
                'Username must be 5-32 characters and contain only letters, numbers, and underscores.'
            )
        
        return username


class ProductFilterForm(forms.Form):
    """Form for filtering Telegram Products"""
    
    CATEGORY_CHOICES = [
        ('', 'All Categories'),
        ('stars', 'Telegram Stars'),
        ('premium', 'Telegram Premium'),
        ('gifts', 'Telegram Gifts'),
    ]
    
    SORT_CHOICES = [
        ('-created_at', 'Newest'),
        ('price_asc', 'Price: Low to High'),
        ('price_desc', 'Price: High to Low'),
        ('name', 'Name: A to Z'),
    ]
    
    RARITY_CHOICES = [
        ('', 'All Rarities'),
        ('common', 'Common'),
        ('rare', 'Rare'),
        ('epic', 'Epic'),
        ('legendary', 'Legendary'),
    ]
    
    rarity = forms.ChoiceField(
        choices=RARITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    category = forms.ChoiceField(
        choices=CATEGORY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    sort_by = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search products...',
        })
    )


class PaymentConfirmationForm(forms.Form):
    """Form for payment confirmation"""
    
    payment_screenshot = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    
    confirmation_note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Additional details...'
        })
    )
