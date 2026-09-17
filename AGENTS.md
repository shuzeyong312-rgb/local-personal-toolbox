# Personal Toolbox

## Project goals

This is a local desktop personal toolbox.

The application contains image tools, file tools and e-commerce utilities.

The UI should follow a clean, minimal personal-workspace design rather than a traditional enterprise admin dashboard.

Design reference:

docs/design/target-toolbox.png

## Important rules

- Preserve existing business logic whenever possible.
- Do not rewrite working image-processing code just for UI changes.
- Do not remove existing tools.
- Prefer refactoring UI components over rewriting features.
- Keep the application local-first.
- User files must not be uploaded unless a feature explicitly requires it.
- Avoid unnecessary dependencies.
- Keep desktop packaging working.

## UI principles

- Light theme by default.
- Primary color: blue.
- Large rounded cards.
- Subtle borders.
- Very subtle shadows.
- Generous spacing.
- Bento-style dashboard.
- Minimal sidebar.
- Global command search.
- Floating dock for frequently used tools.
- Avoid large dark navigation areas.
- Avoid excessive gradients and glassmorphism.

## Architecture

Prefer a centralized tool registry.

Sidebar, dashboard, command search and dock should derive their tool metadata from the same source.

Complex tools should have dedicated pages.

Dashboard cards may contain lightweight previews, but should not contain the entire complex tool UI.

## Verification

After modifying code:

- run lint if available
- run typecheck if available
- run tests if available
- run production build
- fix regressions caused by the changes