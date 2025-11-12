from typing import Optional
from types import SimpleNamespace

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
    home_page = HomePageContent.objects.prefetch_related('features', 'stats').first()
    partners_qs = PartnerOrganization.objects.all()

    if home_page:
        features = list(home_page.features.values('icon', 'title', 'description'))
        stats = list(home_page.stats.values('value', 'label', 'description'))
        home_data = home_page
    else:
        features = _default_features()
        stats = _default_home_stats()
        home_data = SimpleNamespace(**_default_home_content())

    partners = list(partners_qs.values('name', 'campus', 'website', 'logo_url')) or _default_partners()
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
    about_page = AboutPageContent.objects.prefetch_related('values').first()
    if about_page:
        values = about_page.values.all()
    else:
        about_page = SimpleNamespace(
            kicker='Our mission',
            headline='We make insurance simple for international students.',
            intro=(
                'Insurance Buddy blends human support with automation so that every student '
                'can secure the right coverage for study, travel, and everyday campus life.'
            ),
        )
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
    segments = list(AudienceSegment.objects.all())
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

    product_content = ProductPageContent.objects.first()
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
    contact_content = ContactPageContent.objects.first()
    if not contact_content:
        contact_content = SimpleNamespace(
            kicker='We are here to help',
            headline='Let’s talk about coverage, partnerships, or onboarding.',
            intro='Email us or use the form below. We respond within one business day.',
            support_email='support@insurancebuddy.com',
        )
    return render(request, 'contact.html', {'submitted': submitted, 'contact_content': contact_content})
