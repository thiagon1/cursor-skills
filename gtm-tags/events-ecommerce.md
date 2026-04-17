# GA4 Ecommerce Events — Payload Reference

Full payload schemas for standard GA4 ecommerce events. All examples use BRL and illustrative values.

## Common rules

- Always `window.dataLayer.push({ ecommerce: null })` before pushing a new ecommerce event.
- `currency` is ISO 4217 (`BRL`, `USD`, `EUR`).
- `value` = sum of `item.price × item.quantity` for all items in the event (for most events).
- `items[]` must have at least `item_id` OR `item_name` (GA4 requires one of them).

## Item schema

All ecommerce events share the same `item` schema:

```javascript
{
  item_id: 'SKU123',              // required (or item_name)
  item_name: 'Camisa Polo Azul',  // required (or item_id)
  price: 199.90,                  // number, unit price
  quantity: 2,                    // integer
  currency: 'BRL',                // optional at item level
  item_brand: 'Brand Name',
  item_category: 'Roupas',
  item_category2: 'Masculino',
  item_category3: 'Camisas',
  item_category4: 'Polo',
  item_category5: 'Algodão',
  item_variant: 'Azul / M',
  item_list_name: 'Vitrine Home',
  item_list_id: 'home_shelf_1',
  index: 0,                       // position in list
  discount: 20.00,                // discount applied
  affiliation: 'Lojas MM',
  coupon: 'DESCONTO10',
  promotion_id: 'promo_123',
  promotion_name: 'Black Friday',
}
```

---

## view_item_list

Fires when user sees a list of products (PLP, search results, shelf).

```javascript
window.dataLayer.push({ ecommerce: null });
window.dataLayer.push({
  event: 'view_item_list',
  ecommerce: {
    item_list_id: 'plp_masculino',
    item_list_name: 'Categoria Masculino',
    items: [
      { item_id: 'SKU1', item_name: 'Produto A', price: 99.90, quantity: 1, index: 0 },
      { item_id: 'SKU2', item_name: 'Produto B', price: 149.90, quantity: 1, index: 1 },
    ],
  },
});
```

## select_item

Fires when user clicks a product card in a list.

```javascript
window.dataLayer.push({ ecommerce: null });
window.dataLayer.push({
  event: 'select_item',
  ecommerce: {
    item_list_id: 'plp_masculino',
    item_list_name: 'Categoria Masculino',
    items: [
      { item_id: 'SKU1', item_name: 'Produto A', price: 99.90, quantity: 1, index: 0 },
    ],
  },
});
```

## view_item

Fires on product detail page (PDP) load.

```javascript
window.dataLayer.push({ ecommerce: null });
window.dataLayer.push({
  event: 'view_item',
  ecommerce: {
    currency: 'BRL',
    value: 199.90,
    items: [
      {
        item_id: 'SKU123',
        item_name: 'Camisa Polo Azul',
        price: 199.90,
        quantity: 1,
        item_brand: 'Brand',
        item_category: 'Roupas',
        item_variant: 'Azul / M',
      },
    ],
  },
});
```

## add_to_cart

Fires when user adds a product to cart.

```javascript
window.dataLayer.push({ ecommerce: null });
window.dataLayer.push({
  event: 'add_to_cart',
  ecommerce: {
    currency: 'BRL',
    value: 199.90,
    items: [
      {
        item_id: 'SKU123',
        item_name: 'Camisa Polo Azul',
        price: 199.90,
        quantity: 1,
      },
    ],
  },
});
```

## remove_from_cart

```javascript
window.dataLayer.push({ ecommerce: null });
window.dataLayer.push({
  event: 'remove_from_cart',
  ecommerce: {
    currency: 'BRL',
    value: 199.90,
    items: [
      { item_id: 'SKU123', item_name: 'Camisa Polo Azul', price: 199.90, quantity: 1 },
    ],
  },
});
```

## view_cart

Fires when user opens cart / minicart.

