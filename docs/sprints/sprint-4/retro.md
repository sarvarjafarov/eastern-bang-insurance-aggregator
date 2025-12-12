# Sprint 4 Retrospective

## What went well
- Completed all planned stories with no rollover.
- Authentication flow is significantly more stable, improving the foundation for personalization.
- Add-ons, reviews, and notifications received cleanup that reduced friction across the platform.
- Database corrections improved reliability across all modules.
- UI refinements enhanced clarity and reduced user confusion during onboarding and selection.

## What did not go well
- Module interdependencies created testing friction; updates in auth/DB affected reviews and notifications.
- Some flows took longer to stabilize due to hidden assumptions in existing logic.
- Several enhancements required rework because of outdated UI elements or mismatched schema.

## What we learned
- Shared modules (add-ons, reviews, notifications) must be tested together during flow changes to avoid regressions.
- Backend validation must align early with UI expectations to prevent mismatched states.
- Incremental UI improvements can yield large UX gains when applied consistently across modules.
