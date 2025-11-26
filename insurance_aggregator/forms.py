from django import forms
from django.contrib.auth.models import User

from .models import BillingRecord, Document, Pack, Review, SupportTicket, UserProfile


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
        fields = [
            'full_name',
            'phone',
            'organization',
            'preferred_member',
            'preferred_city',
            'budget_min',
            'budget_max',
            'preferred_providers',
            'deductible_preference',
            'language',
            'comms_email',
            'comms_push',
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'Full name'}),
            'phone': forms.TextInput(attrs={'placeholder': '+1 555 123 4567'}),
            'organization': forms.TextInput(attrs={'placeholder': 'School or organization'}),
            'preferred_member': forms.TextInput(attrs={'placeholder': 'adult/child/family/etc.'}),
            'preferred_city': forms.TextInput(attrs={'placeholder': 'Default city'}),
            'budget_min': forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'Min budget'}),
            'budget_max': forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'Max budget'}),
            'preferred_providers': forms.TextInput(attrs={'placeholder': 'Comma-separated providers'}),
            'deductible_preference': forms.TextInput(attrs={'placeholder': 'Low/Medium/High'}),
            'language': forms.TextInput(attrs={'placeholder': 'en-US'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._add_styles()


class PackForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Pack
        fields = [
            'plan_name',
            'provider_name',
            'plan_id',
            'city',
            'status',
            'premium_amount',
            'start_date',
            'end_date',
            'notes',
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._add_styles()


class ReviewForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'title', 'body']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._add_styles()


class DocumentForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'doc_type', 'file_url', 'status', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
            'file_url': forms.URLInput(attrs={'placeholder': 'Link to file or cloud storage'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._add_styles()


class SupportTicketForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ['subject', 'body', 'priority', 'link']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 3}),
            'link': forms.URLInput(attrs={'placeholder': 'Optional link'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._add_styles()


class BillingRecordForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = BillingRecord
        fields = ['title', 'amount', 'status', 'due_date', 'invoice_url', 'notes']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
            'invoice_url': forms.URLInput(attrs={'placeholder': 'Invoice link (optional)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._add_styles()
