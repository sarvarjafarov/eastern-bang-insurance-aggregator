# Sprint 3 Retro

## What went well
- Completed 100 percent of planned work (19/19) with consistent velocity.
- Operationalized the platform by activating plan selection links for end-to-end flow.
- Deployed a Django-powered admin dashboard and integrated Google Analytics and Yandex Metrica for visibility into traffic and behavior.

## What did not go well
- Admin dashboard required extra configuration and template overrides to meet UI expectations.
- Analytics integration slowed down due to fragmented documentation across providers.
- Cross-provider link verification took longer because of inconsistent external URL structures.

## What we learned
- Early analytics integration speeds debugging, conversion tracking, and UX validation.
- Django admin accelerates backend management but needs customization planning for nonstandard workflows.
- Validating external dependencies (provider links) earlier avoids late QA bottlenecks.

## Action items and Sprint 4 preview
- Launch add-ons with badges, expandable details, and interactive selection for personalization.
- Persist selected add-ons through the user flow to keep plans customized.
- Streamline auth by unifying sign-in and sign-up and allow users to view/manage saved plans and preferences.
