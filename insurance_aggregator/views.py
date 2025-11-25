import json
import os
import random
from datetime import date
from typing import Optional
from types import SimpleNamespace

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import OperationalError, ProgrammingError
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.templatetags.static import static
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .forms import PackForm, ProfileForm, SignupForm
from .analytics import (
    record_metric,
    record_metric_once,
    track_acquisition,
    get_metric_total,
    get_metric_change_ratio,
    summarize_sources,
    record_plan_impressions,
    record_plan_click,
    get_plan_impression_totals,
    get_plan_click_totals,
)
from .data_loader import comparison_fields, filter_plans, get_plan_by_id, get_unique_cities, load_plan_catalog, summarize_plans
from .models import (
    AboutPageContent,
    AudienceSegment,
    ContactPageContent,
    HomePageContent,
    PartnerOrganization,
    ProductPageContent,
    Pack,
    UserProfile,
)

MEMBER_OPTIONS = [
    {'value': 'adult', 'label': 'Adult Student', 'description': 'Age 18–64 coverage', 'icon': '👤'},
    {'value': 'child', 'label': 'Child / Dependent', 'description': 'K-12 or dependent visa', 'icon': '🧒'},
    {'value': 'family', 'label': 'Family', 'description': 'Plans that cover both adults & kids', 'icon': '👨‍👩‍👦'},
    {'value': 'government', 'label': 'Gov & Public Programs', 'description': 'Medicaid, CHIP, TRICARE, etc.', 'icon': '🏛️'},
]

DEFAULT_AGE = 24
TRAFFIC_API_KEY = os.environ.get('TRAFFIC_API_KEY')
TEAM_NICKNAMES = [
    nickname.strip()
    for nickname in os.environ.get(
        'TEAM_NICKNAMES',
        'cheerful-newt, careful-deer, silly-elephant, clever-crocodile, eastern-bang',
    ).split(',')
    if nickname.strip()
]
# Default to the IDs already used on the main site so analytics remain consistent.
GA_MEASUREMENT_ID = os.environ.get('GA_MEASUREMENT_ID', 'G-2EYT060RY4')
YANDEX_METRICA_ID = os.environ.get('YANDEX_METRICA_ID', '105393946')


def _strip_reference(value):
    if isinstance(value, str) and ':contentReference' in value:
        return value.split(':contentReference', 1)[0]
    return value


def _get_or_create_profile(user: User) -> UserProfile:
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def _default_home_content():
    return {
        'hero_kicker': 'For international students in the U.S.',
        'hero_headline': 'Find the Right Travel & Health Insurance in Minutes.',
        'hero_subheadline': (
            'Compare trusted providers, check your eligibility, and get covered today. '
            'Insurance Buddy surfaces the best options with real-time data and intuitive filters '
            'inspired by the way students actually search.'
        ),
        'primary_cta_label': 'Compare Plans',
        'primary_cta_url': '/product/',
        'secondary_cta_label': 'Learn more',
        'secondary_cta_url': '/about/',
        'trust_heading': 'Trusted by students',
        'trust_body': 'From New Haven to Los Angeles, campus teams rely on Insurance Buddy.',
    }


def _default_home_stats():
    return [
        {'value': '92+', 'label': 'Active plans', 'description': 'Live data'},
        {'value': '18', 'label': 'Trusted insurers', 'description': 'Global network'},
        {'value': '48 hrs', 'label': 'Average approval', 'description': 'Fast onboarding'},
    ]


def _default_features():
    return [
        {'icon': '⚡️', 'title': 'Real-Time Data', 'description': 'We gather data from trusted providers automatically.'},
        {'icon': '🎛️', 'title': 'Smart Filters', 'description': 'Sort by price, coverage, or plan type with one tap.'},
        {'icon': '🎓', 'title': 'Student-Focused', 'description': 'Tailored for international students studying in the U.S.'},
    ]


def _default_partners():
    return [
        {
            'name': 'Yale University',
            'logo_url': static('img/partners/yale.svg'),
            'website': 'https://www.yale.edu/',
            'campus': 'New Haven, CT',
        },
        {
            'name': 'Massachusetts Institute of Technology',
            'logo_url': static('img/partners/mit.svg'),
            'website': 'https://www.mit.edu/',
            'campus': 'Cambridge, MA',
        },
        {
            'name': 'Columbia University',
            'logo_url': static('img/partners/columbia.svg'),
            'website': 'https://www.columbia.edu/',
            'campus': 'New York, NY',
        },
        {
            'name': 'University of California, Los Angeles',
            'logo_url': static('img/partners/ucla.svg'),
            'website': 'https://www.ucla.edu/',
            'campus': 'Los Angeles, CA',
        },
        {
            'name': 'Rice University',
            'logo_url': static('img/partners/rice.svg'),
            'website': 'https://www.rice.edu/',
            'campus': 'Houston, TX',
        },
    ]


