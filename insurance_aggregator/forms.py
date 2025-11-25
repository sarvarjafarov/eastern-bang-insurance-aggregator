from django import forms
from django.contrib.auth.models import User

from .models import Deal, Offer, UserProfile


class StyledFormMixin:
    def _add_styles(self):
        for field in self.fields.values():
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f"{existing} w-full rounded-lg border border-slate-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-accent".strip()


class SignupForm(StyledFormMixin, forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirm_password']
        widgets = {
            'username': forms.TextInput(attrs={'autocomplete': 'username'}),
            'email': forms.EmailInput(attrs={'autocomplete': 'email'}),
        }

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        confirm = cleaned.get('confirm_password')
        if password and confirm and password != confirm:
            self.add_error('confirm_password', 'Passwords do not match.')
        return cleaned

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._add_styles()
        self.fields['password'].widget.attrs.update({'autocomplete': 'new-password'})
        self.fields['confirm_password'].widget.attrs.update({'autocomplete': 'new-password'})


class ProfileForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['full_name', 'phone', 'organization']
        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'Full name'}),
            'phone': forms.TextInput(attrs={'placeholder': '+1 555 123 4567'}),
            'organization': forms.TextInput(attrs={'placeholder': 'School or organization'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._add_styles()


class DealForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Deal
        fields = ['title', 'description', 'status', 'premium_amount', 'start_date', 'end_date']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._add_styles()


class OfferForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Offer
        fields = ['provider_name', 'summary', 'amount', 'status']
        widgets = {
            'summary': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._add_styles()
