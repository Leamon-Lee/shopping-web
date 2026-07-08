# Frontend Style Guide

## Overview

This ecommerce frontend follows the existing Medusa Next.js starter style: restrained, product-focused, mostly white and gray, with thin borders, semantic Medusa UI tokens, generous whitespace, and minimal decoration.

New UI must feel like it belongs to the same storefront. Inspect existing pages and components before adding or changing UI, and reuse existing components wherever possible.

## Layout

Use `content-container` for primary page width. It is defined in `frontend/src/styles/globals.css` as:

```tsx
className="content-container"
```

This gives pages a max width of `1440px`, full width, centered layout, and `px-6` horizontal padding.

Common layout patterns:

```tsx
className="content-container py-16"
className="flex flex-col small:flex-row small:items-start py-6 content-container"
className="grid grid-cols-1 gap-6 small:grid-cols-3"
className="grid grid-cols-2 w-full small:grid-cols-3 medium:grid-cols-4 gap-x-6 gap-y-8"
```

Prefer unframed full-width sections with constrained inner content. Use cards only for product tiles, form/payment options, modals, and repeated items.

## Responsive Behavior

Use the custom breakpoints from `frontend/tailwind.config.js`:

* `2xsmall`: `320px`
* `xsmall`: `512px`
* `small`: `1024px`
* `medium`: `1280px`
* `large`: `1440px`
* `xlarge`: `1680px`
* `2xlarge`: `1920px`

Mobile layouts are usually single-column. Larger layouts switch at `small:` or `medium:`.

Examples:

```tsx
className="flex flex-col small:flex-row"
className="grid grid-cols-1 small:grid-cols-3"
className="hidden small:flex"
className="hidden small:table-cell"
```

## Colors

Prefer Medusa UI semantic tokens over raw colors:

```tsx
text-ui-fg-base
text-ui-fg-subtle
text-ui-fg-muted
bg-ui-bg-base
bg-ui-bg-subtle
bg-ui-bg-field
bg-ui-bg-field-hover
border-ui-border-base
border-ui-border-interactive
```

The project also extends a neutral `grey` scale in `tailwind.config.js`, but new UI should first reach for the existing semantic tokens.

Avoid unrelated brand colors, decorative gradients, colorful backgrounds, or a new palette unless explicitly requested.

## Typography

The project uses Inter through Tailwind config and Medusa UI text utilities. Prefer existing text classes from `globals.css` and Medusa preset utilities.

Common local text utilities:

```tsx
text-xsmall-regular
text-small-regular
text-small-semi
text-base-regular
text-base-semi
text-large-regular
text-large-semi
text-xl-regular
text-xl-semi
text-2xl-regular
text-2xl-semi
text-3xl-regular
text-3xl-semi
```

Common Medusa-style utilities already used in components:

```tsx
txt-xsmall-plus
txt-small-plus
txt-compact-small
txt-compact-medium
txt-compact-medium-plus
txt-compact-xlarge-plus
```

Headings are typically normal or semibold, not highly decorative. Keep letter spacing default and avoid oversized marketing typography outside true hero areas.

## Spacing

Spacing is generous but systematic.

Common section and component spacing:

```tsx
py-6
py-12
py-16
py-40
mb-8
mt-4
gap-2
gap-4
gap-6
gap-8
gap-x-6
gap-y-8
px-4
px-6
p-4
p-5
p-6
```

Use existing density: storefront pages are airy; nav, tables, forms, and checkout panels are compact and functional.

## Cards And Product Components

Product components are image-first with subtle metadata and restrained states.

Use existing product components before creating new ones:

* `ProductPreview`
* `Thumbnail`
* `ProductRail`
* `ProductPrice`
* `ProductTabs`
* skeleton product components

Common product/card patterns:

```tsx
className="group"
className="relative w-full overflow-hidden p-4 bg-ui-bg-subtle shadow-elevation-card-rest rounded-large group-hover:shadow-elevation-card-hover transition-shadow ease-in-out duration-150"
className="flex txt-compact-medium mt-4 justify-between"
className="text-ui-fg-subtle"
```

Image cards use stable aspect ratios:

```tsx
aspect-[11/14]
aspect-[9/16]
aspect-[1/1]
aspect-[4/3]
```

Keep product cards simple: image/placeholder, title, price, subtle category or metadata. Avoid heavy shadows, colored cards, or ornate product frames.

## Buttons And Links

Prefer `Button` from `@medusajs/ui` where available.

Common patterns:

