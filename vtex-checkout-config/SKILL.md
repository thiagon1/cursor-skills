---
name: vtex-checkout-config
description: Manages VTEX Checkout API Configuration endpoints — orderForm configuration (get/update), seller exchange window (get/update), and clear orderForm messages. Use when working with orderForm settings, paymentConfiguration, taxConfiguration, recaptchaValidation, custom apps registration, seller window, or the Checkout REST API configuration section.
---

# VTEX Checkout API — Configuration

REST API endpoints for managing the orderForm configuration at account level, the seller exchange window, and clearing cart messages.

**Base URL:** `https://{accountName}.{environment.com.br}`

**Auth headers (all endpoints):**

| Header | Value |
|---|---|
| `X-VTEX-API-AppKey` | Your app key |
| `X-VTEX-API-AppToken` | Your app token |

**Important:** Data modification operations (POST/PATCH/PUT/DELETE) must NOT run in parallel — enqueue them sequentially to avoid race conditions.

---

## 1. Get orderForm configuration

Retrieves the current orderForm configuration for the account.

```
GET /api/checkout/pvt/configuration/orderForm
```

**Response 200** — returns the full configuration object. See [reference.md](reference.md) for all fields.

```json
{
  "paymentConfiguration": {
    "requiresAuthenticationForPreAuthorizedPaymentOption": false,
    "allowInstallmentsMerge": null,
    "blockPaymentSession": null,
    "paymentSystemToCheckFirstInstallment": null,
    "defaultPaymentSystemToApplyOnUserOrderForm": null
  },
  "taxConfiguration": null,
  "minimumQuantityAccumulatedForItems": 1,
  "decimalDigitsPrecision": 2,
  "minimumValueAccumulated": 0,
  "apps": [],
  "allowMultipleDeliveries": false,
  "allowManualPrice": true,
  "savePersonalDataAsOptIn": false,
  "maxNumberOfWhiteLabelSellers": null,
  "maskFirstPurchaseData": null,
  "recaptchaValidation": null,
  "maskStateOnAddress": null
}
```

---

## 2. Update orderForm configuration

Updates the account's orderForm configuration. **Always GET first**, then modify only the needed fields to avoid overwriting existing values.

```
POST /api/checkout/pvt/configuration/orderForm
```

**Response:** `204 No Content`

### Mandatory fields

- `paymentConfiguration.requiresAuthenticationForPreAuthorizedPaymentOption`
- `minimumQuantityAccumulatedForItems`

### Request body example

```json
{
  "paymentConfiguration": {
    "requiresAuthenticationForPreAuthorizedPaymentOption": true
  },
  "recaptchaValidation": "vtexCriteria",
  "minimumValueAccumulated": 5,
  "maxNumberOfWhiteLabelSellers": 2,
  "maskFirstPurchaseData": false,
  "decimalDigitsPrecision": 2,
  "minimumQuantityAccumulatedForItems": 8,
  "requiresLoginToPlaceOrder": true,
  "minimumPurchaseDowntimeSeconds": 90,
  "cartAgeToUseNewCardSeconds": 30,
  "apps": [
    {
      "fields": ["gender", "age"],
      "id": "profile",
      "major": 1
    }
  ]
}
```

### Workflow: safe update pattern

```bash
# 1. GET current config
curl -s -X GET \
  "https://{account}.{env}/api/checkout/pvt/configuration/orderForm" \
  -H "X-VTEX-API-AppKey: {key}" \
  -H "X-VTEX-API-AppToken: {token}" \
  -o current-config.json

# 2. Edit current-config.json (modify only desired fields)

# 3. POST updated config
curl -s -X POST \
  "https://{account}.{env}/api/checkout/pvt/configuration/orderForm" \
  -H "Content-Type: application/json" \
  -H "X-VTEX-API-AppKey: {key}" \
  -H "X-VTEX-API-AppToken: {token}" \
  -d @current-config.json
```

---

## 3. Get window to change seller

Returns the current seller exchange window (in days). Default: 2 days. Max: 30 days.

```
GET /api/checkout/pvt/configuration/window-to-change-seller
```

**Response 200** — plain number (e.g. `"4"`)

---

## 4. Update window to change seller

Sets the seller exchange window period in days.

```
POST /api/checkout/pvt/configuration/window-to-change-seller
```

**Response:** `201 Created`

```json
{
  "waitingTime": 10
}
```

---

## 5. Clear orderForm messages

Removes all messages from a specific cart's `messages` array.

```
POST /api/checkout/pub/orderForm/{orderFormId}/messages/clear
```

**Request body:** `{}`

**Response 200** — returns the updated orderForm with `"messages": []`.

---

## Common scenarios

### Register custom app fields

Custom data on the orderForm requires registering an app via the configuration endpoint:

```json
{
  "paymentConfiguration": {
    "requiresAuthenticationForPreAuthorizedPaymentOption": false
  },
  "minimumQuantityAccumulatedForItems": 1,
  "apps": [
    {
      "fields": ["deliveryDate", "deliveryWindow"],
      "id": "delivery-scheduler",
      "major": 1
    }
  ]
}
```

After registration, these fields become available via `PUT /api/checkout/pub/orderForm/{orderFormId}/customData/{appId}/{fieldName}`.

### Configure external tax service

```json
{
  "paymentConfiguration": {
    "requiresAuthenticationForPreAuthorizedPaymentOption": false
  },
  "minimumQuantityAccumulatedForItems": 1,
  "taxConfiguration": {
    "url": "https://my-tax-service.com/api/tax",
    "authorizationHeader": "Bearer my-token",
    "appId": "my-tax-app"
  }
}
```

### Enable reCAPTCHA

Valid values: `null` (disabled), `"vtexCriteria"` (VTEX decides when to show), `"always"` (always show).

```json
{
  "paymentConfiguration": {
    "requiresAuthenticationForPreAuthorizedPaymentOption": false
  },
  "minimumQuantityAccumulatedForItems": 1,
  "recaptchaValidation": "vtexCriteria"
}
```

## Error codes

| Code | Status | Description |
|---|---|---|
| `ORD062` | 401 | Unauthorized — invalid or insufficient credentials |
| `001` | 400 | Bad Request — invalid body (clear messages expects `{}`) |
| `ORD002` | 400 | Invalid cart — `orderFormId` not found |
| — | 404 | URL not found — check account name and path |

## Additional resources

- For complete field descriptions and types, see [reference.md](reference.md)
- [Checkout API Overview](https://developers.vtex.com/docs/guides/checkout-api-overview)
- [orderForm fields reference](https://developers.vtex.com/docs/guides/orderform-fields)
- [Configuration quick start guides](https://developers.vtex.com/docs/guides/configuration-section-api-quick-start-guides)