def home(request):
    track_acquisition(request)
    try:
        home_page = HomePageContent.objects.prefetch_related('features', 'stats').first()
    except (OperationalError, ProgrammingError):
        home_page = None

    try:
        partners = list(PartnerOrganization.objects.values('name', 'campus', 'website', 'logo_url'))
    except (OperationalError, ProgrammingError):
        partners = []

    if home_page:
        try:
            features = list(home_page.features.values('icon', 'title', 'description'))
        except (OperationalError, ProgrammingError):
            features = _default_features()
        try:
            stats = list(home_page.stats.values('value', 'label', 'description'))
        except (OperationalError, ProgrammingError):
            stats = _default_home_stats()
        home_data = home_page
    else:
        features = _default_features()
        stats = _default_home_stats()
        home_data = SimpleNamespace(**_default_home_content())

    partners = partners or _default_partners()
    for index, partner in enumerate(partners):
        partner['delay'] = f'{0.1 * index:.1f}s'

    context = {
        'home_content': home_data,
        'home_features': features,
        'home_stats': stats,
        'partner_universities': partners,
    }
    return render(request, 'home.html', context)


def about(request):
    track_acquisition(request)
    try:
        about_page = AboutPageContent.objects.prefetch_related('values').first()
    except (OperationalError, ProgrammingError):
        about_page = None

    values = []
    if about_page:
        try:
            values = list(about_page.values.all())
        except (OperationalError, ProgrammingError):
            values = []

    if not about_page:
        about_page = SimpleNamespace(
            kicker='Our mission',
            headline='We make insurance simple for international students.',
            intro=(
                'Insurance Buddy blends human support with automation so that every student '
                'can secure the right coverage for study, travel, and everyday campus life.'
            ),
        )

    if not values:
        values = [
            SimpleNamespace(icon='🔍', title='Transparency', description='Clear benefits, exclusions, and pricing.'),
            SimpleNamespace(icon='📊', title='Accuracy', description='Verified data refreshed throughout the day.'),
            SimpleNamespace(icon='🤝', title='Support', description='Live chat, multilingual onboarding, and campus partners.'),
        ]

    return render(request, 'about.html', {'about_content': about_page, 'about_values': values})


def _sanitize_member_choice(choice: str, valid_values: set, default_value: str) -> str:
    if choice in valid_values:
        return choice
    return default_value


def _member_options_with_defaults():
    try:
        segments = list(AudienceSegment.objects.all())
    except (OperationalError, ProgrammingError):
        segments = []
    if segments:
        options = [
            {
                'value': segment.slug,
                'label': segment.label,
                'description': segment.description,
                'icon': segment.icon,
            }
            for segment in segments
        ]
        default_slug = next((segment.slug for segment in segments if segment.is_default), segments[0].slug)
        return options, default_slug
    return MEMBER_OPTIONS, 'adult'


def _parse_age(raw_age: Optional[str]) -> int:
    if not raw_age:
        return DEFAULT_AGE
    try:
        value = int(raw_age)
    except (TypeError, ValueError):
        return DEFAULT_AGE
    return max(0, min(80, value))


def _build_comparison_rows(plans: list, specs: list) -> list:
    rows = []
    for spec in specs:
        values = []
        for plan in plans:
            raw_value = plan.get(spec['key'])
            if spec.get('type') == 'bool':
                value = 'Yes' if raw_value else 'No'
            else:
                value = raw_value or '—'
            values.append(value)
        rows.append({'label': spec['label'], 'values': values})
    return rows


def _percent(part: int, total: int) -> int:
    if not total:
        return 0
    return int(round((part / total) * 100))


def _pipeline_status(percent: int) -> str:
    if percent >= 70:
        return 'healthy'
    if percent >= 45:
        return 'watch'
    return 'risk'


