from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.safestring import mark_safe

from .models import SellerApplication, User


class SellerApplicationForm(forms.ModelForm):
    agreed_to_terms = forms.BooleanField(
        label=mark_safe(
            'Men <a href="/terms" target="_blank" class="text-primary-500 hover:text-primary-400 underline">Terms of Service</a> va '
            '<a href="/privacy" target="_blank" class="text-primary-500 hover:text-primary-400 underline">Privacy Policy</a> ga roziman'
        ),
        required=True,
        error_messages={
            'required': 'Sotuvchi bo‘lish uchun Terms of Service va Privacy Policy ga rozilik bildirish shart.'
        }
    )

    class Meta:
        model = SellerApplication
        fields = [
            'full_name', 'phone', 'email', 'telegram_username', 'country', 'city',
            'resume', 'experience', 'skills', 'niche', 'what_to_sell',
            'website', 'portfolio', 'avatar', 'identity_document', 'agreed_to_terms'
        ]
        widgets = {
            'resume': forms.Textarea(attrs={'rows': 5}),
            'experience': forms.Textarea(attrs={'rows': 5}),
            'portfolio': forms.Textarea(attrs={'rows': 4}),
            'skills': forms.TextInput(attrs={'placeholder': 'e.g. Photoshop, Figma, Prompt engineering'}),
            'what_to_sell': forms.TextInput(attrs={'placeholder': 'Qaysi mahsulotlar yoki xizmatlar'}),
            'website': forms.URLInput(attrs={'placeholder': 'https://example.com'}),
            'telegram_username': forms.TextInput(attrs={'placeholder': '@telegram_username'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != 'agreed_to_terms':
                field.widget.attrs.update({
                    'class': 'w-full rounded-2xl bg-slate-950/90 border border-slate-800 px-4 py-3 text-sm text-slate-100 outline-none transition focus:ring-2 focus:ring-primary-500/30 focus:border-primary-400',
                    'autocomplete': 'off',
                })
            else:
                field.widget.attrs.update({
                    'class': 'h-4 w-4 text-primary-500 focus:ring-primary-400 rounded',
                })

    def clean_agreed_to_terms(self):
        agreed = self.cleaned_data.get('agreed_to_terms')
        if not agreed:
            raise forms.ValidationError('Sotuvchi bo‘lish uchun Terms of Service va Privacy Policy ga rozilik bildirish shart.')
        return agreed


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
    accept_terms = forms.BooleanField(
        label=mark_safe(
            'Men <a href="/terms" target="_blank" class="text-primary-500 hover:text-primary-400 underline">Terms of Service</a> va '
            '<a href="/privacy" target="_blank" class="text-primary-500 hover:text-primary-400 underline">Privacy Policy</a> ga roziman'
        ),
        required=True,
        error_messages={
            'required': 'Foydalanish shartlari va Maxfiylik siyosatiga rozilik berish shart.'
        }
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("first_name", "last_name", "username", "email", "phone", "accept_terms")
    
    field_order = ["first_name", "last_name", "username", "email", "phone", "password1", "password2", "accept_terms"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        base_classes = 'w-full rounded-2xl bg-slate-950/90 border border-slate-800 px-4 py-3 text-sm text-slate-100 outline-none transition focus:ring-2 focus:ring-primary-500/30 focus:border-primary-400'
        for name, field in self.fields.items():
            if name != 'accept_terms':
                field.widget.attrs.update({
                    'class': base_classes,
                    'autocomplete': 'off',
                })
        self.fields['accept_terms'].widget.attrs.update({
            'class': 'h-4 w-4 text-primary-500 focus:ring-primary-400 rounded',
            'id': 'acceptTermsCheckbox'
        })

    def clean_accept_terms(self):
        accepted = self.cleaned_data.get('accept_terms')
        if not accepted:
            raise forms.ValidationError('Roʻyxatdan oʻtish uchun Terms of Service va Privacy Policy ga rozilik bildirishingiz kerak.')
        return accepted

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
