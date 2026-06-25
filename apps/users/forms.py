from django import forms
from .models import SellerApplication


class SellerApplicationForm(forms.ModelForm):
    class Meta:
        model = SellerApplication
        fields = ['full_name', 'phone', 'avatar', 'resume', 'skills', 'niche']
        widgets = {
            'resume': forms.Textarea(attrs={'rows': 6}),
            'skills': forms.TextInput(attrs={'placeholder': 'e.g. Photoshop, Figma, Prompt engineering'}),
        }
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(
        label="Ism",
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Ism'})
    )
    last_name = forms.CharField(
        label="Familiya",
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Familiya'})
    )
    phone = forms.CharField(
        label="Telefon raqami",
        required=True,
        widget=forms.TextInput(attrs={'placeholder': '+998 90 123 45 67'})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("first_name", "last_name", "username", "email", "phone")
    
    field_order = ["first_name", "last_name", "username", "email", "phone", "password1", "password2"]

class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = (
            "username",
            "email",
            "role",
            "phone",
            "telegram_id",
            "avatar",
            "loyalty_level",
            "is_verified",
            "is_staff",
            "is_superuser",
            "is_active",
        )