def product(request):
    track_acquisition(request)
    catalog = load_plan_catalog()
    cities = get_unique_cities(catalog) or ['New Haven, CT']
    member_options, default_member = _member_options_with_defaults()
    record_metric_once(request, 'plan_profile_view')

    selected_member = _sanitize_member_choice(
        request.GET.get('member', default_member),
        {option['value'] for option in member_options},
        default_member,
    )
    selected_age = _parse_age(request.GET.get('age'))
    selected_city = request.GET.get('city') or cities[0]
    if selected_city not in cities:
        selected_city = cities[0]

    filtered = filter_plans(catalog, selected_member, selected_age, selected_city)
    fallback_to_all = False
    if not filtered:
        filtered = catalog
        fallback_to_all = True

    featured_plans = filtered[:4]
    record_plan_impressions(featured_plans)
    comparison_plans = filtered[:3]
    field_specs = comparison_fields()
    comparison_rows = _build_comparison_rows(comparison_plans, field_specs)
    summary = summarize_plans(filtered)
    city_label = 'city' if summary['city_count'] == 1 else 'cities'
    plan_summary = (
        f"{summary['plan_count']} plans · {summary['provider_count']} providers · "
        f"{summary['city_count']} {city_label}"
    )
    plan_summary_secondary = (
        f"{summary['child_ready']} cover dependents · {summary['adult_ready']} adult-ready"
    )
    if request.GET:
        record_metric_once(request, 'comparison_engaged')

    try:
        product_content = ProductPageContent.objects.first()
    except (OperationalError, ProgrammingError):
        product_content = None
    if not product_content:
        product_content = SimpleNamespace(
            kicker='Plan builder',
            headline='Design the perfect coverage mix.',
            subheadline='Build profiles, search cities, and review side-by-side comparisons powered entirely by our curated static dataset.',
            summary_line='92+ plans · 18 insurers · 1 city',
            summary_secondary='Child-ready and adult-ready options filtered instantly.',
        )

    context = {
        'member_options': member_options,
        'cities': cities,
        'selected_member': selected_member,
        'selected_age': selected_age,
        'selected_city': selected_city,
        'featured_plans': featured_plans,
        'plan_summary': plan_summary,
        'plan_summary_secondary': plan_summary_secondary,
        'results_count': summary['plan_count'],
        'fallback_to_all': fallback_to_all,
        'comparison_plans': comparison_plans,
        'comparison_rows': comparison_rows,
        'product_content': product_content,
    }
    return render(request, 'product.html', context)


