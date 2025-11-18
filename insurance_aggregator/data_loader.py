import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Optional

from django.conf import settings

DATA_PATH = Path(settings.BASE_DIR) / 'insurance_aggregator' / 'static' / 'data' / 'plans.json'

CONTENT_REF_PATTERN = re.compile(r':contentReference\[[^\]]+\]\{[^}]+\}')

FIELD_MAP = {
    'plan_name': 'plan_name',
    'overall-deductible': 'overall_deductible',
    'services-covered-before-deductible': 'services_before_deductible',
    'specific-service-deductible': 'specific_service_deductible',
    'out-of-pocket-limit-individual': 'oop_individual',
    'out-of-pocket-limit-family': 'oop_family',
    'out-of-pocket-limit-hospital-surgery-combined': 'oop_hospital',
    'excluded-from-out-of-pocket-limit': 'excluded_from_oop',
    'network-provider-lower-cost': 'network_lower_cost',
    'referral-required-for-specialist': 'referral_required',
    'cities': 'cities',
    'age_min': 'age_min',
    'age_max': 'age_max',
    'for-child': 'for_child',
    'for-adult': 'for_adult',
}

GOVERNMENT_KEYWORDS = (
    'medicaid',
    'chip',
    'medicare',
    'tricare',
    'husky',
)

PLAN_URLS = {
    "Yale University Student Health Plan": "https://yalehealth.yale.edu/patient-care/student-coverage",
    "Student Medicover Supreme (UHCSR Top Tier)": "https://www.studentmedicover.com/",
    "Student Medicover Elite (UHCSR)": "https://www.studentmedicover.com/",
    "Student Medicover Prime 100 (UHCSR)": "https://www.studentmedicover.com/",
    "Student Medicover Prime 500 (UHCSR)": "https://www.studentmedicover.com/",
    "WorldTrips Student Secure Smart": "https://www.worldtrips.com/studentsecure",
    "WorldTrips Student Secure Budget": "https://www.worldtrips.com/studentsecure",
    "WorldTrips Student Secure Select": "https://www.worldtrips.com/studentsecure",
    "WorldTrips Student Secure Elite": "https://www.worldtrips.com/studentsecure",
    "ISO Platinum": "https://www.isoa.org/",
    "ISO Gold": "https://www.isoa.org/",
    "ISO Silver (Basic)": "https://www.isoa.org/",
    "ISO Compass PPO": "https://www.isoa.org/",
    "ISO Secure": "https://www.isoa.org/",
    "ISO J1 Exchange Plan": "https://www.isoa.org/",
    "ISO OPTima Plan": "https://www.isoa.org/",
    "ISO Share (ACA comparable)": "https://www.isoa.org/",
    "ISO Care (ACA comparable)": "https://www.isoa.org/",
    "IMG Student Health Advantage Standard": "https://www.imglobal.com/img-insurance/student-health-advantage",
    "IMG Student Health Advantage Platinum": "https://www.imglobal.com/img-insurance/student-health-advantage",
    "IMG Patriot Exchange Program": "https://www.imglobal.com/travel-medical-insurance/patriot-exchange-program",
    "GeoBlue Navigator Student": "https://www.geobluestudents.com/",
    "ACA Catastrophic Plan": "https://www.healthcare.gov/choose-a-plan/catastrophic-plans/",
    "Medicaid (HUSKY Health)": "https://portal.ct.gov/dss/healthcare/medicaid-and-medical-assistance/husky-health-program",
    "CHIP (Children's Health Insurance Program)": "https://www.medicaid.gov/chip/index.html",
    "Short-term Health Insurance Plan (temporary)": "https://www.healthcare.gov/coverage-options/short-term-limited-duration-insurance/",
    "Seven Corners Liaison Student": "https://www.sevencorners.com/travel-medical-insurance/international-student/liaison-student",
    "PSI Bronze Plan": "https://www.psiservice.com/international-student-health-insurance",
    "PSI Silver Plan": "https://www.psiservice.com/international-student-health-insurance",
    "PSI Gold Plan (High School)": "https://www.psiservice.com/international-student-health-insurance",
    "ACA Marketplace Bronze Plan": "https://www.healthcare.gov/choose-a-plan/plan-categories/",
    "ACA Marketplace Silver Plan": "https://www.healthcare.gov/choose-a-plan/plan-categories/",
    "ACA Marketplace Gold Plan": "https://www.healthcare.gov/choose-a-plan/plan-categories/",
    "ACA Marketplace Platinum Plan": "https://www.healthcare.gov/choose-a-plan/plan-categories/",
    "Parent's Employer Plan (Dependent Coverage)": "https://www.healthcare.gov/young-adults/children-under-26/",
    "TRICARE Young Adult Prime": "https://tricare.mil/Plans/HealthPlans/TYA",
    "TRICARE Young Adult Select": "https://tricare.mil/Plans/HealthPlans/TYA",
    "Cigna Global Student Plan": "https://www.cignaglobal.com/plans/international-student-insurance",
    "SafetyWing Nomad Insurance": "https://www.safetywing.com/nomad-insurance",
    "Wellfleet Student Plan (College)": "https://www.wellfleetstudent.com/",
    "Anthem Student Advantage Plan": "https://studentadvantage.anthem.com/",
    "UnitedHealthcare Student Resources Plan": "https://www.uhcsr.com/",
    "Aetna Student Health Plan": "https://www.aetnastudenthealth.com/",
    "Compass Savings Plan (Economical)": "https://www.compassstudenthealthinsurance.com/",
    "Compass Sports Plan (with Sports Coverage)": "https://www.compassstudenthealthinsurance.com/",
    "Gallagher Student Health Plan": "https://www.gallagherstudent.com/",
    "Florida Blue Student Health Plan": "https://www.floridabluestudentinsurance.com/",
    "ConnectiCare Health Plan (Connecticut)": "https://www.connecticare.com/",
    "Spouse/Partner's Employer Health Plan": "https://www.healthcare.gov/married-couples/coverage-through-spouse/",
    "Medicare (Eligible Student)": "https://www.medicare.gov/",
}


