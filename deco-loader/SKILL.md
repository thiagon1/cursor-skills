---
name: deco-loader
description: Creates Loaders for deco.cx — server-side data fetching functions with configurable Props for the Admin. Use when fetching data from external APIs, creating inline loaders in sections, building reusable loader blocks, optimizing data payloads, or connecting sections to data sources.
---

# deco.cx Loaders

Guide for creating Loaders — server-side data fetching in deco.cx.

## What is a Loader

A Loader is an **async TypeScript function** that fetches and transforms data on the server before passing it to a Section. Loaders can be:

1. **Inline** — exported as `loader` in the same file as a Section
2. **Standalone** — defined in the `loaders/` folder for reuse across sections

Like Sections, Loader `Props` generate an Admin form for business users to configure.

## Project structure

```
loaders/
├── products.ts
├── blogPosts.ts
└── utils/
    └── fetchWithCache.ts
sections/
├── ProductShelf.tsx     ← can have inline loader
└── DogFacts.tsx         ← can have inline loader
```

## Inline Loader (same file as Section)

The simplest pattern — export a `loader` function alongside the Section component.

```tsx
// sections/DogFacts.tsx
import type { SectionProps } from "deco/mod.ts";

export interface Props {
  /** @title Section title */
  title: string;
  /** @title Number of facts */
  /** @minimum 1 */
  /** @maximum 10 */
  /** @default 3 */
  numberOfFacts?: number;
}

export async function loader({ numberOfFacts = 3, title }: Props, _req: Request) {
  const { facts: dogFacts } = await fetch(
    `https://dogapi.dog/api/facts?number=${numberOfFacts}`,
  ).then((r) => r.json()) as { facts: string[] };

  return { dogFacts, title };
}

export default function DogFacts({ title, dogFacts }: SectionProps<typeof loader>) {
  return (
    <div class="p-4">
      <h1 class="font-bold text-2xl">{title}</h1>
      <ul class="list-disc pl-6 mt-4">
        {dogFacts.map((fact) => <li>{fact}</li>)}
      </ul>
    </div>
  );
}
```

### Key points

- `Props` = what the **Admin user** configures (input)
- `SectionProps<typeof loader>` = what the **component** receives (output)
- The loader transforms Admin props into component props
- The `_req: Request` parameter gives access to the HTTP request (URL, headers, cookies)

## Standalone Loader (reusable)

For data shared across multiple sections, create a loader in the `loaders/` folder.

```ts
// loaders/productList.ts
import type { AppContext } from "../apps/site.ts";

export interface Props {
  /** @title Search query */
  query?: string;
  /** @title Max results */
  /** @default 12 */
  count?: number;
}

export default async function loader(
  props: Props,
  _req: Request,
  ctx: AppContext,
): Promise<Product[]> {
  const { query = "", count = 12 } = props;

  const response = await fetch(
    `https://api.example.com/products?q=${query}&limit=${count}`,
  );
  const data = await response.json();

  return data.products;
}
```

Standalone loaders are available in the Admin as data sources that can be "plugged" into any Section prop whose type matches the loader's return type.

## Loader function signature

```ts
export default async function loader(
  props: Props,       // configured by business user in Admin
  req: Request,       // incoming HTTP request
  ctx: AppContext,     // app context (state, invoke other loaders/actions)
): Promise<ReturnType> {
  // fetch, transform, return
}
```

| Parameter | Description |
|---|---|
| `props` | Values configured in the Admin form |
| `req` | HTTP Request object (URL, headers, cookies) |
| `ctx` | App context — access app state, invoke other loaders/actions |

## Loader with request context

Use the `req` parameter to adapt data based on URL, query params, or headers.

```ts
export async function loader(props: Props, req: Request) {
  const url = new URL(req.url);
  const page = Number(url.searchParams.get("page")) || 1;
  const searchTerm = url.searchParams.get("q") || props.defaultQuery;

  const data = await fetch(
    `https://api.example.com/search?q=${searchTerm}&page=${page}`,
  ).then((r) => r.json());

  return { ...props, results: data.results, currentPage: page };
}
```

## Dynamic options loader

Create a loader that powers a `@format dynamic-options` select in the Admin.

```ts
// loaders/availableCategories.ts
import { allowCorsFor, type FnContext } from "deco/mod.ts";

export default function loader(
  _props: unknown,
  req: Request,
  ctx: FnContext,
) {
  Object.entries(allowCorsFor(req)).map(([name, value]) => {
    ctx.response.headers.set(name, value);
  });

  return ["Electronics", "Clothing", "Home & Garden", "Sports"];
}
```

Usage in a section:

```tsx
export interface Props {
  /**
   * @title Category
   * @format dynamic-options
   * @options site/loaders/availableCategories.ts
   */
  category: string;
}
```

## Performance optimization

### Filter data in loaders, not in sections

Send only what the UI needs — especially important when data reaches Islands.

```ts
// BAD: returns entire product object
return { products: rawProducts };

// GOOD: returns only fields the UI uses
return {
  products: rawProducts.map((p) => ({
    id: p.id,
    name: p.name,
    price: p.offers?.lowPrice,
    image: p.image?.[0]?.url,
    url: p.url,
  })),
};
```

### Reuse loader blocks

When the same loader is used on multiple sections of a page, save it as a **loader block** in the Admin. Deco optimizes execution so the same loader runs only once per page render.

### Deferred sections

Sections below the fold can be deferred — they load data lazily, improving initial page load. Configure this in the Admin page editor.

## Error handling

```ts
export async function loader(props: Props, _req: Request) {
  try {
    const response = await fetch(`https://api.example.com/data`);
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    const data = await response.json();
    return { ...props, data, error: null };
  } catch (err) {
    console.error("Loader error:", err);
    return { ...props, data: null, error: "Failed to load data" };
  }
}
```

## Best practices

1. **Use `SectionProps<typeof loader>`** for inline loaders to get type-safe return types
2. **Filter data in the loader** — never send full API responses to sections/islands
3. **Add `@title` and `@description`** to loader Props for clear Admin UX
4. **Set `@default` values** so sections work without manual configuration
5. **Use `req.url`** to read URL search params for pagination, search, filters
6. **Handle errors gracefully** — return fallback data instead of throwing
7. **Reuse loaders as blocks** when the same data is needed across multiple sections
8. **Keep loaders fast** — avoid unnecessary API calls, use caching when possible
9. **Use `ctx`** to invoke other loaders or access app state when composing data
10. **JSON payload under 500kb** — if larger, you're likely sending unnecessary data
