---
name: deco-island
description: Creates Islands for deco.cx — interactive Preact components that hydrate on the client. Use when adding interactivity (click handlers, state, effects), creating buy buttons, modals, carousels, counters, or any component that needs client-side JavaScript. Covers islands architecture, prop minimization, children pattern, and invoke API.
---

# deco.cx Islands

Guide for creating Islands — interactive client-side components in deco.cx.

## What is an Island

An Island is a **Preact component that hydrates on the client**. In deco.cx (built on Fresh/Deno), all components are server-rendered by default. Only components placed in the `islands/` folder are shipped as JavaScript to the browser.

Sections = server-only (zero JS). Islands = interactive (hydrated JS).

## Project structure

```
islands/
├── AddToCartButton.tsx
├── SearchBar.tsx
├── ImageCarousel.tsx
└── QuantitySelector.tsx
components/
├── ui/
│   ├── Modal.tsx           ← used inside islands
│   └── Spinner.tsx
```

- `islands/` — components that need client-side interactivity
- `components/` — shared UI pieces (used by both sections and islands)

## When to use an Island

**Use an Island when the component needs:**
- Event handlers (`onClick`, `onSubmit`, `onChange`)
- Client-side state (`useState`, `useSignal`)
- Effects (`useEffect`)
- Browser APIs (`localStorage`, `window`, `document`)
- Real-time updates (WebSocket, polling)

**Do NOT use an Island when:**
- The component only displays data (use a Section)
- The component is purely structural/layout (use a Section)
- Interactivity can be achieved with CSS only (`:hover`, `details/summary`)

## Creating an Island

### Basic example

```tsx
// islands/Counter.tsx
import { useSignal } from "@preact/signals";

export default function Counter() {
  const count = useSignal(0);

  return (
    <div class="flex items-center gap-4">
      <button
        class="btn btn-sm btn-outline"
        onClick={() => count.value--}
      >
        -
      </button>
      <span class="text-lg font-bold">{count}</span>
      <button
        class="btn btn-sm btn-outline"
        onClick={() => count.value++}
      >
        +
      </button>
    </div>
  );
}
```

### Buy button example

```tsx
// islands/AddToCartButton.tsx
import { useSignal } from "@preact/signals";
import { invoke } from "../runtime.ts";

interface Props {
  productId: string;
  seller: string;
  label?: string;
}

export default function AddToCartButton({
  productId,
  seller,
  label = "Add to Cart",
}: Props) {
  const loading = useSignal(false);

  const handleClick = async () => {
    loading.value = true;
    try {
      await invoke.vtex.actions.cart.addItems({
        orderItems: [{ id: productId, seller, quantity: 1 }],
      });
    } finally {
      loading.value = false;
    }
  };

  return (
    <button
      class="btn btn-primary w-full"
      onClick={handleClick}
      disabled={loading.value}
    >
      {loading.value ? "Adding..." : label}
    </button>
  );
}
```

## Using Islands inside Sections

Import the Island into a Section and pass only the minimum required props.

```tsx
// sections/ProductCard.tsx
import type { ImageWidget } from "apps/admin/widgets.ts";
import Image from "apps/website/components/Image.tsx";
import AddToCartButton from "../islands/AddToCartButton.tsx";

export interface Props {
  image: ImageWidget;
  title: string;
  price: number;
  productId: string;
  seller: string;
}

export default function ProductCard({
  image, title, price, productId, seller,
}: Props) {
  return (
    <div class="card bg-base-100 shadow-md">
      <Image src={image} alt={title} width={300} height={300} />
      <div class="card-body">
        <h3 class="card-title">{title}</h3>
        <p class="text-xl font-bold">R$ {price.toFixed(2)}</p>
        <AddToCartButton productId={productId} seller={seller} />
      </div>
    </div>
  );
}
```

## Performance: minimizing Island props

Every prop sent to an Island is serialized as JSON and shipped to the browser. Large props = slow hydration.

### BAD — sending entire product object

```tsx
// Section
<AddToCartButton product={product} />

// Island receives the full product JSON (~5kb per product)
```

