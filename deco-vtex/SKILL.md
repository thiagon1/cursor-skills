---
name: deco-vtex
description: Integrates deco.cx with VTEX e-commerce — product listing pages (PLP), product detail pages (PDP), cart operations, search, and checkout via the VTEX app and invoke API. Use when building e-commerce pages with VTEX data, adding to cart, managing minicart, using VTEX loaders, or calling VTEX actions from islands.
---

# deco.cx VTEX Integration

Guide for integrating deco.cx with VTEX e-commerce using the official VTEX app.

## Overview

deco.cx connects to VTEX through the `apps/vtex` app, which provides:

- **Loaders** — fetch products, categories, search results, suggestions
- **Actions** — cart operations (add/remove/update items), wishlist, newsletter
- **Standard types** — `ProductListingPage`, `ProductDetailsPage`, `Product`, etc.

## Installing the VTEX app

The VTEX app is pre-installed in deco.cx storefront templates. If not, add it to your site's app configuration with the required VTEX credentials (account name, API keys).

## Standard commerce types

deco.cx uses schema.org-based standard types for commerce data, making sections portable across VTEX, Shopify, and other platforms.

| Type | Description |
|---|---|
| `Product` | Product with name, images, offers, variants |
| `ProductListingPage` | PLP with products array, filters, breadcrumb, pagination |
| `ProductDetailsPage` | PDP with full product data and breadcrumb |
| `BreadcrumbList` | Navigation breadcrumb |
| `Filter` | Facet filter with values |
| `SortOption` | Sort option for PLPs |

Import from:

```ts
import type { Product, ProductListingPage, ProductDetailsPage } from "apps/commerce/types.ts";
```

## Product Listing Page (PLP)

### Section receiving PLP data

```tsx
// sections/ProductShelf.tsx
import type { Product } from "apps/commerce/types.ts";
import type { SectionProps } from "deco/mod.ts";
import Image from "apps/website/components/Image.tsx";
import AddToCartButton from "../islands/AddToCartButton.tsx";

export interface Props {
  /** @title Section title */
  title: string;
  /** @title Products */
  products: Product[] | null;
  /** @title Columns */
  columns?: "2" | "3" | "4";
}

export default function ProductShelf({
  title,
  products,
  columns = "4",
}: Props) {
  if (!products?.length) return null;

  const colsClass = {
    "2": "grid-cols-2",
    "3": "grid-cols-3",
    "4": "grid-cols-2 lg:grid-cols-4",
  };

  return (
    <section class="py-8">
      <div class="container mx-auto px-4">
        <h2 class="text-2xl font-bold mb-6">{title}</h2>
        <div class={`grid gap-4 ${colsClass[columns]}`}>
          {products.map((product) => {
            const image = product.image?.[0];
            const offer = product.offers?.lowPrice;
            const seller = product.offers?.offers?.[0]?.seller || "1";

            return (
              <div class="card bg-base-100 shadow-sm">
                {image && (
                  <figure>
                    <Image
                      src={image.url || ""}
                      alt={image.alternateName || product.name || ""}
                      width={300}
                      height={300}
                      class="w-full"
                    />
                  </figure>
                )}
                <div class="card-body p-3">
                  <h3 class="text-sm line-clamp-2">{product.name}</h3>
                  {offer && (
                    <p class="text-lg font-bold text-primary">
                      R$ {offer.toFixed(2)}
                    </p>
                  )}
                  <AddToCartButton
                    productId={product.productID}
                    seller={seller}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
```

In the Admin, connect the `products` prop to a VTEX loader like `vtex/loaders/intelligentSearch/productList.ts`.

## Product Details Page (PDP)

```tsx
// sections/ProductDetails.tsx
import type { ProductDetailsPage } from "apps/commerce/types.ts";
import Image from "apps/website/components/Image.tsx";
import AddToCartButton from "../islands/AddToCartButton.tsx";
import QuantitySelector from "../islands/QuantitySelector.tsx";

export interface Props {
  /** @title hide */
  page: ProductDetailsPage | null;
}

export default function ProductDetails({ page }: Props) {
  if (!page?.product) {
    return <div class="container mx-auto p-8">Product not found</div>;
  }

  const { product, breadcrumbList } = page;
  const image = product.image?.[0];
  const offer = product.offers?.offers?.[0];
  const price = offer?.price;
  const listPrice = offer?.priceSpecification?.find(
    (s) => s.priceType === "https://schema.org/ListPrice",
  )?.price;
  const seller = offer?.seller || "1";

  return (
    <section class="container mx-auto px-4 py-8">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Image */}
        <div>
          {image && (
            <Image
              src={image.url || ""}
              alt={product.name || ""}
              width={600}
              height={600}
              class="w-full rounded-lg"
            />
          )}
        </div>

        {/* Info */}
        <div>
          <h1 class="text-3xl font-bold">{product.name}</h1>

          {listPrice && listPrice > (price || 0) && (
            <p class="text-sm line-through text-gray-400 mt-2">
              R$ {listPrice.toFixed(2)}
            </p>
          )}
          {price && (
            <p class="text-2xl font-bold text-primary">
              R$ {price.toFixed(2)}
            </p>
          )}

          <div class="mt-6 flex gap-4">
            <QuantitySelector />
            <AddToCartButton
              productId={product.productID}
              seller={seller}
            />
          </div>

          {product.description && (
            <div class="mt-8 prose" dangerouslySetInnerHTML={{ __html: product.description }} />
          )}
        </div>
      </div>
    </section>
  );
}
```