def contact(request):
    track_acquisition(request)
    submitted = request.method == 'POST'
    try:
        contact_content = ContactPageContent.objects.first()
    except (OperationalError, ProgrammingError):
        contact_content = None
    if not contact_content:
        contact_content = SimpleNamespace(
            kicker='We are here to help',
            headline='Let’s talk about coverage, partnerships, or onboarding.',
            intro='Email us or use the form below. We respond within one business day.',
            support_email='support@insurancebuddy.com',
        )
    return render(request, 'contact.html', {'submitted': submitted, 'contact_content': contact_content})


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('packs_list')
    form = SignupForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = User.objects.create_user(
            username=form.cleaned_data['username'],
            email=form.cleaned_data['email'],
            password=form.cleaned_data['password'],
        )
        _get_or_create_profile(user)
        record_metric('user_signup')
        login(request, user)
        return redirect('packs_list')
    return render(request, 'auth/signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('packs_list')
    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect(request.GET.get('next') or 'packs_list')
        error = 'Invalid username or password.'
    return render(request, 'auth/login.html', {'error': error})


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required(login_url='login')
def profile_view(request):
    profile = _get_or_create_profile(request.user)
    form = ProfileForm(request.POST or None, instance=profile)
    saved = False
    if request.method == 'POST' and form.is_valid():
        form.save()
        saved = True
    return render(request, 'account/profile.html', {'form': form, 'saved': saved})


@login_required(login_url='login')
def packs_list(request):
    packs = Pack.objects.filter(user=request.user).order_by('-updated_at')
    return render(request, 'account/deals_list.html', {'packs': packs})


@login_required(login_url='login')
def pack_create(request):
    form = PackForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        pack = form.save(commit=False)
        pack.user = request.user
        pack.save()
        return redirect('pack_detail', pack_id=pack.id)
    return render(request, 'account/deal_form.html', {'form': form, 'mode': 'create'})


@login_required(login_url='login')
def pack_edit(request, pack_id):
    pack = Pack.objects.filter(id=pack_id, user=request.user).first()
    if not pack:
        raise Http404('Pack not found')
    form = PackForm(request.POST or None, instance=pack)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('pack_detail', pack_id=pack.id)
    return render(request, 'account/deal_form.html', {'form': form, 'mode': 'edit', 'pack': pack})


@login_required(login_url='login')
def pack_detail(request, pack_id):
    pack = Pack.objects.filter(id=pack_id, user=request.user).first()
    if not pack:
        raise Http404('Pack not found')
    return render(
        request,
        'account/deal_detail.html',
        {'pack': pack},
    )


@staff_member_required
def dashboard(request):
    catalog = load_plan_catalog()
    summary = summarize_plans(catalog)
    plan_count = summary['plan_count']
    city_count = summary['city_count']
    adult_ready = summary['adult_ready']
    child_ready = summary['child_ready']
    provider_count = summary['provider_count']

    family_ready = sum(1 for plan in catalog if plan.get('supports_family'))
    gov_programs = sum(1 for plan in catalog if plan.get('is_government'))
    referral_free = sum(1 for plan in catalog if not plan.get('referral_required'))
    global_coverage = sum(1 for plan in catalog if 'Global coverage' in plan.get('tags', []))
    preventive_ready = sum(1 for plan in catalog if plan.get('services_before_deductible'))
    average_cities = (
        round(sum(len(plan.get('cities', [])) for plan in catalog) / plan_count, 1)
        if plan_count
        else 0
    )

    flow_cards = [
        {'label': 'Active plans', 'value': f'{plan_count}', 'change': f'{provider_count} providers'},
        {
            'label': 'Cities tracked',
            'value': f'{city_count}',
            'change': f"Avg {average_cities:.1f} cities/plan" if plan_count else 'No cities ingested',
        },
        {
            'label': 'Family-ready coverage',
            'value': f'{family_ready}',
            'change': f"{_percent(family_ready, plan_count)}% of catalog",
        },
        {
            'label': 'Referral-free access',
            'value': f'{referral_free}',
            'change': f"{_percent(referral_free, plan_count)}% allow direct booking",
        },
    ]

    user_segments = [
        {
            'title': 'Adult-ready plans',
            'value': adult_ready,
            'detail': 'Cover undergraduate & graduate students',
            'trend': f"{_percent(adult_ready, plan_count)}%",
        },
        {
            'title': 'Child & dependent coverage',
            'value': child_ready,
            'detail': 'Meets K-12 or dependent visa waivers',
            'trend': f"{_percent(child_ready, plan_count)}%",
        },
        {
            'title': 'Public & gov programs',
            'value': gov_programs,
            'detail': 'Medicaid, CHIP, TRICARE & more',
            'trend': f"{_percent(gov_programs, plan_count)}%",
        },
    ]

    acquisition_total = get_metric_total('acquisition')
    plan_views_total = get_metric_total('plan_profile_view')
    comparison_total = get_metric_total('comparison_engaged')
    checkout_total = get_metric_total('checkout_intent')

    pipeline = []
    pipeline_specs = [
        ('Acquisition', acquisition_total, acquisition_total, 'Unique visitors captured'),
        ('Plan profile views', plan_views_total, acquisition_total, 'Students exploring plan details'),
        ('Comparisons opened', comparison_total, plan_views_total, 'Side-by-side comparisons run'),
        ('Checkout intent', checkout_total, comparison_total, 'Clicks to insurer checkout'),
    ]
    for label, count, baseline, caption in pipeline_specs:
        if label == 'Acquisition':
            percent = 100 if count else 0
        else:
            percent = _percent(count, baseline)
        pipeline.append(
            {
                'stage': label,
                'value': f'{percent}%',
                'detail': f"{count:,} sessions · {caption}",
                'status': _pipeline_status(percent),
            }
        )

    recent_users = [
        {'name': 'Esther Howard', 'email': 'esther@yale.edu', 'region': 'US · CT', 'plan': 'Yale SHP', 'status': 'Verified'},
        {'name': 'Diego Flores', 'email': 'diego@mit.edu', 'region': 'US · MA', 'plan': 'MIT Classic', 'status': 'Pending docs'},
        {'name': 'Jun Park', 'email': 'jun.park@rice.edu', 'region': 'US · TX', 'plan': 'Rice Guardian', 'status': 'Active'},
        {'name': 'Ava Thompson', 'email': 'ava.t@columbia.edu', 'region': 'US · NY', 'plan': 'Columbia Core', 'status': 'Trial'},
    ]

    operations_feed = [
        {'time': '12:40', 'title': 'API import complete', 'meta': '17 new plans synced', 'trend': '+', 'status': 'success'},
        {'time': '11:05', 'title': 'Escalation resolved', 'meta': 'MIT dental waiver approved', 'trend': '→', 'status': 'neutral'},
        {'time': '09:32', 'title': 'Incident #1841', 'meta': 'Delayed webhook from carrier', 'trend': '!', 'status': 'alert'},
        {'time': '07:50', 'title': 'New campus pilot', 'meta': 'Columbia SIPA onboarding', 'trend': '+', 'status': 'success'},
    ]

    product_health = [
        {
            'title': 'Preventive care at $0',
            'value': f"{_percent(preventive_ready, plan_count)}%",
            'detail': f"{preventive_ready} plans cover preventive benefits before the deductible.",
        },
        {
            'title': 'Referral-free specialists',
            'value': f"{_percent(referral_free, plan_count)}%",
            'detail': f"{referral_free} plans allow seeing specialists without referrals.",
        },
        {
            'title': 'Global & nomad coverage',
            'value': f"{_percent(global_coverage, plan_count)}%",
            'detail': f"{global_coverage} plans highlight worldwide reach or nomad benefits.",
        },
    ]

    source_breakdown = summarize_sources(acquisition_total)
    change_ratio = get_metric_change_ratio('acquisition')
    traffic_summary = {
        'period': 'All time',
        'updated': timezone.now().strftime('%Y-%m-%d %H:%M'),
        'total_visitors': f"{acquisition_total:,}",
        'sources': source_breakdown,
        'change_display': f"{change_ratio:+.0%}" if change_ratio is not None else None,
        'change_positive': change_ratio >= 0 if change_ratio is not None else None,
    }

    plan_engagement = []
    impression_totals = get_plan_impression_totals()
    click_totals = get_plan_click_totals()
    for plan in catalog:
        plan_id = plan.get('plan_id')
        if plan_id is None:
            continue
        impressions = impression_totals.get(plan_id, 0)
        clicks = click_totals.get(plan_id, 0)
        if not impressions and not clicks:
            continue
        ctr = round((clicks / impressions) * 100) if impressions else 0
        plan_engagement.append(
            {
                'plan_name': plan.get('plan_name'),
                'cities': plan.get('cities_display') or 'N/A',
                'segment': plan.get('audience_label'),
                'impressions': impressions,
                'clicks': clicks,
                'ctr': ctr,
            }
        )
    plan_engagement.sort(key=lambda entry: (entry['clicks'], entry['impressions']), reverse=True)
    plan_engagement = plan_engagement[:4]

    context = {
        'plan_count': plan_count,
        'city_count': city_count,
        'adult_ready': adult_ready,
        'child_ready': child_ready,
        'flow_cards': flow_cards,
        'user_segments': user_segments,
        'recent_users': recent_users,
        'pipeline': pipeline,
        'operations_feed': operations_feed,
        'product_health': product_health,
        'traffic_summary': traffic_summary,
        'plan_engagement': plan_engagement,
    }
    return render(request, 'dashboard.html', context)


@csrf_exempt
@require_http_methods(['POST'])
def traffic_ingest(request):
    if TRAFFIC_API_KEY:
        provided_key = request.headers.get('X-Api-Key')
        if provided_key != TRAFFIC_API_KEY:
            return JsonResponse({'detail': 'Forbidden'}, status=403)

    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'detail': 'Invalid JSON payload'}, status=400)

    raw_event = payload.get('event')
    event = str(raw_event).strip() if raw_event not in (None, '') else ''
    raw_source = payload.get('source')
    source = str(raw_source).strip() if raw_source not in (None, '') else ''
    count = payload.get('count', 1)
    raw_date = payload.get('date')

    if not event:
        event = 'acquisition'

    try:
        count_value = int(count)
    except (TypeError, ValueError):
        return JsonResponse({'detail': 'count must be an integer'}, status=400)
    if count_value <= 0:
        return JsonResponse({'detail': 'count must be greater than zero'}, status=400)

    if len(event) > 120:
        return JsonResponse({'detail': 'event must be 120 characters or fewer'}, status=400)
    max_source_length = 120 - len(SOURCE_PREFIX)
    if source and len(source) > max_source_length:
        return JsonResponse({'detail': f'source must be {max_source_length} characters or fewer'}, status=400)

    target_date = None
    if raw_date:
        try:
            target_date = date.fromisoformat(raw_date)
        except (TypeError, ValueError):
            return JsonResponse({'detail': 'date must be in YYYY-MM-DD format'}, status=400)

    record_metric(event, amount=count_value, date=target_date)
    if source:
        record_metric(f'{SOURCE_PREFIX}{source}', amount=count_value, date=target_date)

    return JsonResponse(
        {
            'status': 'ok',
            'metric': event,
            'source': source or None,
            'count': count_value,
            'date': target_date.isoformat() if target_date else None,
        },
        status=201,
    )


