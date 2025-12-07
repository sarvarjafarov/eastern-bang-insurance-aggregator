from django.contrib import admin

from . import models


class HomeStatInline(admin.TabularInline):
    model = models.HomeStat
    extra = 1


class HomeFeatureInline(admin.TabularInline):
    model = models.HomeFeature
    extra = 1


@admin.register(models.HomePageContent)
class HomePageContentAdmin(admin.ModelAdmin):
    inlines = [HomeStatInline, HomeFeatureInline]
    list_display = ('hero_headline', 'updated_at')


@admin.register(models.PartnerOrganization)
class PartnerOrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'campus', 'order')
    list_editable = ('order',)


class AboutValueInline(admin.TabularInline):
    model = models.AboutValue
    extra = 1


@admin.register(models.AboutPageContent)
class AboutPageContentAdmin(admin.ModelAdmin):
    inlines = [AboutValueInline]
    list_display = ('headline', 'updated_at')


@admin.register(models.ProductPageContent)
class ProductPageContentAdmin(admin.ModelAdmin):
    list_display = ('headline', 'updated_at')


@admin.register(models.AudienceSegment)
class AudienceSegmentAdmin(admin.ModelAdmin):
    list_display = ('label', 'slug', 'order', 'is_default')
    list_editable = ('order', 'is_default')


@admin.register(models.ContactPageContent)
class ContactPageContentAdmin(admin.ModelAdmin):
    list_display = ('headline', 'support_email', 'updated_at')


@admin.register(models.SiteMetadata)
class SiteMetadataAdmin(admin.ModelAdmin):
    list_display = ('meta_title', 'updated_at')
    fieldsets = (
        (None, {'fields': ('meta_title', 'meta_description')}),
        ('Images', {'fields': ('meta_image_path',)}),
    )

    def has_add_permission(self, request):
        if models.SiteMetadata.objects.exists():
            return False
        return super().has_add_permission(request)