## Cart operations with invoke

Use `invoke` from `runtime.ts` to call VTEX actions from Islands.

### Add to cart

```tsx
import { invoke } from "../runtime.ts";

await invoke.vtex.actions.cart.addItems({
  orderItems: [{
    id: productId,    // SKU ID
    seller: "1",
    quantity: 1,
  }],
});
```

### Update item quantity

```tsx
await invoke.vtex.actions.cart.updateItems({
  orderItems: [{
    index: 0,         // item index in cart
    quantity: 3,
  }],
});
```

### Remove item

```tsx
await invoke.vtex.actions.cart.updateItems({
  orderItems: [{
    index: itemIndex,
    quantity: 0,       // quantity 0 = remove
  }],
});
```

### Get cart (simulate)

```tsx
const cart = await invoke.vtex.loaders.cart.loader({});
```

### Apply coupon

```tsx
await invoke.vtex.actions.cart.updateCoupons({
  text: "DISCOUNT20",
});
```

## Search with Intelligent Search

### Loader props for product search

The VTEX Intelligent Search loader supports:

| Prop | Type | Description |
|---|---|---|
| `query` | `string` | Search term |
| `count` | `number` | Products per page |
| `page` | `number` | Page number (0-based) |
| `sort` | `string` | Sort order |
| `selectedFacets` | `array` | Active filters |

### Sort options

| Value | Description |
|---|---|
| `"" ` | Relevance |
| `"price:asc"` | Price low to high |
| `"price:desc"` | Price high to low |
| `"orders:desc"` | Best sellers |
| `"name:asc"` | Name A-Z |
| `"name:desc"` | Name Z-A |
| `"release:desc"` | Newest first |
| `"discount:desc"` | Biggest discounts |

## Calling VTEX loaders from Islands

```tsx
// islands/SearchResults.tsx
import { invoke } from "../runtime.ts";
import { useSignal } from "@preact/signals";

export default function SearchResults() {
  const products = useSignal([]);
  const loading = useSignal(false);

  const search = async (query: string) => {
    loading.value = true;
    try {
      const result = await invoke.vtex.loaders.intelligentSearch.productList({
        query,
        count: 12,
      });
      products.value = result || [];
    } finally {
      loading.value = false;
    }
  };

  return (
    <div>
      <input
        type="text"
        placeholder="Search products..."
        class="input input-bordered w-full"
        onInput={(e) => search(e.currentTarget.value)}
      />
      {loading.value && <span class="loading loading-spinner" />}
      <div class="grid grid-cols-3 gap-4 mt-4">
        {products.value.map((p) => (
          <div key={p.productID}>{p.name}</div>
        ))}
      </div>
    </div>
  );
}
```

## Batching invoke calls

```tsx
const { products, cart } = await invoke({
  products: invoke.vtex.loaders.intelligentSearch.productList({
    query: "shoes",
    count: 8,
  }),
  cart: invoke.vtex.loaders.cart.loader({}),
});
```

## Best practices

1. **Use standard commerce types** (`Product`, `ProductListingPage`) for portable sections
2. **Connect loaders in the Admin** — plug VTEX loaders into section props via the visual editor
3. **Minimize data in Islands** — send only `productID` and `seller` to AddToCart buttons
4. **Use `invoke`** for cart operations — never call VTEX APIs directly from Islands
5. **Batch invoke calls** when you need multiple pieces of data simultaneously
6. **Handle null data** — loaders may return `null` if VTEX API fails; always guard with `if (!data) return null`
7. **Use VTEX Intelligent Search** for product search — it handles fuzzy matching, synonyms, and merchandising rules
8. **Filter data in loaders** — extract only needed fields (name, price, image) before sending to sections
9. **Use deferred sections** for below-fold product shelves to improve initial page load
10. **Test with real VTEX data** — mock data may not cover edge cases like variant selectors and promotions
