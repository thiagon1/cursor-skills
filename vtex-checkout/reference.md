# vtex.js Checkout API Reference

Complete API reference for the `vtexjs.checkout` module.

---

## getOrderForm(expectedOrderFormSections)

Gets the current orderForm. **Must be called before any mutation.**

**Returns:** `Promise<orderForm>`

```js
vtexjs.checkout.getOrderForm()
  .done(function(orderForm) {
    console.log(orderForm);
  });
```

---

## sendAttachment(attachmentId, attachment, expectedOrderFormSections)

Sends a complete attachment (section) to the current orderForm. **Must send the entire attachment object**, not just changed fields.

**Arguments:**

| Name | Type | Description |
|---|---|---|
| `attachmentId` | String | Attachment name (e.g. `clientProfileData`, `openTextField`) |
| `attachment` | Object | The complete attachment object |

**Returns:** `Promise<orderForm>`

### Example: update clientProfileData

```js
vtexjs.checkout.getOrderForm()
  .then(function(orderForm) {
    var clientProfileData = orderForm.clientProfileData;
    clientProfileData.firstName = 'Guilherme';
    return vtexjs.checkout.sendAttachment('clientProfileData', clientProfileData);
  }).done(function(orderForm) {
    console.log(orderForm.clientProfileData);
  });
```

### Example: set openTextField (order notes)

```js
vtexjs.checkout.getOrderForm()
  .then(function() {
    return vtexjs.checkout.sendAttachment('openTextField', { value: 'Sem cebola!' });
  }).done(function(orderForm) {
    console.log(orderForm.openTextField);
  });
```

---

## addToCart(items, expectedOrderFormSections, salesChannel)

Adds items to the cart. Items already in the cart remain unchanged.

**Does NOT auto-apply UTM promotions.** Send `marketingData` via `sendAttachment` separately.

**Arguments:**

| Name | Type | Description |
|---|---|---|
| `items` | Array | Items with `id`, `quantity`, `seller` (always an Array) |
| `salesChannel` | Number/String | Optional, default `1` |

**Returns:** `Promise<orderForm>`

```js
var item = { id: 2000017893, quantity: 1, seller: '1' };
vtexjs.checkout.addToCart([item], null, 3)
  .done(function(orderForm) {
    console.log(orderForm);
  });
```

---

## updateItems(items, expectedOrderFormSections, splitItem)

Updates items in the cart. Items identified by their `index` property.

Unchanged properties and non-sent items remain as-is.

**Arguments:**

| Name | Type | Description |
|---|---|---|
| `items` | Array | Items with `index` and properties to change |
| `splitItem` | Boolean | Default `true`. If `true`, creates a separate item when attachments/services exist |

**Returns:** `Promise<orderForm>`

```js
vtexjs.checkout.getOrderForm()
  .then(function(orderForm) {
    return vtexjs.checkout.updateItems([{ index: 0, quantity: 5 }], null, false);
  })
  .done(function(orderForm) {
    console.log(orderForm);
  });
```

---

## removeItems(items, expectedOrderFormSections)

Removes items from the cart by `index`.

**Arguments:**

| Name | Type | Description |
|---|---|---|
| `items` | Array | Items with `index` and `quantity: 0` |

**Returns:** `Promise<orderForm>`

```js
vtexjs.checkout.getOrderForm()
  .then(function(orderForm) {
    return vtexjs.checkout.removeItems([{ index: 0, quantity: 0 }]);
  })
  .done(function(orderForm) {
    console.log(orderForm);
  });
```

---

## removeAllItems(expectedOrderFormSections)

Removes all items from the cart.

**Returns:** `Promise<orderForm>`

```js
vtexjs.checkout.removeAllItems()
  .done(function(orderForm) {
    console.log(orderForm);
  });
```

---

## cloneItem(itemIndex, newItemsOptions, expectedOrderFormSections)

Creates one or more items based on an existing item (that must have an attachment).

**Arguments:**

