---
name: vtex-checkout
description: Customizes VTEX Checkout v6 using vtex.js Checkout module, orderForm manipulation, cart operations, shipping calculation, coupons, and checkout events. Use when editing checkout6-custom.js, working with vtex.js checkout API, manipulating orderForm, adding/removing cart items, calculating shipping, applying coupons, handling checkout events (orderFormUpdated, checkoutRequestBegin/End), or customizing VTEX checkout behavior.
---

# VTEX Checkout Customization

Guide for customizing VTEX Checkout v6 via `checkout6-custom.js` using the `vtex.js` Checkout module.

## Project structure

```
checkout/
├── js/
│   ├── checkout6-custom.js           ← main customization file
│   └── checkout-confirmation-custom.js
├── css/
│   └── checkout6-custom.css          ← checkout styles
├── html/
│   ├── checkout-header.html
│   └── checkout-footer.html
├── configurations/
│   └── orderform-configuration.json
└── img/
```

## Core concepts

### OrderForm

The `orderForm` is the central data structure for a purchase. Key sections:

| Section | Description |
|---|---|
| `items` | Array of cart items (SKU, qty, price, seller) |
| `clientProfileData` | Customer personal info |
| `shippingData` | Address + shipping options (`logisticsInfo`) |
| `paymentData` | Payment methods and available accounts |
| `totalizers` | Array of totals (items, shipping, discounts) |
| `marketingData` | UTM, coupons, campaign info |
| `openTextField` | Free-text field for order notes |
| `messages` | Info/error messages from the API |
| `sellers` | Available sellers info |
| `storePreferencesData` | Currency, time zone, locale |

### vtexjs.checkout instance

All methods live on `vtexjs.checkout`. Always call `getOrderForm()` before any mutation to ensure the orderForm is loaded.

### Successive requests

The module auto-cancels duplicate in-flight requests for the same operation — only the last request resolves. Use separate `vtexjs.Checkout()` instances per plugin if needed, or listen to `orderFormUpdated.vtex` for state changes.

### expectedOrderFormSections

Most methods accept an optional `expectedOrderFormSections` array to limit which sections are returned. Omit it to get all sections (safe default).

## Events

```js
// OrderForm updated (fires after last pending request completes)
$(window).on('orderFormUpdated.vtex', function(evt, orderForm) {
  console.log(orderForm);
});

// Request started — show loading state
$(window).on('checkoutRequestBegin.vtex', function(evt, ajaxOptions) {
  // block UI
});

// Request ended (success or failure)
$(window).on('checkoutRequestEnd.vtex', function(evt, orderFormOrJqXHR) {
  // unblock UI
});
```

**Tip:** prefer `orderFormUpdated.vtex` over `checkoutRequestEnd.vtex` for reacting to orderForm changes.

## Common operations

### Get orderForm

```js
vtexjs.checkout.getOrderForm()
  .done(function(orderForm) {
    console.log(orderForm);
  });
```

### Add item to cart

```js
var item = { id: 2000017893, quantity: 1, seller: '1' };
vtexjs.checkout.addToCart([item], null, 3)
  .done(function(orderForm) {
    console.log(orderForm);
  });
```

`addToCart` does NOT auto-apply UTM promotions. Send a `sendAttachment('marketingData', {...})` separately.

### Update item quantity

```js
vtexjs.checkout.getOrderForm()
  .then(function(orderForm) {
    return vtexjs.checkout.updateItems([{ index: 0, quantity: 5 }], null, false);
  })
  .done(function(orderForm) {
    console.log(orderForm);
  });
```

### Remove item / clear cart

```js
// Remove specific item (set quantity 0)
vtexjs.checkout.removeItems([{ index: 0, quantity: 0 }]);

// Remove ALL items
vtexjs.checkout.removeAllItems();
```

### Calculate shipping

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

### Simulate shipping (product page)

```js
var items = [{ id: 5987, quantity: 1, seller: '1' }];
vtexjs.checkout.simulateShipping(items, '22250-040', 'BRA')
  .done(function(result) {
    // result.logisticsInfo[0].slas → carriers with price/time
  });
```

### Apply / remove coupon

```js
// Apply
vtexjs.checkout.addDiscountCoupon('ABC123');

// Remove
vtexjs.checkout.removeDiscountCoupon();
```

### Update attachment (e.g. clientProfileData)

```js
vtexjs.checkout.getOrderForm()
  .then(function(orderForm) {
    var profile = orderForm.clientProfileData;
    profile.firstName = 'João';
    return vtexjs.checkout.sendAttachment('clientProfileData', profile);
  });
```