def _clean_value(value):
    if isinstance(value, str):
        cleaned = CONTENT_REF_PATTERN.sub('', value)
        return cleaned.strip()
    return value


def _derive_provider(plan_name: str) -> str:
    if not plan_name:
        return ''
    provider = plan_name.split('(')[0].strip()
    if 'Student Medicover' in provider:
        return 'Student Medicover'
    if 'WorldTrips' in provider:
        return 'WorldTrips'
    if 'ISO ' in provider:
        return 'ISO International'
    if 'IMG ' in provider:
        return 'IMG Global'
    if 'ACA Marketplace' in provider:
        return 'ACA Marketplace'
    if "Parent's Employer" in provider:
        return "Parent Employer Plan"
    if 'Compass' in provider:
        return 'Compass Student'
    if 'PSI ' in provider:
        return 'PSI'
    if 'TRICARE' in provider:
        return 'TRICARE'
    if 'Cigna' in provider:
        return 'Cigna Global'
    if 'SafetyWing' in provider:
        return 'SafetyWing'
    if 'Wellfleet' in provider:
        return 'Wellfleet'
    if 'Anthem' in provider:
        return 'Anthem'
    if 'UnitedHealthcare' in provider:
        return 'UnitedHealthcare'
    if 'Aetna' in provider:
        return 'Aetna'
    if 'Florida Blue' in provider:
        return 'Florida Blue'
    if 'ConnectiCare' in provider:
        return 'ConnectiCare'
    if "Spouse/Partner" in provider:
        return 'Employer Plan'
    if 'GeoBlue' in provider:
        return 'GeoBlue'
    return provider


def _derive_tags(plan: dict) -> list:
    tags = []
    if plan.get('for_child') and plan.get('for_adult'):
        tags.append('Family-ready')
    elif plan.get('for_child'):
        tags.append('Child coverage')
    elif plan.get('for_adult'):
        tags.append('Adult student')

    if plan.get('referral_required'):
        tags.append('Referral needed')
    else:
        tags.append('No referral')

    if plan.get('network_lower_cost'):
        tags.append('Best in-network pricing')

    provider = plan.get('provider', '').lower()
    name = plan.get('plan_name', '').lower()
    if any(keyword in name for keyword in GOVERNMENT_KEYWORDS):
        tags.append('Government program')
    elif 'aca' in name:
        tags.append('ACA compliant')
    elif 'exchange' in name or 'marketplace' in name:
        tags.append('Marketplace ready')
    elif 'nomad' in name or 'global' in name:
        tags.append('Global coverage')

    return tags