| Name | Type | Description |
|---|---|---|
| `itemIndex` | Number | Index of the source item |
| `newItemsOptions` | Array | Optional. Properties for the new items |

**Returns:** `Promise<orderForm>`

```js
var newItemsOptions = [{
  itemAttachments: [{
    name: 'Personalização',
    content: { Nome: 'Ronaldo' }
  }],
  quantity: 2
}];

vtexjs.checkout.cloneItem(0, newItemsOptions)
  .done(function(orderForm) {
    console.log(orderForm);
  });
```

---

## calculateShipping(address)

Registers address in `shippingData` and calculates shipping. Result appears in `totalizers`.

**Arguments:**

| Name | Type | Description |
|---|---|---|
| `address` | Object | Must have at least `postalCode` and `country` |

**Returns:** `Promise<orderForm>`

```js
vtexjs.checkout.getOrderForm()
  .then(function() {
    return vtexjs.checkout.calculateShipping({
      postalCode: '22250-040',
      country: 'BRA'
    });
  })
  .done(function(orderForm) {
    console.log(orderForm.shippingData);
    console.log(orderForm.totalizers);
  });
```

---

## simulateShipping(items, postalCode, country, salesChannel) [DEPRECATED]

Simulates shipping for arbitrary items without binding the address to the user. Ideal for product page shipping estimates.

**Arguments:**

| Name | Type | Description |
|---|---|---|
| `items` | Array | Items with `id`, `quantity`, `seller` |
| `postalCode` | String | CEP (with or without hyphen) |
| `country` | String | 3-letter country code (e.g. `BRA`) |
| `salesChannel` | Number/String | Optional, default `1` |

**Returns:** `Promise` with `logisticsInfo` property

```js
var items = [{ id: 5987, quantity: 1, seller: '1' }];

vtexjs.checkout.simulateShipping(items, '22250-040', 'BRA')
  .done(function(result) {
    // result.logisticsInfo[0].slas → array of carriers (name, price, deliveryTime)
  });
```

---

## simulateShipping(shippingData, orderFormId, country, salesChannel)

Polymorphic overload. Simulates shipping using `shippingData` object with `logisticsInfo` and `selectedAddresses`.

**Arguments:**

| Name | Type | Description |
|---|---|---|
| `shippingData` | Object | Contains `logisticsInfo` and `selectedAddresses` |
| `orderFormId` | String | The orderForm ID |
| `country` | String | 3-letter country code |
| `salesChannel` | Number/String | Optional, default `1` |

**Returns:** `Promise` with `logisticsInfo` property

```js
var shippingData = {
  logisticsInfo: logisticsInfoList,
  selectedAddresses: selectedAddressesList
};
var orderFormId = '9f879d435f8b402cb133167d6058c14f';

vtexjs.checkout.simulateShipping(shippingData, orderFormId, 'BRA')
  .done(function(result) {
    // result.logisticsInfo[0].slas
  });
```

---

## getAddressInformation(address)

Returns a complete address from a partial one (postalCode + country).

**Arguments:**

| Name | Type | Description |
|---|---|---|
| `address` | Object | Must have `postalCode` and `country` |

**Returns:** `Promise<address>` (complete with city, state, street, etc.)

```js
vtexjs.checkout.getAddressInformation({
  postalCode: '22250-040',
  country: 'BRA'
}).done(function(result) {
  console.log(result);
});
```

---

## getProfileByEmail(email, salesChannel)

Partial login by email. Data may come masked for existing users (requires VTEX ID auth for full access). Check `orderForm.canEditData`.

**Arguments:**

| Name | Type | Description |
|---|---|---|
| `email` | String | Customer email |
| `salesChannel` | Number/String | Default `1` |

**Returns:** `Promise<orderForm>`

```js
vtexjs.checkout.getOrderForm()
  .then(function() {
    return vtexjs.checkout.getProfileByEmail('user@example.com');
  })
  .done(function(orderForm) {
    console.log(orderForm);
  });
```

---

## removeAccountId(accountId, expectedOrderFormSections)

