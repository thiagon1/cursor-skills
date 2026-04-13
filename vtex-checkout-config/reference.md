# VTEX Checkout Configuration — Field Reference

Complete field reference for the orderForm configuration object returned by `GET /api/checkout/pvt/configuration/orderForm` and sent to `POST /api/checkout/pvt/configuration/orderForm`.

---

## Top-level fields

| Field | Type | Required on POST | Description |
|---|---|---|---|
| `paymentConfiguration` | object | Yes (partial) | Payment behavior settings |
| `taxConfiguration` | object \| null | No | External tax service integration |
| `minimumQuantityAccumulatedForItems` | integer | **Yes** | Minimum total SKU quantity allowed in the cart |
| `decimalDigitsPrecision` | integer | No | Number of decimal digits for prices |
| `minimumValueAccumulated` | integer | No | Minimum cart value (in cents) to allow checkout |
| `apps` | array | No | Custom data apps registered for the orderForm |
| `allowMultipleDeliveries` | boolean | No | Allow items from different delivery channels in same purchase |
| `allowManualPrice` | boolean | No | Allow manual editing of SKU prices in the cart |
| `savePersonalDataAsOptIn` | boolean | No | Let users opt-in to saving personal/payment data |
| `maxNumberOfWhiteLabelSellers` | integer \| null | No | Max white label sellers on the cart |
| `maskFirstPurchaseData` | boolean \| null | No | Mask client data on first purchase (useful for shared carts) |
| `recaptchaValidation` | string \| null | No | reCAPTCHA mode: `null`, `"vtexCriteria"`, or `"always"` |
| `maskStateOnAddress` | boolean \| null | No | Mask state field on address |
| `requiresLoginToPlaceOrder` | boolean | No | Require authentication to complete purchases |
| `minimumPurchaseDowntimeSeconds` | integer | No | Minimum interval (seconds) between successive purchases |
| `cartAgeToUseNewCardSeconds` | integer | No | Minimum cart age (seconds) before allowing a new credit card |

---

## paymentConfiguration

| Field | Type | Required | Description |
|---|---|---|---|
| `requiresAuthenticationForPreAuthorizedPaymentOption` | boolean | **Yes** | Whether pre-authorized payments require authentication |
| `allowInstallmentsMerge` | boolean \| null | No | Allow flexible installments across sellers in multi-seller orders |
| `blockPaymentSession` | boolean \| null | No | Block payment session |
| `paymentSystemToCheckFirstInstallment` | string \| null | No | Payment system ID for first installment discount |
| `defaultPaymentSystemToApplyOnUserOrderForm` | string \| null | No | Default payment system applied to user's orderForm |

---

## taxConfiguration

| Field | Type | Description |
|---|---|---|
| `url` | string | External tax service endpoint URL |
| `authorizationHeader` | string | Authorization header value sent to the tax service |
| `appId` | string | Custom data ID sent to the tax system |

When `taxConfiguration` is `null`, no external tax service is configured.

---

## apps

Array of custom data apps. Each app object:

| Field | Type | Description |
|---|---|---|
| `id` | string | App identifier (used as `appId` in custom data endpoints) |
| `fields` | array of strings | Field names available in this app |
| `major` | integer | App major version (typically `1`) |

### How apps work

1. Register an app via `POST /api/checkout/pvt/configuration/orderForm` with the `apps` array
2. Once registered, set values via `PUT /api/checkout/pub/orderForm/{orderFormId}/customData/{appId}/{fieldName}`
3. Values appear in `orderForm.customData.customApps[]`

### Example: registering multiple apps

```json
"apps": [
  {
    "fields": ["cart-extra-context", "cart-type"],
    "id": "cart-extra-context",
    "major": 1
  },
  {
    "fields": ["orderIdMarketplace", "paymentIdMarketplace"],
    "id": "marketplace-integration",
    "major": 1
  },
  {
    "fields": ["quantity", "deadlines_1", "interestRate"],
    "id": "customer-credit",
    "major": 1
  },
  {
    "fields": ["affiliateId"],
    "id": "affiliates",
    "major": 1
  }
]
```

---

## recaptchaValidation values

| Value | Behavior |
|---|---|
| `null` | Disabled |
| `"vtexCriteria"` | VTEX decides when to display reCAPTCHA based on risk analysis |
| `"always"` | Always display reCAPTCHA at checkout |

---

## Window to change seller

### GET response

Returns a plain string with the number of days (e.g. `"4"`).

### POST request body

| Field | Type | Description |
|---|---|---|
| `waitingTime` | integer | Number of days for the seller exchange window (max 30) |

---

## Clear orderForm messages

### Request

- **URL:** `POST /api/checkout/pub/orderForm/{orderFormId}/messages/clear`
- **Body:** `{}`
- **Path param:** `orderFormId` — the cart identifier

### Response

Returns the full orderForm with `"messages": []`.

The `messages` array normally contains objects like:

```json
{
  "code": null,
  "status": "error",
  "text": "Voucher code AAAA-BBBB-CCCC-DDDD was not found in the system"
}
```

---

## Error code reference

| Code | HTTP Status | Message | Cause |
|---|---|---|---|
| `ORD062` | 401 | Unauthorized | Invalid API key/token or insufficient permissions |
| `001` | 400 | Bad request | Invalid request body (e.g. non-empty body on clear messages) |
| `ORD002` | 400 | Carrinho inválido | `orderFormId` does not exist or is incorrect |
| — | 404 | The requested URL was not found | Wrong account name or endpoint path |