```tsx
<Button variant="secondary">...</Button>
<Button className="w-full h-10">...</Button>
className="hover:text-ui-fg-base"
className="text-ui-fg-subtle hover:text-ui-fg-base"
```

Use existing link components:

* `LocalizedClientLink`
* `InteractiveLink` / underline link component

Buttons should be compact, rectangular or softly rounded according to the existing component. Avoid new pill-heavy, gradient, or oversized button systems.

## Forms

Reuse the existing form components before making new controls:

* `Input`
* `NativeSelect`
* `Checkbox`
* `Radio`
* checkout address and payment controls

Input pattern:

```tsx
className="pt-4 pb-1 block w-full h-11 px-4 mt-0 bg-ui-bg-field border rounded-md appearance-none focus:outline-none focus:ring-0 focus:shadow-borders-interactive-with-active border-ui-border-base hover:bg-ui-bg-field-hover"
```

Labels often use compact text and floating-label behavior. Required markers use a restrained rose color only for the asterisk.

Payment and selectable panels use:

```tsx
className="flex flex-col gap-y-2 text-small-regular cursor-pointer py-4 border rounded-rounded px-8 mb-2 hover:shadow-borders-interactive-with-active"
```

## Tables

Use `Table` from `@medusajs/ui`.

Cart table pattern:

```tsx
<Table>
  <Table.Header className="border-t-0">
    <Table.Row className="text-ui-fg-subtle txt-medium-plus">
```

Hide lower-priority columns on smaller screens:

```tsx
className="hidden small:table-cell"
```

Keep table styling quiet: semantic text colors, thin separators, no dense zebra striping unless an existing table uses it.

## Navbar

The navbar is sticky, 64px high, white, and separated by a thin bottom border.

Pattern:

```tsx
className="sticky top-0 inset-x-0 z-50 group"
className="relative h-16 mx-auto border-b duration-200 bg-white border-ui-border-base"
className="content-container txt-xsmall-plus text-ui-fg-subtle flex items-center justify-between w-full h-full text-small-regular"
```

Nav links are subtle by default and darken on hover:

```tsx
className="hover:text-ui-fg-base"
```

The center brand link is uppercase and compact. Avoid adding large logos or decorative navigation treatments unless explicitly requested.

## Footer

The footer uses a top border, large vertical padding, simple columns, and muted text.

Pattern:

```tsx
className="border-t border-ui-border-base w-full"
className="content-container flex flex-col w-full"
className="flex flex-col gap-y-6 xsmall:flex-row items-start justify-between py-40"
className="text-small-regular gap-10 md:gap-x-16 grid grid-cols-2 sm:grid-cols-3"
```

Footer links should remain quiet and text-based:

```tsx
className="text-ui-fg-subtle hover:text-ui-fg-base"
```

## Modals And Overlays

Reuse `Modal` from `frontend/src/modules/common/components/modal`.

Existing modal panels use:

```tsx
className="bg-white shadow-xl border rounded-rounded"
className="max-w-md"
className="max-w-xl"
className="max-w-3xl"
```

Animations are subtle scale/opacity transitions. Avoid dramatic overlay effects or new animation language.

## Shadows And Border Radius

Use existing Tailwind radius tokens:

* `rounded-md`
* `rounded-rounded`
* `rounded-large`

Use Medusa shadows where existing components do:

```tsx
shadow-elevation-card-rest
group-hover:shadow-elevation-card-hover
hover:shadow-borders-interactive-with-active
focus:shadow-borders-interactive-with-active
```

Most layout surfaces use borders instead of heavy shadows:

```tsx
border
border-b
border-t
border-ui-border-base
```

## Empty And Loading States

Reuse existing skeleton components where possible:

* `SkeletonProductGrid`
* `SkeletonProductPreview`
* `SkeletonCartPage`
* `SkeletonLineItem`
* `SkeletonButton`
* `SkeletonOrderSummary`

Empty states should use simple copy, muted foreground colors, and existing buttons/links. Avoid illustration-heavy or marketing-style empty states unless the surrounding page already does that.

## Implementation Checklist

Before creating frontend UI:

1. Read `docs/AGENTS.md`.
2. Read this style guide.
3. Inspect nearby pages and components.
4. Reuse existing components whenever possible.
5. Match existing Tailwind CSS spacing, colors, typography, borders, shadows, radius, and responsive behavior.
6. Keep new pages visually consistent with the storefront.
7. Do not introduce a new design language unless explicitly requested.
