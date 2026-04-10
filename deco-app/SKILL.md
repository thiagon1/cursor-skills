---
name: deco-app
description: Creates custom Apps for deco.cx — modular bundles of sections, loaders, actions, and workflows with shared state. Use when creating a deco app, defining mod.ts, adding actions/workflows, managing app state (API keys, global config), or making an app installable.
---

# deco.cx Apps

Guide for creating custom Apps in deco.cx — modular capability bundles.

## What is an App

An App is a **self-contained module** that bundles sections, loaders, actions, workflows, and shared state. Apps can be installed into any deco.cx site, making them the primary mechanism for code reuse and distribution.

## Project structure

```
my-app/
├── mod.ts                  ← app entry point (required)
├── manifest.gen.ts         ← auto-generated manifest
├── deno.json               ← Deno configuration
├── sections/
│   └── MyWidget.tsx
├── loaders/
│   └── fetchData.ts
├── actions/
│   └── submitForm.ts
├── workflows/
│   └── syncProducts.ts
└── utils/
    └── api.ts
```

## Creating an App

### Step 1: Initialize

```bash
deno run -A -r https://deco.cx/start
```

Choose a name when prompted. Navigate to the directory.

### Step 2: Understand mod.ts

The `mod.ts` file is the app entry point — it defines the manifest, state, and exports.

```ts
// mod.ts
import manifest from "./manifest.gen.ts";
import type { Manifest } from "./manifest.gen.ts";
import type { App, AppContext as AC } from "deco/mod.ts";

export interface State {
  /**
   * @title API Base URL
   * @description Base URL for the external API
   */
  url: string;

  /**
   * @title API Key
   * @description Authentication key for API access
   */
  apiKey: string;
}

export type MyApp = App<Manifest, State>;

export default function App(state: State): MyApp {
  return {
    manifest,
    state,
  };
}

export type AppContext = AC<MyApp>;
```

| Export | Purpose |
|---|---|
| `State` interface | App-level configuration (API keys, URLs, feature flags). Generates an Admin form when the app is installed |
| `App` function | Receives state, returns manifest + state. Entry point for the app |
| `AppContext` type | Type helper to access state and invoke loaders/actions from within the app |

### Step 3: Run the app

```bash
deno task start
```

This auto-generates `manifest.gen.ts` with all discovered sections, loaders, actions, and workflows.

## App components

### Loaders

Server-side data fetching, same as site loaders but scoped to the app.

```ts
// loaders/fetchProducts.ts
import type { AppContext } from "../mod.ts";

export interface Props {
  /** @title Search query */
  query?: string;
  /** @title Limit */
  /** @default 10 */
  limit?: number;
}

export default async function loader(
  props: Props,
  _req: Request,
  ctx: AppContext,
) {
  const { url, apiKey } = ctx.state;

  const response = await fetch(
    `${url}/products?q=${props.query || ""}&limit=${props.limit || 10}`,
    { headers: { Authorization: `Bearer ${apiKey}` } },
  );

  return response.json();
}
```

### Actions

Mutations (write operations) — add to cart, submit forms, update data.

```ts
// actions/submitLead.ts
import type { AppContext } from "../mod.ts";

export interface Props {
  name: string;
  email: string;
  phone?: string;
}

export default async function action(
  props: Props,
  _req: Request,
  ctx: AppContext,
) {
  const { url, apiKey } = ctx.state;

  const response = await fetch(`${url}/leads`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify(props),
  });

  if (!response.ok) {
    throw new Error(`Failed to submit lead: ${response.status}`);
  }

  return response.json();
}
```

### Sections

Preact components bundled with the app.

```tsx
// sections/LeadForm.tsx
import type { SectionProps } from "deco/mod.ts";

export interface Props {
  /** @title Form title */
  title?: string;
  /** @title Submit button label */
  buttonLabel?: string;
}

export default function LeadForm({
  title = "Contact Us",
  buttonLabel = "Submit",
}: Props) {
  return (
    <section class="bg-base-100 py-8">
      <div class="container mx-auto max-w-md">
        <h2 class="text-2xl font-bold mb-4">{title}</h2>
        <form>
          <input type="text" placeholder="Name" class="input input-bordered w-full mb-3" />
          <input type="email" placeholder="Email" class="input input-bordered w-full mb-3" />
          <button type="submit" class="btn btn-primary w-full">{buttonLabel}</button>
        </form>
      </div>
    </section>
  );
}
```

### Workflows

Long-running or scheduled processes.

```ts
// workflows/syncProducts.ts
import type { AppContext } from "../mod.ts";
import type { WorkflowContext } from "deco/mod.ts";

export default async function workflow(
  _props: unknown,
  ctx: WorkflowContext<AppContext>,
) {
  // Scheduled sync logic
  const products = await ctx.invoke.loaders.fetchProducts({ limit: 100 });
  // Process products...
}
```

## Using AppContext

`AppContext` gives loaders and actions access to the app's state and to other loaders/actions in the same app.

```ts
export default async function loader(
  props: Props,
  req: Request,
  ctx: AppContext,
) {
  // Access app state (configured in Admin)
  const { apiKey, url } = ctx.state;

  // Invoke another loader from the same app
  const categories = await ctx.invoke.loaders.fetchCategories({});

  return { ...props, categories };
}
```

## Using Secret for sensitive values

```ts
import { Secret } from "apps/website/loaders/secret.ts";

export interface State {
  /** @title API URL */
  url: string;
  /** @title API Key */
  apiKey: Secret;
}
```

The `Secret` type encrypts the value in the Admin — it is never exposed in the frontend.

## Making an App installable

To make your app installable by other deco sites:

1. Publish the app to a Deno-compatible registry or GitHub
2. The consuming site adds it to `apps/` and imports it in their site configuration
3. The `State` interface generates an Admin form for configuration

## Best practices

1. **Keep `mod.ts` minimal** — only manifest, state, and the App function
2. **Use `State` for global config** — API keys, base URLs, feature flags
3. **Use `Secret` for sensitive values** — never store API keys as plain strings
4. **Add `@title` and `@description`** to State properties for clear Admin setup
5. **Use `AppContext`** to access state in loaders/actions — never hardcode config
6. **Separate concerns** — loaders for reads, actions for writes, workflows for background tasks
7. **Auto-generate manifest** — run `deno task start` to regenerate `manifest.gen.ts` after adding files
8. **Type the return values** of loaders and actions for downstream type safety
9. **Handle errors** in loaders/actions — return meaningful error objects instead of throwing
10. **Keep apps focused** — one app per integration/domain (e.g., one for CRM, one for analytics)
