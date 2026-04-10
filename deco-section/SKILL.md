---
name: deco-section
description: Creates Sections for deco.cx — Preact components with TypeScript Props that auto-generate the Admin editor UI. Use when creating sections, defining props with widgets/annotations, styling with Tailwind/DaisyUI themes, or building configurable UI blocks for the deco.cx CMS.
---

# deco.cx Sections

Guide for creating Sections in deco.cx — the fundamental UI building block.

## What is a Section

A Section is a **Preact component** exported from a `.tsx` file inside the `sections/` folder. Its TypeScript `Props` interface is automatically converted into a visual form in the deco.cx Admin, making sections configurable by business users.

## Project structure

```
sections/
├── Hero.tsx
├── ProductShelf.tsx
├── Header/
│   ├── Header.tsx
│   └── NavItem.tsx
└── Footer.tsx
```

Subdirectories inside `sections/` are supported — the Admin groups them automatically.

## Creating a Section

### Minimal example

```tsx
// sections/Banner.tsx
export interface Props {
  /** @title Banner title */
  title: string;
  /** @title Subtitle */
  subtitle?: string;
}

export default function Banner({ title, subtitle }: Props) {
  return (
    <div class="bg-primary text-primary-content p-8 text-center">
      <h1 class="text-4xl font-bold">{title}</h1>
      {subtitle && <p class="mt-2 text-lg">{subtitle}</p>}
    </div>
  );
}
```

### Rules

1. The file **must** `export default` a Preact component (function returning JSX)
2. The file **must** `export` a `Props` interface (named exactly `Props`)
3. All prop types must be **serializable** (no functions, classes, or DOM refs)

## Props & Widgets

The Admin form is generated from the `Props` type. Use widget types from `apps/admin/widgets.ts` for rich editors.

### Widget types

| Import | Admin widget | Example |
|---|---|---|
| `ImageWidget` | Image uploader | `photo: ImageWidget` |
| `VideoWidget` | Video uploader | `video: VideoWidget` |
| `HTMLWidget` | WYSIWYG editor | `content: HTMLWidget` |
| `RichText` | Rich text editor | `text: RichText` |
| `TextArea` | Multi-line text | `body: TextArea` |
| `Color` | Color picker | `bgColor: Color` |
| `Secret` | Encrypted field | `apiKey: Secret` |
| `CSS` | CSS code editor | `customCSS: CSS` |
| `TypeScript` | TS code editor | `script: TypeScript` |
| `Json` | JSON code editor | `config: Json` |

```tsx
import type { ImageWidget, HTMLWidget, Color } from "apps/admin/widgets.ts";

export interface Props {
  /** @title Hero image */
  image: ImageWidget;
  /** @title Body content */
  body: HTMLWidget;
  /** @title Background color */
  /** @format color */
  bgColor?: Color;
}
```

### Union types → Select dropdown

```tsx
export interface Props {
  /** @title Card layout */
  layout: "Grid" | "Table" | "List";
  /** @title Button size */
  size?: "xs" | "sm" | "md" | "lg";
}
```

### Section as prop (composition)

```tsx
import { Section } from "deco/blocks/section.ts";

export interface Props {
  /** @title Inner content section */
  content: Section;
}
```

### Arrays

```tsx
export interface Card {
  /** @title {{{title}}} */
  title: string;
  description: string;
  image: ImageWidget;
}

export interface Props {
  /** @title Cards */
  /** @maxItems 6 */
  cards: Card[];
}
```

Mustache template `{{{title}}}` in `@title` renders the card's title in the Admin list.

## Annotations (JSDoc tags)

Add annotations above properties to customize the Admin form.

| Annotation | Description | Example |
|---|---|---|
| `@title` | Label in the form | `@title Product count` |
| `@description` | Helper text below input | `@description How many products to show` |
| `@format` | Change widget type | `@format textarea`, `@format color`, `@format datetime`, `@format html`, `@format dynamic-options`, `@format code` |
| `@default` | Default value | `@default 4` |
| `@hide` | Hide from form (value kept) | `@hide true` |
| `@ignore` | Remove property entirely | `@ignore` |
| `@minimum` / `@maximum` | Number range | `@minimum 1` `@maximum 20` |
| `@minLength` / `@maxLength` | String length | `@maxLength 120` |
| `@minItems` / `@maxItems` | Array size | `@maxItems 8` |
| `@uniqueItems` | No duplicates in array | `@uniqueItems true` |
| `@readOnly` | Non-editable in form | `@readOnly` |
| `@deprecated` | Mark as deprecated | `@deprecated Use newProp instead` |
| `@options` | Dynamic options loader | `@options site/loaders/products.ts` |
| `@language` | Code editor language | `@language javascript` |
| `@mode` | Object open/closed in form | `@mode closed` |
| `@aiContext` | AI suggestion hint | `@aiContext Suggest a fashion title` |