**Important:** always send the complete attachment object, not just changed fields.

### Address lookup by CEP

```js
vtexjs.checkout.getAddressInformation({
  postalCode: '22250040',
  country: 'BRA'
}).done(function(address) {
  console.log(address); // full address with city, state, street
});
```

### Partial login by email

```js
vtexjs.checkout.getProfileByEmail('user@example.com');
```

Returns masked data if user exists. Check `orderForm.canEditData` for edit permissions.

### Logout (keep cart)

```js
var logoutURL = vtexjs.checkout.getLogoutURL();
window.location = logoutURL;
```

## checkout6-custom.js patterns

This project uses a `Checkout` object with a `methods` namespace and an `init` function:

```js
var Checkout = {
  methods: {
    myFeature: function() {
      // feature implementation
    },
  },
  init: function() {
    Checkout.methods.myFeature();
  }
};

$(document).ready(function() {
  Checkout.init();
});
```

### Hash-based step detection

Checkout steps are identified by the URL hash:

| Hash | Step |
|---|---|
| `#/cart` | Cart |
| `#/email` | Email identification |
| `#/profile` | Profile |
| `#/shipping` | Shipping address |
| `#/payment` | Payment |

```js
window.addEventListener('hashchange', function() {
  var step = window.location.hash.replace('#/', '');
  // "cart", "email", "profile", "shipping", "payment"
});
```

### DOM polling pattern

Checkout renders async. Use polling to wait for elements:

```js
var poll = setInterval(function() {
  var el = document.querySelector('.target-element');
  if (el) {
    clearInterval(poll);
    // work with el
  }
}, 250);
```

### Mobile detection

```js
function isMobile() {
  return window.innerWidth <= 768;
}
```

## Local proxy for testing

Use the proxy at `checkout/proxy/` to test CSS and JS changes locally without uploading to VTEX.

### Setup (first time)

```bash
cd checkout/proxy
npm install
```

### Running

```bash
npm run dev        # with live reload (recommended)
npm start          # without live reload
```

Then open `http://localhost:3000/checkout/#/cart` in the browser.

### How it works

The proxy intercepts requests for `/files/checkout6-custom.js` and `/files/checkout6-custom.css`, serving local files from `checkout/js/` and `checkout/css/` instead. All other requests are forwarded transparently to the VTEX workspace.

With `--live-reload`, saving a CSS file hot-reloads styles without full page refresh; saving a JS file triggers a full reload.

### Configuration (environment variables)

| Variable | Default | Description |
|---|---|---|
| `VTEX_WORKSPACE` | `task13631` | Workspace name |
| `VTEX_ACCOUNT` | `lojamm` | VTEX account |
| `PORT` | `3000` | Local port |

Example switching workspace:

```powershell
$env:VTEX_WORKSPACE="master"; npm run dev
```

### Adding more file overrides

Edit `LOCAL_OVERRIDES` in `checkout/proxy/server.js`:

```js
const LOCAL_OVERRIDES = {
  '/files/checkout6-custom.js': {
    localPath: path.resolve(__dirname, '..', 'js', 'checkout6-custom.js'),
    contentType: 'application/javascript; charset=utf-8',
  },
  '/files/checkout6-custom.css': {
    localPath: path.resolve(__dirname, '..', 'css', 'checkout6-custom.css'),
    contentType: 'text/css; charset=utf-8',
  },
  // Add more overrides here
};
```

### Troubleshooting

- **EADDRINUSE**: Port already in use. Kill the process: `netstat -ano | findstr :3000` then `taskkill /PID <pid> /F`
- **Cookies/auth issues**: Clear cookies for localhost and re-login through the proxy
- **502 errors**: Check that the VTEX workspace URL is accessible directly

## Best practices

1. **Always `getOrderForm()` first** before any mutation call
2. **Listen to `orderFormUpdated.vtex`** instead of chaining `.done()` for cross-component sync
3. **Send complete attachment objects** via `sendAttachment` — partial updates are not supported
4. **Use `setInterval` + `clearInterval`** for DOM element polling in async checkout rendering
5. **Scope features by hash step** — only run payment logic on `#/payment`, cart logic on `#/cart`, etc.
6. **Use separate Checkout instances** (`new vtexjs.Checkout()`) if multiple plugins call the same method concurrently
7. **Avoid blocking the main thread** — checkout is performance-sensitive
8. **Test on both desktop and mobile** — checkout layout differs significantly

## Additional resources

- For the complete vtex.js Checkout API (all methods, arguments, examples), see [reference.md](reference.md)