def _compute_rating(plan_name: str) -> float:
    if not plan_name:
        return 4.2
    seed = sum(ord(char) for char in plan_name)
    rating = 4.2 + (seed % 8) * 0.1
    return round(min(rating, 4.9), 1)


@lru_cache(maxsize=1)
def load_plan_catalog() -> list:
    with DATA_PATH.open() as source:
        raw = json.load(source)

    catalog = []
    for entry in raw:
        normalized = {}
        for raw_key, field_key in FIELD_MAP.items():
            if raw_key in entry:
                normalized[field_key] = _clean_value(entry[raw_key])
        normalized['plan_name'] = _clean_value(entry.get('plan_name')) or 'Unnamed Plan'
        normalized['plan_url'] = PLAN_URLS.get(normalized['plan_name'], '')
        normalized['provider'] = _derive_provider(normalized['plan_name'])
        normalized['cities'] = normalized.get('cities', []) or []
        normalized['for_child'] = bool(normalized.get('for_child'))
        normalized['for_adult'] = bool(normalized.get('for_adult'))
        normalized['supports_family'] = normalized['for_child'] and normalized['for_adult']
        normalized['is_government'] = any(
            keyword in normalized['plan_name'].lower()
            for keyword in GOVERNMENT_KEYWORDS
        )
        normalized['audience_label'] = _build_audience_label(normalized)
        normalized['tags'] = _derive_tags(normalized)
        normalized['cities_display'] = ', '.join(normalized['cities'])
        normalized['rating'] = _compute_rating(normalized['plan_name'])
        catalog.append(normalized)

    return catalog


def _build_audience_label(plan: dict) -> str:
    if plan['for_child'] and plan['for_adult']:
        return 'All ages'
    if plan['for_child']:
        return 'Child / dependent'
    if plan['for_adult']:
        return 'Adult student'
    return 'Special eligibility'


def get_unique_cities(plans: list) -> list:
    cities = {city for plan in plans for city in plan.get('cities', [])}
    return sorted(cities)


def filter_plans(plans: list, member: str, age: Optional[int], city: Optional[str]) -> list:
    def supports_member(plan: dict) -> bool:
        if member == 'adult':
            return plan['for_adult']
        if member == 'child':
            return plan['for_child']
        if member == 'family':
            return plan['supports_family']
        if member == 'government':
            return plan['is_government']
        return True

    filtered = []
    for plan in plans:
        if city and city not in plan.get('cities', []):
            continue
        if not supports_member(plan):
            continue
        if age is not None:
            min_age = plan.get('age_min') if isinstance(plan.get('age_min'), int) else 0
            max_age = plan.get('age_max') if isinstance(plan.get('age_max'), int) else 120
            if not (min_age <= age <= max_age):
                continue
        filtered.append(plan)
    return filtered


def summarize_plans(plans: list) -> dict:
    if not plans:
        return {'plan_count': 0, 'provider_count': 0, 'city_count': 0, 'child_ready': 0, 'adult_ready': 0}
    providers = {plan['provider'] for plan in plans if plan.get('provider')}
    cities = {city for plan in plans for city in plan.get('cities', [])}
    child_ready = sum(1 for plan in plans if plan.get('for_child'))
    adult_ready = sum(1 for plan in plans if plan.get('for_adult'))
    return {
        'plan_count': len(plans),
        'provider_count': len(providers),
        'city_count': len(cities) or 1,
        'child_ready': child_ready,
        'adult_ready': adult_ready,
    }


def comparison_fields():
    return [
        {'key': 'overall_deductible', 'label': 'Overall Deductible'},
        {'key': 'services_before_deductible', 'label': 'Preventive Before Deductible'},
        {'key': 'specific_service_deductible', 'label': 'Specific Service Deductible'},
        {'key': 'oop_individual', 'label': 'OOP Max (Individual)'},
        {'key': 'oop_family', 'label': 'OOP Max (Family)'},
        {'key': 'oop_hospital', 'label': 'Hospital/Surgery Limit'},
        {'key': 'excluded_from_oop', 'label': 'Excluded From OOP'},
        {'key': 'network_lower_cost', 'label': 'Prefers Network', 'type': 'bool'},
        {'key': 'referral_required', 'label': 'Referral Needed', 'type': 'bool'},
    ]
