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