def abtest_endpoint(request):
    variant = request.session.get('abtest_variant')
    if variant not in ('kudos', 'thanks'):
        variant = random.choice(['kudos', 'thanks'])
        request.session['abtest_variant'] = variant
        request.session.modified = True

    record_metric('abtest_page_view')
    record_metric(f'abtest_variant_{variant}')

    names_list = ''.join(f'<li>{name}</li>' for name in TEAM_NICKNAMES)
    ga_script = ''
    if GA_MEASUREMENT_ID:
        ga_script = f"""
        <script async src="https://www.googletagmanager.com/gtag/js?id={GA_MEASUREMENT_ID}"></script>
        <script>
            window.dataLayer = window.dataLayer || [];
            function gtag(){{dataLayer.push(arguments);}}
            gtag('js', new Date());
            gtag('config', '{GA_MEASUREMENT_ID}');
        </script>
        """

    ym_script = ''
    if YANDEX_METRICA_ID:
        ym_script = f"""
        <script type="text/javascript">
            (function(m,e,t,r,i,k,a){{m[i]=m[i]||function(){{(m[i].a=m[i].a||[]).push(arguments)}};
            m[i].l=1*new Date();k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a);}})
            (window, document, "script", "https://mc.yandex.ru/metrika/tag.js", "ym");
            ym({YANDEX_METRICA_ID}, "init", {{
                clickmap:true,
                trackLinks:true,
                accurateTrackBounce:true
            }});
        </script>
        <noscript><div><img src="https://mc.yandex.ru/watch/{YANDEX_METRICA_ID}" style="position:absolute; left:-9999px;" alt="" /></div></noscript>
        """

    html = f"""
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <title>eastern-bang · A/B test</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 720px; margin: 48px auto; padding: 0 16px; color: #0f172a; }}
            h1 {{ font-size: 28px; margin-bottom: 8px; }}
            p {{ color: #475569; }}
            ul {{ padding-left: 20px; }}
            button {{ background: #0f172a; color: #fff; border: none; padding: 12px 20px; border-radius: 8px; cursor: pointer; font-size: 16px; }}
            button:hover {{ background: #0b1224; }}
            .card {{ background: #f8fafc; border: 1px solid #e2e8f0; padding: 20px; border-radius: 12px; margin-top: 24px; }}
        </style>
        {ga_script}
        {ym_script}
    </head>
    <body>
        <h1>eastern-bang A/B Test Endpoint</h1>
        <p>This page is publicly accessible and used for analytics testing.</p>
        <div class="card">
            <h3>Team member nicknames</h3>
            <ul>{names_list}</ul>
            <button id="abtest">{variant}</button>
        </div>
        <script>
            document.addEventListener('DOMContentLoaded', function() {{
                var btn = document.getElementById('abtest');
                if (!btn) return;
                btn.addEventListener('click', function() {{
                    // Lightweight click tracking for analytics tools already on the page.
                    if (typeof gtag === 'function') {{
                        gtag('event', 'abtest_click', {{ variant: '{variant}' }});
                    }}
                    if (typeof ym === 'function') {{
                        ym({YANDEX_METRICA_ID}, 'reachGoal', 'abtest_click', {{ variant: '{variant}' }});
                    }}
                    btn.innerText = '{variant} ✨';
                }});
            }});
        </script>
    </body>
    </html>
    """
    return HttpResponse(html)


def plan_redirect(request, plan_id: str):
    try:
        plan_index = int(plan_id)
    except (TypeError, ValueError):
        raise Http404('Plan not found')

    plan = get_plan_by_id(plan_index)
    if not plan or not plan.get('plan_url'):
        raise Http404('Plan not available for redirect')

    record_metric_once(request, 'checkout_intent')
    record_metric('checkout_click')
    record_plan_click(plan_index)
    return redirect(plan['plan_url'])