### Multi-line annotation

```tsx
export interface Props {
  /**
   * @title Number of products
   * @description Total products to display in the storefront
   * @minimum 1
   * @maximum 50
   * @default 12
   */
  count: number;
}
```

## Styling with Tailwind & DaisyUI themes

deco.cx uses Tailwind CSS with DaisyUI theme tokens. Use theme-aware classes:

| Token class | Description |
|---|---|
| `text-primary` | Primary color text |
| `bg-secondary` | Secondary color background |
| `text-base-content` | Default text on base background |
| `bg-base-100` | Main background |
| `btn btn-primary` | Themed button |

The `Theme.tsx` section defines tokens (colors, fonts, spacing). These are configurable in the Admin under Themes.

```tsx
export default function CTA({ title }: Props) {
  return (
    <section class="bg-base-100 py-12">
      <div class="container mx-auto px-4">
        <h2 class="text-3xl font-bold text-primary">{title}</h2>
        <button class="btn btn-secondary mt-4">Learn more</button>
      </div>
    </section>
  );
}
```

## Image component

Use deco's optimized Image component instead of `<img>`:

```tsx
import Image from "apps/website/components/Image.tsx";

<Image
  src={photo}
  alt="Description"
  width={600}
  height={400}
  class="rounded-lg"
  loading="lazy"
  preload
/>
```

## Complete Section example

```tsx
import type { ImageWidget } from "apps/admin/widgets.ts";
import Image from "apps/website/components/Image.tsx";

/** @title {{{title}}} */
export interface Card {
  image: ImageWidget;
  /** @title Card title */
  title: string;
  /** @title Description */
  /** @format textarea */
  description: string;
  /** @title CTA label */
  ctaText?: string;
  /** @title CTA link */
  ctaHref?: string;
}

export interface Props {
  /** @title Section title */
  title: string;
  /** @title Layout */
  columns?: "2" | "3" | "4";
  /** @title Cards */
  /** @maxItems 8 */
  cards: Card[];
}

export default function CardGrid({
  title,
  columns = "3",
  cards,
}: Props) {
  const colsClass = {
    "2": "grid-cols-1 md:grid-cols-2",
    "3": "grid-cols-1 md:grid-cols-3",
    "4": "grid-cols-1 md:grid-cols-2 lg:grid-cols-4",
  };

  return (
    <section class="bg-base-100 py-12">
      <div class="container mx-auto px-4">
        <h2 class="text-3xl font-bold text-center mb-8">{title}</h2>
        <div class={`grid gap-6 ${colsClass[columns]}`}>
          {cards.map((card) => (
            <div class="card bg-base-200 shadow-md">
              <figure>
                <Image
                  src={card.image}
                  alt={card.title}
                  width={400}
                  height={300}
                  class="w-full object-cover"
                />
              </figure>
              <div class="card-body">
                <h3 class="card-title">{card.title}</h3>
                <p>{card.description}</p>
                {card.ctaText && card.ctaHref && (
                  <a href={card.ctaHref} class="btn btn-primary mt-2">
                    {card.ctaText}
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
```

## Best practices

1. **Name Props `Props`** — the Admin only detects the exported interface named `Props`
2. **Always add `@title`** to every prop — improves Admin UX for business users
3. **Use `@format` annotations** for rich inputs (color, datetime, textarea, html)
4. **Use widget types** (`ImageWidget`, `HTMLWidget`) instead of plain `string`
5. **Use theme tokens** (`text-primary`, `bg-base-100`) instead of hardcoded colors
6. **Use deco's `Image` component** for optimized image loading
7. **Keep sections pure** — no side effects, no `useEffect`, no `useState` (use Islands for interactivity)
8. **Organize by feature** — group related sections in subdirectories
9. **Use Mustache `{{{field}}}`** in `@title` for array items to show meaningful labels in the Admin list
10. **Set `@default` values** for optional props so sections render correctly out of the box