### GOOD — sending only what the Island needs

```tsx
// Section
<AddToCartButton productId={product.id} seller={product.seller} />

// Island receives ~50 bytes
```

**Rule of thumb:** if the Island's JSON payload exceeds ~500kb, you're sending too much data.

## Performance: children pattern

Use `children` to pass server-rendered content into an Island without hydrating it.

### BAD — Gallery is hydrated unnecessarily

```tsx
// islands/TitleContainer.tsx
import { Gallery } from "../components/Gallery.tsx";

export default function TitleContainer({ galleryProps }: Props) {
  const title = IS_BROWSER ? localStorage.getItem("title") : "Loading...";

  return (
    <div>
      <h1>{title}</h1>
      <Gallery {...galleryProps} />  {/* ← hydrated for no reason */}
    </div>
  );
}
```

### GOOD — Gallery passed as children (not hydrated)

```tsx
// islands/TitleContainer.tsx
import type { ComponentChildren } from "preact";

export default function TitleContainer({ children }: { children: ComponentChildren }) {
  const title = IS_BROWSER ? localStorage.getItem("title") : "Loading...";

  return (
    <div>
      <h1>{title}</h1>
      {children}  {/* ← pre-rendered HTML, no hydration */}
    </div>
  );
}

// Usage in Section:
<TitleContainer>
  <Gallery {...galleryProps} />
</TitleContainer>
```

## Client-side data fetching with invoke

Use `invoke` from `runtime.ts` to call Loaders and Actions from Islands without shipping the function code to the browser.

### Calling a loader

```tsx
import { invoke } from "../runtime.ts";

const data = await invoke["deco-sites/my-store"].loaders.myLoader({
  query: "shoes",
  limit: 10,
});
```

### Calling an action

```tsx
import { invoke } from "../runtime.ts";

await invoke.vtex.actions.cart.addItems({
  orderItems: [{ id: "123", seller: "1", quantity: 1 }],
});
```

### Batching requests

```tsx
import { invoke } from "../runtime.ts";

const { products, categories } = await invoke({
  products: invoke.vtex.loaders.productList({ count: 12 }),
  categories: invoke.vtex.loaders.categoryTree({}),
});
```

## Detecting browser environment

```tsx
import { IS_BROWSER } from "$fresh/runtime.ts";

export default function MyIsland() {
  if (!IS_BROWSER) {
    return <div>Loading...</div>;
  }

  const savedTheme = localStorage.getItem("theme");
  return <div>Theme: {savedTheme}</div>;
}
```

## Signals (preferred over useState)

deco.cx uses Preact Signals for reactive state — more performant than `useState` because they update only the DOM nodes that depend on the signal, not the entire component tree.

```tsx
import { useSignal, useComputed } from "@preact/signals";

export default function PriceCalculator() {
  const quantity = useSignal(1);
  const unitPrice = useSignal(29.90);
  const total = useComputed(() => quantity.value * unitPrice.value);

  return (
    <div>
      <input
        type="number"
        value={quantity}
        onInput={(e) => quantity.value = Number(e.currentTarget.value)}
      />
      <p>Total: R$ {total.value.toFixed(2)}</p>
    </div>
  );
}
```

## Best practices

1. **Minimize Island count** — fewer islands = less JS shipped = better performance
2. **Minimize props** — send only IDs and essential data, never full API objects
3. **Use `children` pattern** — pass server-rendered content as children to avoid unnecessary hydration
4. **Prefer Signals over useState** — `useSignal` for granular DOM updates
5. **Use `invoke`** for data fetching — never import API clients directly into Islands
6. **Use `IS_BROWSER`** guard for browser-only APIs (localStorage, window, document)
7. **Keep Islands small** — extract display logic into `components/` and import into the Island
8. **CSS-only interactivity first** — use `details/summary`, `:hover`, checkbox hacks before reaching for an Island
9. **Lazy load heavy Islands** — use intersection observer or deferred sections for below-fold interactivity
10. **Never put Sections inside Islands** — Sections are server-only; Islands are client-hydrated
