from typing import Optional
from types import SimpleNamespace

from django.contrib.admin.views.decorators import staff_member_required
from django.db import OperationalError, ProgrammingError
from django.shortcuts import render
from django.templatetags.static import static

from .data_loader import (
    comparison_fields,
    filter_plans,
    get_unique_cities,
    load_plan_catalog,
    summarize_plans,
)
from .models import (
    AboutPageContent,
    AudienceSegment,
    ContactPageContent,
    HomePageContent,
    PartnerOrganization,
    ProductPageContent,
)

MEMBER_OPTIONS = [
    {'value': 'adult', 'label': 'Adult Student', 'description': 'Age 18–64 coverage', 'icon': '👤'},
    {'value': 'child', 'label': 'Child / Dependent', 'description': 'K-12 or dependent visa', 'icon': '🧒'},
    {'value': 'family', 'label': 'Family', 'description': 'Plans that cover both adults & kids', 'icon': '👨‍👩‍👦'},
    {'value': 'government', 'label': 'Gov & Public Programs', 'description': 'Medicaid, CHIP, TRICARE, etc.', 'icon': '🏛️'},
]

DEFAULT_AGE = 24


def _strip_reference(value):
    if isinstance(value, str) and ':contentReference' in value:
        return value.split(':contentReference', 1)[0]
    return value


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


def product(request):
    catalog = load_plan_catalog()
    cities = get_unique_cities(catalog) or ['New Haven, CT']
    member_options, default_member = _member_options_with_defaults()

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


@staff_member_required
def dashboard(request):
    catalog = load_plan_catalog()
    plan_count = len(catalog)
    cities = sorted({city for plan in catalog for city in (plan.get('cities') or [])})
    city_count = len(cities) or 0
    adult_ready = sum(1 for plan in catalog if plan.get('for-adult'))
    child_ready = sum(1 for plan in catalog if plan.get('for-child'))

    top_plans = []
    for plan in catalog[:4]:
        plan_cities = ', '.join(plan.get('cities') or ['N/A'])
        if plan.get('for-adult') and plan.get('for-child'):
            segment = 'Family ready'
        elif plan.get('for-adult'):
            segment = 'Adult only'
        elif plan.get('for-child'):
            segment = 'Child ready'
        else:
            segment = 'Specialty'
        top_plans.append(
            {
                'name': plan.get('plan_name'),
                'cities': plan_cities or 'N/A',
                'segment': segment,
                'deductible': _strip_reference(plan.get('overall-deductible', '—')),
                'oop': _strip_reference(plan.get('out-of-pocket-limit-individual', '—')),
            }
        )

    flow_cards = [
        {'label': 'Active users', 'value': '4.2K', 'change': '+8.1% vs last week'},
        {'label': 'Qualified leads', 'value': '932', 'change': '+12 new schools'},
        {'label': 'Plans live', 'value': f'{plan_count}', 'change': 'Dataset refreshed nightly'},
        {'label': 'Cities tracked', 'value': f'{city_count}', 'change': 'Expansion list ready'},
    ]

    user_segments = [
        {'title': 'New signups', 'value': '312', 'detail': 'Week to date', 'trend': '+3.2%'},
        {'title': 'Activated accounts', 'value': '2,841', 'detail': '92% completion', 'trend': '+1.1%'},
        {'title': 'Campus partners', 'value': '58', 'detail': '9 in onboarding', 'trend': '+14%'},
    ]

    recent_users = [
        {'name': 'Esther Howard', 'email': 'esther@yale.edu', 'region': 'US · CT', 'plan': 'Yale SHP', 'status': 'Verified'},
        {'name': 'Diego Flores', 'email': 'diego@mit.edu', 'region': 'US · MA', 'plan': 'MIT Classic', 'status': 'Pending docs'},
        {'name': 'Jun Park', 'email': 'jun.park@rice.edu', 'region': 'US · TX', 'plan': 'Rice Guardian', 'status': 'Active'},
        {'name': 'Ava Thompson', 'email': 'ava.t@columbia.edu', 'region': 'US · NY', 'plan': 'Columbia Core', 'status': 'Trial'},
    ]

    pipeline = [
        {'stage': 'Acquisition', 'value': '68%', 'status': 'healthy', 'detail': 'Paid + content mix'},
        {'stage': 'Eligibility review', 'value': '54%', 'status': 'watch', 'detail': 'Docs queue up 6 hrs'},
        {'stage': 'Plan comparison', 'value': '82%', 'status': 'healthy', 'detail': 'New filters driving usage'},
        {'stage': 'Checkout', 'value': '34%', 'status': 'risk', 'detail': 'Payment partner SLA investigating'},
    ]

    operations_feed = [
        {'time': '12:40', 'title': 'API import complete', 'meta': '17 new plans synced', 'trend': '+', 'status': 'success'},
        {'time': '11:05', 'title': 'Escalation resolved', 'meta': 'MIT dental waiver approved', 'trend': '→', 'status': 'neutral'},
        {'time': '09:32', 'title': 'Incident #1841', 'meta': 'Delayed webhook from carrier', 'trend': '!', 'status': 'alert'},
        {'time': '07:50', 'title': 'New campus pilot', 'meta': 'Columbia SIPA onboarding', 'trend': '+', 'status': 'success'},
    ]

    product_health = [
        {'title': 'Coverage freshness', 'value': '99.2%', 'detail': 'Last import 35m ago'},
        {'title': 'Eligibility accuracy', 'value': '97%', 'detail': 'Manual QA sample this AM'},
        {'title': 'Support SLA', 'value': '12m', 'detail': 'Median first reply'},
    ]

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
        'top_plans': top_plans,
    }
    return render(request, 'dashboard.html', context)