```javascript
window.dataLayer.push({ ecommerce: null });
window.dataLayer.push({
  event: 'view_cart',
  ecommerce: {
    currency: 'BRL',
    value: 399.80,
    items: [
      { item_id: 'SKU123', item_name: 'Camisa Polo', price: 199.90, quantity: 1 },
      { item_id: 'SKU456', item_name: 'Tênis Runner', price: 199.90, quantity: 1 },
    ],
  },
});
```

## begin_checkout

Fires when user starts checkout flow.

```javascript
window.dataLayer.push({ ecommerce: null });
window.dataLayer.push({
  event: 'begin_checkout',
  ecommerce: {
    currency: 'BRL',
    value: 399.80,
    coupon: 'DESCONTO10',
    items: [
      { item_id: 'SKU123', item_name: 'Camisa Polo', price: 199.90, quantity: 1 },
      { item_id: 'SKU456', item_name: 'Tênis Runner', price: 199.90, quantity: 1 },
    ],
  },
});
```

## add_shipping_info

Fires when user completes shipping information step.

```javascript
window.dataLayer.push({ ecommerce: null });
window.dataLayer.push({
  event: 'add_shipping_info',
  ecommerce: {
    currency: 'BRL',
    value: 399.80,
    coupon: 'DESCONTO10',
    shipping_tier: 'Sedex',
    items: [ /* ... */ ],
  },
});
```

## add_payment_info

Fires when user completes payment information step.

```javascript
window.dataLayer.push({ ecommerce: null });
window.dataLayer.push({
  event: 'add_payment_info',
  ecommerce: {
    currency: 'BRL',
    value: 399.80,
    coupon: 'DESCONTO10',
    payment_type: 'Credit Card',
    items: [ /* ... */ ],
  },
});
```

## purchase

Fires on order confirmation page. `transaction_id` is **required** and must be unique.

```javascript
window.dataLayer.push({ ecommerce: null });
window.dataLayer.push({
  event: 'purchase',
  ecommerce: {
    transaction_id: 'order-123456',
    currency: 'BRL',
    value: 399.80,
    tax: 20.00,
    shipping: 15.00,
    coupon: 'DESCONTO10',
    items: [
      { item_id: 'SKU123', item_name: 'Camisa Polo', price: 199.90, quantity: 1 },
      { item_id: 'SKU456', item_name: 'Tênis Runner', price: 199.90, quantity: 1 },
    ],
  },
});
```

## refund (optional)

Fires when an order is refunded.

```javascript
window.dataLayer.push({ ecommerce: null });
window.dataLayer.push({
  event: 'refund',
  ecommerce: {
    transaction_id: 'order-123456',
    currency: 'BRL',
    value: 199.90,
    items: [ /* items refunded */ ],
  },
});
```

---

## VTEX orderForm → GA4 items mapping

When building ecommerce events from VTEX orderForm:

```javascript
const items = orderForm.items.map((item, index) => ({
  item_id: item.id,                          // SKU id
  item_name: item.name,
  price: item.sellingPrice / 100,            // VTEX uses cents
  quantity: item.quantity,
  item_brand: item.additionalInfo?.brandName,
  item_category: item.productCategories
    ? Object.values(item.productCategories)[0]
    : undefined,
  item_variant: item.skuName,
  index,
}));

const value = items.reduce(
  (sum, i) => sum + (i.price * i.quantity),
  0
);
```

Key fields in orderForm:
- `orderForm.items[].id` → SKU (use for `item_id`)
- `orderForm.items[].productId` → product ID (optional)
- `orderForm.items[].sellingPrice` → price in cents (divide by 100)
- `orderForm.items[].listPrice` → original price in cents
- `orderForm.value` → total in cents
- `orderForm.orderGroup` (in order placed) → `transaction_id`

## Debug / common mistakes

| Mistake | Fix |
|---|---|
| `quantity` as string (`"1"`) | Use integer (`1`) |
| `price` with comma (`"199,90"`) | Use number (`199.90`) |
| `value` missing or mismatching sum of items | Calculate `value = Σ(price × quantity)` |
| `items` as object instead of array | Always use `items: [...]` |
| Not clearing `ecommerce: null` before push | Always clear first |
| `transaction_id` reused across tests | Use real unique order ID |
| Empty `item_name` with just `item_id` | GA4 accepts, but both is better |
