from django.conf import settings
from django.db import OperationalError, ProgrammingError
from django.templatetags.static import static

from .models import SiteMetadata


def analytics_ids(request):
    """Expose analytics IDs to templates without hardcoding values."""
    return {
        'GA_MEASUREMENT_ID': getattr(settings, 'GA_MEASUREMENT_ID', ''),
        'YANDEX_METRICA_ID': getattr(settings, 'YANDEX_METRICA_ID', ''),
    }


def site_metadata(request):
    """Provide meta title/description/image for templates."""
    default_title = 'Insurance Buddy'
    default_description = 'Insurance Buddy helps international students compare travel and health insurance plans designed for life in the U.S.'
    default_image_path = 'img/insure-buddy-meta-image.png'

    title = default_title
    description = default_description
    image_path = default_image_path

    try:
        meta = SiteMetadata.objects.order_by('-updated_at').first()
    except (OperationalError, ProgrammingError):
        meta = None

    if meta:
        title = meta.meta_title or default_title
        description = meta.meta_description or default_description
        image_path = meta.meta_image_path or default_image_path

    if image_path and not image_path.startswith(('http://', 'https://')):
        image_path = static(image_path.lstrip('/'))

    absolute_image_url = ''
    if image_path and request:
        try:
            absolute_image_url = request.build_absolute_uri(image_path)
        except Exception:
            absolute_image_url = image_path

    return {
        'SITE_META_TITLE': title,
        'SITE_META_DESCRIPTION': description,
        'SITE_META_IMAGE': absolute_image_url,
        'SITE_META_URL': request.build_absolute_uri() if request else '',
    }
