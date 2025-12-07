from django.conf import settings


def analytics_ids(request):
    """Expose analytics IDs to templates without hardcoding values."""
    return {
        'GA_MEASUREMENT_ID': getattr(settings, 'GA_MEASUREMENT_ID', ''),
        'YANDEX_METRICA_ID': getattr(settings, 'YANDEX_METRICA_ID', ''),
    }
