# Project Instructions for Codex

## Goal

This is an ecommerce frontend project with an existing frontend design style.
Codex must preserve and extend the existing style instead of creating a new visual design.

When implementing new pages, components, or frontend features, Codex must make the new UI look like it belongs to the same website.

Codex must never introduce a new design language unless the user explicitly requests it.

## Frontend Style Learning Rule

Before making frontend changes, Codex must inspect the existing frontend codebase.

Codex must review relevant existing pages and components before creating any new UI.

Codex should inspect:

* existing pages
* layout components
* shared UI components
* Tailwind CSS class patterns
* global CSS files
* theme configuration
* navigation
* cards
* buttons
* forms
* tables
* badges
* product components
* empty states
* modal/dialog components
* responsive layout patterns

Codex must infer the project's design system from the current code before creating new UI.

## Design Consistency Rules

When creating new UI, Codex must follow the existing style for:

1. Layout width
2. Page spacing
3. Section spacing
4. Grid system
5. Typography
6. Colors
7. Border radius
8. Shadows
9. Button style
10. Card style
11. Form input style
12. Table style
13. Navigation style
14. Responsive behavior
15. Icon usage
16. Image style
17. Hover and focus states

Every new page must look like it belongs to the same ecommerce website.

## Component Reuse Rules

Codex must reuse existing components whenever possible.

Before creating a new component, Codex must check whether a similar component already exists.

If an existing component can be reused or lightly extended without breaking its current behavior, Codex must prefer that over creating a new component.

Preferred reusable components include:

* PageLayout
* Navbar
* Footer
* PageHeader
* SectionTitle
* ProductCard
* CategoryCard
* PrimaryButton
* SecondaryButton
* FormInput
* SearchInput
* StatusBadge
* EmptyState
* LoadingState
* ErrorState
* Pagination
* DataTable
* Modal

If a new component is required, it must follow the same style as the existing components.

## Tailwind CSS Rules

Codex must follow the existing Tailwind CSS patterns in the project.

Codex must match the existing Tailwind CSS style, including:

* spacing
* colors
* typography
* border radius
* shadows
* layout density
* hover states
* focus states
* responsive behavior

Codex must avoid:

* random colors
* unrelated gradients
* inconsistent shadows
* inconsistent border radius
* inconsistent spacing
* duplicated one-off styles
* unnecessary inline styles
* introducing another UI framework unless explicitly requested

Codex should prefer reusable class patterns that already appear in the project.

## Style Guide Rule

If `docs/frontend-style-guide.md` exists, Codex must read it before making frontend changes.

If `docs/frontend-style-guide.md` does not exist, Codex must create it before making frontend UI changes.

The style guide should document:

* layout rules
* spacing rules
* color palette
* typography
* buttons
* cards
* forms
* tables
* navigation
* reusable components
* responsive behavior
* Tailwind CSS examples

## New Page Implementation Rule

When implementing a new page, Codex must:

1. Read existing frontend files.
2. Read `docs/frontend-style-guide.md` if it exists.
3. Create `docs/frontend-style-guide.md` first if it does not exist.
4. Inspect existing pages and components before creating UI.
5. Identify reusable components.
6. Reuse existing components whenever possible.
7. Implement the page using existing style patterns.
8. Match existing Tailwind CSS spacing, colors, typography, border radius, shadows, and responsive behavior.
9. Avoid redesigning unrelated pages.
10. Keep the code modular.
11. Keep the project structure clean.
12. Ensure the page is responsive.
13. Ensure the page visually matches the existing website.
14. Avoid introducing a new design language unless explicitly requested by the user.

## Reporting Rule

After finishing frontend work, Codex should briefly report:

1. Existing components reused
2. New components created
3. Style patterns followed
4. Files modified
5. Any assumptions made
