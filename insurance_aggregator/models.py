from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class HomePageContent(TimeStampedModel):
    hero_kicker = models.CharField(max_length=120, default='For international students in the U.S.')
    hero_headline = models.CharField(max_length=255)
    hero_subheadline = models.TextField()
    primary_cta_label = models.CharField(max_length=80, default='Compare Plans')
    primary_cta_url = models.CharField(max_length=255, default='/product/')
    secondary_cta_label = models.CharField(max_length=80, default='Learn more')
    secondary_cta_url = models.CharField(max_length=255, default='/about/')
    trust_heading = models.CharField(max_length=255, default='Trusted by students')
    trust_body = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Home Page Content'
        verbose_name_plural = 'Home Page Content'

    def __str__(self):
        return 'Home Page Content'


class HomeStat(models.Model):
    home_page = models.ForeignKey(HomePageContent, related_name='stats', on_delete=models.CASCADE)
    value = models.CharField(max_length=40)
    label = models.CharField(max_length=120)
    description = models.CharField(max_length=120)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.value} {self.label}"


class HomeFeature(models.Model):
    home_page = models.ForeignKey(HomePageContent, related_name='features', on_delete=models.CASCADE)
    icon = models.CharField(max_length=10, default='✨')
    title = models.CharField(max_length=120)
    description = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class PartnerOrganization(TimeStampedModel):
    name = models.CharField(max_length=150)
    campus = models.CharField(max_length=150, blank=True)
    website = models.URLField(blank=True)
    logo_url = models.URLField('Logo URL')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'University partner'
        verbose_name_plural = 'University partners'

    def __str__(self):
        return self.name


class AboutPageContent(TimeStampedModel):
    kicker = models.CharField(max_length=120, default='Our mission')
    headline = models.CharField(max_length=255)
    intro = models.TextField()

    class Meta:
        verbose_name = 'About Page Content'
        verbose_name_plural = 'About Page Content'

    def __str__(self):
        return 'About Page Content'


class AboutValue(models.Model):
    about_page = models.ForeignKey(AboutPageContent, related_name='values', on_delete=models.CASCADE)
    icon = models.CharField(max_length=10, default='💡')
    title = models.CharField(max_length=120)
    description = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class ProductPageContent(TimeStampedModel):
    kicker = models.CharField(max_length=120, default='Plan builder')
    headline = models.CharField(max_length=255)
    subheadline = models.TextField()
    summary_line = models.CharField(max_length=255, blank=True)
    summary_secondary = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = 'Product Page Content'
        verbose_name_plural = 'Product Page Content'

    def __str__(self):
        return 'Product Page Content'


class AudienceSegment(models.Model):
    slug = models.SlugField(unique=True)
    label = models.CharField(max_length=120)
    description = models.CharField(max_length=255)
    icon = models.CharField(max_length=10, default='👤')
    order = models.PositiveIntegerField(default=0)
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.label


class ContactPageContent(TimeStampedModel):
    kicker = models.CharField(max_length=120, default='We are here to help')
    headline = models.CharField(max_length=255)
    intro = models.TextField()
    support_email = models.EmailField(default='support@insurancebuddy.com')

    class Meta:
        verbose_name = 'Contact Page Content'
        verbose_name_plural = 'Contact Page Content'

    def __str__(self):
        return 'Contact Page Content'


class DailyMetric(TimeStampedModel):
    date = models.DateField()
    metric = models.CharField(max_length=120)
    count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('date', 'metric')
        ordering = ['-date', 'metric']

    def __str__(self):
        return f"{self.metric} · {self.date} · {self.count}"


class UserProfile(TimeStampedModel):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    organization = models.CharField(max_length=120, blank=True)
    preferred_member = models.CharField(max_length=40, blank=True)
    preferred_city = models.CharField(max_length=120, blank=True)
    budget_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    budget_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    preferred_providers = models.CharField(max_length=255, blank=True)
    deductible_preference = models.CharField(max_length=40, blank=True)
    language = models.CharField(max_length=20, blank=True)
    comms_email = models.BooleanField(default=True)
    comms_push = models.BooleanField(default=False)

    def __str__(self):
        return self.full_name or self.user.get_username()


class Pack(TimeStampedModel):
    STATUS_CHOICES = [
        ('saved', 'Saved'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='packs')
    plan_id = models.IntegerField(null=True, blank=True)
    plan_name = models.CharField(max_length=200)
    provider_name = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='saved')
    premium_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    selected_addons = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ['-updated_at', '-created_at']

    def __str__(self):
        return f"{self.plan_name} ({self.get_status_display()})"


class Review(TimeStampedModel):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='reviews')
    plan_id = models.IntegerField()
    plan_name = models.CharField(max_length=200)
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    title = models.CharField(max_length=120, blank=True)
    body = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['plan_id']),
        ]

    def __str__(self):
        return f"{self.plan_name} · {self.rating}★"


class Activity(TimeStampedModel):
    ACTION_CHOICES = [
        ('saved_plan', 'Saved plan'),
        ('updated_addons', 'Updated add-ons'),
        ('review_submitted', 'Review submitted'),
        ('viewed_plan', 'Viewed plan'),
        ('document_added', 'Document added'),
        ('support_opened', 'Support opened'),
        ('billing_updated', 'Billing updated'),
    ]

    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=40, choices=ACTION_CHOICES)
    plan_id = models.IntegerField(null=True, blank=True)
    plan_name = models.CharField(max_length=200, blank=True)
    meta = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['plan_id']),
        ]

    def __str__(self):
        return f"{self.user} · {self.get_action_display()}"


class Document(TimeStampedModel):
    STATUS_CHOICES = [
        ('pending', 'Pending review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    TYPE_CHOICES = [
        ('id', 'ID / Passport'),
        ('coverage', 'Proof of coverage'),
        ('claim', 'Claim receipt'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=150)
    doc_type = models.CharField(max_length=40, choices=TYPE_CHOICES, default='other')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    file_url = models.URLField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-updated_at', '-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"


class Notification(TimeStampedModel):
    TYPE_CHOICES = [
        ('renewal', 'Renewal'),
        ('plan_update', 'Plan update'),
        ('claim', 'Claim'),
        ('review', 'Review'),
        ('general', 'General'),
    ]
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=150)
    body = models.TextField(blank=True)
    notif_type = models.CharField(max_length=40, choices=TYPE_CHOICES, default='general')
    link = models.URLField(blank=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['is_read', '-created_at']

    def __str__(self):
        return f"{self.title} ({'read' if self.is_read else 'unread'})"


class SupportTicket(TimeStampedModel):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In progress'),
        ('closed', 'Closed'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
    ]

    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='tickets')
    subject = models.CharField(max_length=200)
    body = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    link = models.URLField(blank=True)
    resolution = models.TextField(blank=True)

    class Meta:
        ordering = ['-updated_at', '-created_at']

    def __str__(self):
        return f"{self.subject} ({self.get_status_display()})"


class BillingRecord(TimeStampedModel):
    STATUS_CHOICES = [
        ('due', 'Due'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
    ]
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='billing_records')
    title = models.CharField(max_length=150)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='due')
    due_date = models.DateField(null=True, blank=True)
    invoice_url = models.URLField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-updated_at', '-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
