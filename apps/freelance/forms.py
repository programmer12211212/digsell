from django import forms

from apps.freelance.models import (
    FreelanceProject,
    FreelancerProfile,
    PortfolioItem,
    Milestone,
    FreelanceReview,
    Contest,
    ContestSubmission,
)
from apps.freelance.utils import sanitize_text

ALLOWED_FILE_EXTENSIONS = {".pdf", ".doc", ".docx", ".zip", ".png", ".jpg", ".jpeg", ".webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024


class StyledFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = "w-full px-4 py-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-900 dark:text-white focus:outline-none focus:border-primary-500"
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({"class": css, "rows": 5})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({"class": "accent-primary-500"})
            else:
                field.widget.attrs.update({"class": css})


class ProjectForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = FreelanceProject
        fields = [
            "title", "description", "category", "project_type",
            "budget", "hourly_rate", "estimated_hours", "deadline",
        ]
        labels = {
            "title": "Sarlavha",
            "description": "Tavsif",
            "category": "Kategoriya",
            "project_type": "Loyiha turi",
            "budget": "Budjet",
            "hourly_rate": "Soatbay stavka",
            "estimated_hours": "Taxminiy soatlar",
            "deadline": "Muddat",
        }
        widgets = {
            "deadline": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "description": forms.Textarea(attrs={"rows": 6}),
        }

    def clean_description(self):
        return sanitize_text(self.cleaned_data.get("description", ""))


class ProposalForm(StyledFormMixin, forms.Form):
    bid_amount = forms.DecimalField(min_value=1, label="Taklif miqdori")
    delivery_days = forms.IntegerField(min_value=1, max_value=365, label="Yetkazib berish kunlari")
    cover_letter = forms.CharField(widget=forms.Textarea(attrs={"rows": 6}), label="Kuzatuv xati")

    def clean_cover_letter(self):
        return sanitize_text(self.cleaned_data.get("cover_letter", ""), max_length=5000)


class ProfileForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = FreelancerProfile
        fields = ["title", "bio", "hourly_rate", "experience_years", "availability"]
        labels = {
            "title": "Sarlavha (Mutaxassislik)",
            "bio": "Biografiya / Tajriba haqida",
            "hourly_rate": "Soatbay stavka",
            "experience_years": "Tajriba (yillar)",
            "availability": "Ishga tayyorlik",
        }
        widgets = {"bio": forms.Textarea(attrs={"rows": 5})}


class PortfolioForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = PortfolioItem
        fields = ["title", "description", "image", "url"]
        labels = {
            "title": "Sarlavha",
            "description": "Tavsif",
            "image": "Rasm",
            "url": "Havola (URL)",
        }


class MilestoneForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Milestone
        fields = ["title", "description", "amount", "due_date", "order_index"]
        labels = {
            "title": "Sarlavha",
            "description": "Tavsif",
            "amount": "Miqdor",
            "due_date": "Muddat",
            "order_index": "Tartib raqami",
        }
        widgets = {"due_date": forms.DateTimeInput(attrs={"type": "datetime-local"})}


class ReviewForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = FreelanceReview
        fields = ["rating", "comment"]
        labels = {
            "rating": "Reyting",
            "comment": "Izoh",
        }
        widgets = {"comment": forms.Textarea(attrs={"rows": 4})}


class EscrowPaymentForm(forms.Form):
    payment_method = forms.CharField(max_length=50)
    screenshot = forms.ImageField()

    def clean_screenshot(self):
        f = self.cleaned_data["screenshot"]
        if f.size > MAX_FILE_SIZE:
            raise forms.ValidationError("Fayl 10MB dan katta bo'lmasligi kerak.")
        return f


def validate_upload_file(f):
    if f.size > MAX_FILE_SIZE:
        raise forms.ValidationError("Fayl 10MB dan katta.")
    ext = "." + f.name.rsplit(".", 1)[-1].lower() if "." in f.name else ""
    if ext not in ALLOWED_FILE_EXTENSIONS:
        raise forms.ValidationError("Ruxsat etilmagan fayl turi.")
    return f


class ContestForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Contest
        fields = ["title", "description", "category", "reward", "deadline"]
        labels = {
            "title": "Tanlov sarlavhasi",
            "description": "Batafsil shartlar va topshiriq",
            "category": "Kategoriya",
            "reward": "Mukofot jamg'armasi (UZS)",
            "deadline": "Topshirish muddati",
        }
        widgets = {
            "deadline": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "description": forms.Textarea(attrs={"rows": 6}),
        }


class ContestSubmissionForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ContestSubmission
        fields = ["description", "file"]
        labels = {
            "description": "Yuborilgan ish haqida izoh",
            "file": "Dizayn / faylni yuklash",
        }

