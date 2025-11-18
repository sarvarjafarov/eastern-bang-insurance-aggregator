from __future__ import annotations

from datetime import timedelta
from typing import Dict, Iterable, Optional
from urllib.parse import urlparse

from django.db.models import F, Sum
from django.utils import timezone

from .models import DailyMetric

METRIC_SESSION_PREFIX = '_metric_recorded_'
SOURCE_PREFIX = 'source:'
PLAN_IMPRESSION_PREFIX = 'plan_impression:'
PLAN_CLICK_PREFIX = 'plan_click:'

SEARCH_ENGINES = ('google.', 'bing.', 'yahoo.', 'duckduckgo.', 'baidu.', 'naver.', 'yandex.')
PAID_UTM_MEDIUMS = {'cpc', 'ppc', 'paid', 'paidsearch', 'display', 'ads'}
EMAIL_HOST_HINTS = ('mail.', 'email.', 'outlook.', 'inbox.')


def _today():
    return timezone.now().date()


def record_metric(metric: str, amount: int = 1, *, date=None) -> None:
    if amount <= 0:
        return
    target_date = date or _today()
    obj, created = DailyMetric.objects.get_or_create(
        date=target_date,
        metric=metric,
        defaults={'count': amount},
    )
    if not created:
        DailyMetric.objects.filter(pk=obj.pk).update(count=F('count') + amount)


def record_metric_once(
    request,
    metric: str,
    *,
    session_key: Optional[str] = None,
    amount: int = 1,
    extras: Optional[Dict[str, int]] = None,
) -> bool:
    if not hasattr(request, 'session'):
        return False
    key = session_key or f'{METRIC_SESSION_PREFIX}{metric}'
    if request.session.get(key):
        return False
    record_metric(metric, amount=amount)
    if extras:
        for extra_metric, extra_amount in extras.items():
            record_metric(extra_metric, amount=extra_amount)
    request.session[key] = True
    request.session.modified = True
    return True


def get_metric_total(metric: str) -> int:
    result = DailyMetric.objects.filter(metric=metric).aggregate(total=Sum('count'))
    return int(result['total'] or 0)


def get_metric_total_for_range(metric: str, *, start, end) -> int:
    result = DailyMetric.objects.filter(metric=metric, date__gte=start, date__lte=end).aggregate(total=Sum('count'))
    return int(result['total'] or 0)


def get_metric_breakdown(prefix: str) -> Iterable[tuple[str, int]]:
    queryset = DailyMetric.objects.filter(metric__startswith=prefix).values('metric').annotate(total=Sum('count'))
    items = []
    for entry in queryset:
        label = entry['metric'][len(prefix):] or 'Unknown'
        items.append((label, int(entry['total'] or 0)))
    items.sort(key=lambda item: item[1], reverse=True)
    return items


def get_metric_change_ratio(metric: str, days: int = 7) -> Optional[float]:
    today = _today()
    current_start = today - timedelta(days=days - 1)
    previous_start = current_start - timedelta(days=days)
    previous_end = current_start - timedelta(days=1)
    current_total = get_metric_total_for_range(metric, start=current_start, end=today)
    previous_total = get_metric_total_for_range(metric, start=previous_start, end=previous_end)
    if previous_total == 0:
        return None
    return (current_total - previous_total) / previous_total


def determine_source_label(request) -> str:
    utm_medium = (request.GET.get('utm_medium') or '').lower()
    utm_source = (request.GET.get('utm_source') or '').lower()
    referer = request.META.get('HTTP_REFERER') or ''
    host = (request.get_host() or '').split(':')[0].lower()

    if utm_medium == 'email':
        return 'Email'
    if utm_medium in PAID_UTM_MEDIUMS:
        return 'Paid Campaigns'
    if utm_source in {'google_ads', 'facebook_ads', 'instagram_ads', 'linkedin_ads'}:
        return 'Paid Campaigns'
    if utm_source:
        return utm_source.replace('-', ' ').title()

    if referer:
        domain = urlparse(referer).netloc.lower()
        if host and domain.endswith(host):
            return 'Direct'
        if any(engine in domain for engine in SEARCH_ENGINES):
            return 'Organic Search'
        if any(hint in domain for hint in EMAIL_HOST_HINTS):
            return 'Email'
        return 'Referral Partners'

    return 'Direct'


def track_acquisition(request) -> None:
    source_label = determine_source_label(request)
    extras = {f'{SOURCE_PREFIX}{source_label}': 1} if source_label else None
    record_metric_once(request, 'acquisition', extras=extras)


def summarize_sources(total_visitors: int) -> list[dict]:
    breakdown = get_metric_breakdown(SOURCE_PREFIX)
    summary = []
    for label, count in breakdown:
        share = int(round((count / total_visitors) * 100)) if total_visitors else 0
        summary.append(
            {
                'label': label,
                'visitors_display': f"{count:,}",
                'share': share,
            }
        )
    return summary


def record_plan_impressions(plans: Iterable[dict]) -> None:
    for plan in plans:
        plan_id = plan.get('plan_id')
        if plan_id is None:
            continue
        record_metric(f'{PLAN_IMPRESSION_PREFIX}{plan_id}')


def record_plan_click(plan_id: int) -> None:
    record_metric(f'{PLAN_CLICK_PREFIX}{plan_id}')


def _plan_totals(prefix: str) -> dict[int, int]:
    queryset = (
        DailyMetric.objects.filter(metric__startswith=prefix)
        .values('metric')
        .annotate(total=Sum('count'))
    )
    totals: dict[int, int] = {}
    for entry in queryset:
        suffix = entry['metric'][len(prefix):]
        try:
            plan_id = int(suffix)
        except (TypeError, ValueError):
            continue
        totals[plan_id] = int(entry['total'] or 0)
    return totals


def get_plan_impression_totals() -> dict[int, int]:
    return _plan_totals(PLAN_IMPRESSION_PREFIX)


def get_plan_click_totals() -> dict[int, int]:
    return _plan_totals(PLAN_CLICK_PREFIX)