Removes a payment account. Account IDs found in `orderForm.paymentData.availableAccounts`.

**Arguments:**

| Name | Type | Description |
|---|---|---|
| `accountId` | String | Payment account ID |

**Returns:** `Promise`

```js
vtexjs.checkout.getOrderForm()
  .then(function(orderForm) {
    var accountId = orderForm.paymentData.availableAccounts[0].accountId;
    return vtexjs.checkout.removeAccountId(accountId);
  });
```

---

## addDiscountCoupon(couponCode, expectedOrderFormSections)

Adds a discount coupon. Only one coupon per order.

**Arguments:**

| Name | Type | Description |
|---|---|---|
| `couponCode` | String | Coupon code |

**Returns:** `Promise<orderForm>`

```js
vtexjs.checkout.getOrderForm()
  .then(function() {
    return vtexjs.checkout.addDiscountCoupon('ABC123');
  }).then(function(orderForm) {
    console.log(orderForm.paymentData);
    console.log(orderForm.totalizers);
  });
```

---

## removeDiscountCoupon(expectedOrderFormSections)

Removes the discount coupon from the order.

**Returns:** `Promise<orderForm>`

```js
vtexjs.checkout.getOrderForm()
  .then(function() {
    return vtexjs.checkout.removeDiscountCoupon();
  });
```

---

## removeGiftRegistry(expectedOrderFormSections)

Unlinks a gift registry from the orderForm (no-op if not linked).

**Returns:** `Promise<orderForm>`

---

## addOffering(offeringId, itemIndex, expectedOrderFormSections)

Adds an offering (e.g. warranty, installation) to an item. Once added, it appears in the item's `bundleItems`.

**Arguments:**

| Name | Type | Description |
|---|---|---|
| `offeringId` | String/Number | The offering `id` |
| `itemIndex` | Number | Index of the target item |

**Returns:** `Promise<orderForm>`

```js
var offeringId = items[0].offerings[0].id;
vtexjs.checkout.getOrderForm()
  .then(function() {
    return vtexjs.checkout.addOffering(offeringId, 0);
  });
```

---

## removeOffering(offeringId, itemIndex, expectedOrderFormSections)

Removes an offering from an item.

**Arguments:** same as `addOffering`.

**Returns:** `Promise<orderForm>`

---

## addItemAttachment(itemIndex, attachmentName, content, expectedOrderFormSections, splitItem)

Adds an attachment (extra info) to a cart item. Check `item.attachmentOfferings` for available attachments.

**Important:** always send the complete `content` object with ALL properties, even unchanged ones.

**Arguments:**

| Name | Type | Description |
|---|---|---|
| `itemIndex` | Number | Item index |
| `attachmentName` | String | Name from `attachmentOfferings` |
| `content` | Object | Must match the attachment schema (all properties required) |
| `splitItem` | Boolean | Default `true`. Creates separate item if attachments exist |

**Returns:** `Promise<orderForm>`

**Errors:**
- `404` — item doesn't have this attachment or invalid `content` property
- `400` — `content` object malformed

```js
var content = { Nome: 'Ronaldo', Numero: '10' };
vtexjs.checkout.addItemAttachment(0, 'Customização', content)
  .done(function(orderForm) {
    console.log(orderForm);
  });
```

---

## removeItemAttachment(itemIndex, attachmentName, content, expectedOrderFormSections)

Removes an attachment from an item.

**Arguments:** same as `addItemAttachment` (without `splitItem`).

**Returns:** `Promise<orderForm>`

---

## addBundleItemAttachment(itemIndex, bundleItemId, attachmentName, content, expectedOrderFormSections)

Adds an attachment to a service (bundleItem) of an item.

**Arguments:**

| Name | Type | Description |
|---|---|---|
| `itemIndex` | Number | Item index |
| `bundleItemId` | String/Number | The bundleItem `id` |
| `attachmentName` | String | Name from service's `attachmentOfferings` |
| `content` | Object | Must match the attachment schema |

**Returns:** `Promise<orderForm>`

```js
vtexjs.checkout.addBundleItemAttachment(0, 5, 'message', { text: 'Parabéns!' });
```

---

## removeBundleItemAttachment(itemIndex, bundleItemId, attachmentName, content, expectedOrderFormSections)

Removes an attachment from a service.

**Arguments:** same as `addBundleItemAttachment`.

**Returns:** `Promise<orderForm>`

---

## sendLocale(locale)

Changes the user's locale. Updates `clientPreferencesData`.

**Arguments:**

| Name | Type | Description |
|---|---|---|
| `locale` | String | e.g. `pt-BR`, `en-US` |

**Returns:** `Promise`

---

## clearMessages(expectedOrderFormSections)

Clears info/error messages from `orderForm.messages`.

**Returns:** `Promise`

---

## getLogoutURL()

Returns a URL that logs the user out while keeping their cart.

**Returns:** `String`

```js
var logoutURL = vtexjs.checkout.getLogoutURL();
window.location = logoutURL;
```

---

## getOrders(orderGroupId)

Gets orders within an order group. A group like `v50123456abc` may contain `v50123456abc-01`, `v50123456abc-02` (split by seller).

**Arguments:**

| Name | Type | Description |
|---|---|---|
| `orderGroupId` | String | e.g. `v50123456abc` |

**Returns:** `Promise<Array<order>>`

```js
vtexjs.checkout.getOrders('v50123456abc')
  .then(function(orders) {
    console.log(orders.length);
  });
```

---

## changeItemsOrdination(criteria, ascending, expectedOrderFormSections)

Reorders cart items. Updates `itemsOrdination` and the `items` array order.

**Arguments:**

| Name | Type | Description |
|---|---|---|
| `criteria` | String | `name` or `add_time` |
| `ascending` | Boolean | `true` = ascending, `false` = descending |

**Returns:** `Promise<orderForm>`

---

## replaceSKU(items, expectedOrderFormSections, splitItem)

Replaces an item's SKU: removes the current one (quantity 0) and adds a new one in a single operation.

**Arguments:**

| Name | Type | Description |
|---|---|---|
| `items` | Array | First element: item to remove (`index`, `quantity: 0`). Second: new item (`id`, `quantity`, `seller`) |
| `splitItem` | Boolean | Default `true` |

**Returns:** `Promise<orderForm>`

```js
var items = [
  { seller: '1', quantity: 0, index: 0 },
  { seller: '1', quantity: 1, id: '2' }
];

vtexjs.checkout.replaceSKU(items)
  .then(function(orderForm) {
    console.log(orderForm.items);
  });
```

---

## finishTransaction(orderGroupId, expectedOrderFormSections)

Tells the checkout API to finish a transaction and redirect to the final URL (e.g. order-placed).

**Arguments:**

| Name | Type | Description |
|---|---|---|
| `orderGroupId` | Number | Order ID at purchase time |

**Returns:** `Promise<orderForm>`

```js
vtexjs.checkout.finishTransaction('959290226406')
  .then(function(response) {
    console.log(response.status);
  });
```

---

## OrderForm sections reference

All available sections (from `_allOrderFormSections`):

| Section | Content |
|---|---|
| `items` | Cart items (SKU, name, qty, price, seller, imageUrl) |
| `totalizers` | Totals breakdown (Items, Shipping, Discounts) |
| `clientProfileData` | Name, email, document, phone |
| `shippingData` | Address, logisticsInfo, selectedAddresses |
| `paymentData` | Payment info, installments, availableAccounts |
| `sellers` | Seller details |
| `messages` | API messages (info/error) |
| `marketingData` | UTM params, coupon, campaign |
| `clientPreferencesData` | Locale, opt-in newsletter |
| `storePreferencesData` | Currency, country, time zone |
| `giftRegistryData` | Gift registry info |
| `openTextField` | Free-text order notes |
| `commercialConditionData` | Commercial conditions |
| `customData` | Custom app data |
