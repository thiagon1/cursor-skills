---
name: gtm-tags
description: Audit, validate, debug, and implement Google Tag Manager tags, triggers, variables, and dataLayer events. Use when the user mentions GTM, Google Tag Manager, dataLayer, GA4, gtag, tags, triggers, pixels, tracking, or provides a GTM container ID / validation URL.
---

# GTM — Tags, Triggers, Events & Validation

End-to-end workflow for Google Tag Manager tasks: audit tags on a page, validate firing, identify problems, and implement new tags/events/triggers.

## Input

| Campo | Obrigatório | Descrição |
|-------|-------------|-----------|
| **URL de validação** | Sim | Página a ser inspecionada (homolog, workspace VTEX, ambiente do cliente) |
| **GTM Container ID** | Não | Ex.: `GTM-XXXXXX`. Se não fornecido, é extraído da página |
| **Tag alvo** | Não | Nome/tipo da tag a validar (ex.: "GA4 - Purchase") |
| **Evento esperado** | Não | Nome do evento GA4/dataLayer (ex.: `add_to_cart`, `purchase`) |
| **Ambiente** | Não | `preview` (GTM Debug) ou `production` |

## Workflow — Choose the right flow

| User intent | Flow |
|---|---|
| "Lista as tags da página" / "Quais tags tem nessa página?" | **Flow 1 — Audit** |
| "Valida se a tag X tá disparando" / "Essa tag funciona?" | **Flow 2 — Validate** |
| "Tem problema na tag X" / "Por que não dispara?" | **Flow 3 — Troubleshoot** |
| "Implementa evento X" / "Adiciona tag Y" | **Flow 4 — Implement** |

---

# Flow 1 — Audit (listar tags e eventos da página)

Goal: descobrir TODAS as tags GTM ativas, o dataLayer atual e os eventos disparados.

## Step 1.1 — Navigate and capture dataLayer

Use the `cursor-ide-browser` MCP:

1. `browser_navigate` para a URL de validação
2. `browser_evaluate` para extrair dados do GTM e dataLayer:

```javascript
() => {
  const gtm = window.google_tag_manager || {};
  const containers = Object.keys(gtm).filter(k => k.startsWith('GTM-'));

  return {
    containers,
    dataLayer: window.dataLayer || [],
    gtag: typeof window.gtag === 'function',
    events: (window.dataLayer || [])
      .filter(d => d.event)
      .map(d => d.event),
  };
}
```

3. Extract container ID(s) and the full dataLayer.

## Step 1.2 — List tag names via tag_manager API

For each container, call:

```javascript
(containerId) => {
  const c = window.google_tag_manager[containerId];
  if (!c || !c.dataLayer) return [];
  const tags = c.dataLayer.get('gtm.tags') || {};
  return Object.keys(tags).map(k => ({
    id: k,
    name: tags[k].name || 'unknown',
    type: tags[k].tagType || 'unknown',
    status: tags[k].status || 'unknown',
  }));
}
```

If this doesn't work (GTM may not expose tag names in production), use **GTM Preview mode** instead (see Flow 2).

## Step 1.3 — Present audit report

```
Auditoria GTM — {url}

Containers GTM ativos:
- GTM-XXXXXX

Eventos no dataLayer ({n}):
- event_name_1 (disparado {n}x)
- event_name_2

Tags detectadas ({n}):
- GA4 - Page View (ga4_event) — active
- Meta Pixel - PageView (html) — active
- ...

Variáveis dataLayer relevantes:
- user_id: "12345"
- page_type: "product"
- ecommerce: { items: [...] }

Problemas potenciais:
- {list any missing standard events, malformed ecommerce objects, etc.}
```

---

# Flow 2 — Validate (verificar disparo de tag)

Goal: confirmar que uma tag específica está disparando corretamente com os dados esperados.

## Step 2.1 — Build the GTM Preview URL

If the user provides a GTM Preview mode URL, use it directly. Otherwise, explain:

```
Para ativar GTM Preview:
1. Acesse https://tagmanager.google.com
2. Abra o container {GTM-XXXXXX}
3. Clique em "Preview" (canto superior direito)
4. Cole a URL de validação e clique em "Connect"
5. Compartilhe o link do Tag Assistant para eu validar
```

Alternative: use [Google Tag Assistant](https://tagassistant.google.com/) to debug live pages.

## Step 2.2 — Capture the event

Open the page in browser MCP and trigger the action (click button, complete checkout step, etc.):

```javascript
() => {
  const before = (window.dataLayer || []).length;
  return { before, timestamp: Date.now() };
}
```

After triggering the action:

```javascript
(beforeIndex) => {
  const events = (window.dataLayer || []).slice(beforeIndex);
  return events;
}
```

## Step 2.3 — Validate payload

Compare the captured event against the expected schema. For GA4 ecommerce events, see [events-ecommerce.md](events-ecommerce.md).

Basic checklist:

- [ ] Event name matches expected (e.g., `add_to_cart`, not `addToCart`)
- [ ] `ecommerce` object is present (for ecommerce events)
- [ ] `items[]` array has required fields (`item_id`, `item_name`, `price`, `quantity`)
- [ ] `currency` is set (ISO code: `BRL`, `USD`)
- [ ] `value` equals `sum(item.price * item.quantity)` (when applicable)
- [ ] `transaction_id` is unique per purchase
- [ ] No `undefined`, `null`, or empty strings in required fields

## Step 2.4 — Report validation result

```
Validação: {tag_name} na página {url}

Status: ✅ OK | ⚠️ Com avisos | ❌ Falhou

Payload capturado:
{json block}

Verificações:
✅ Evento disparou
✅ Schema correto
⚠️ Campo X está vazio (não crítico)
❌ Campo Y esperado mas ausente
```

---

# Flow 3 — Troubleshoot (investigar problema)

See [troubleshooting.md](troubleshooting.md) for the full decision tree.

Quick checks when a tag is not firing:

1. **Container loaded?** `window.google_tag_manager['GTM-XXXXXX']` exists?
2. **dataLayer initialized?** `window.dataLayer` exists and has entries?
3. **Event name correct?** Check capitalization (`add_to_cart` vs `addToCart`)
4. **Trigger condition met?** Run the exact DOM condition in console
5. **Consent mode blocking?** Check `google_tag_data.ics` state
6. **Ad blocker?** Disable and retest
7. **CSP headers?** Check browser console for CSP violations

---

# Flow 4 — Implement (criar/ajustar tag, trigger, evento)

Goal: adicionar ou ajustar dataLayer events no código, ou orientar o usuário a configurar tag/trigger/variable no painel GTM.

## Step 4.1 — Identify where to implement

| Type of change | Where |
|---|---|
| Push event from site to dataLayer | **Code** (VTEX IO, deco.cx, checkout6-custom.js) |
| Create/edit tag, trigger, variable | **GTM Admin** (panel configuration — guide user) |
| Map dataLayer variable in GTM | **GTM Admin** |

## Step 4.2 — dataLayer push pattern

Always initialize dataLayer before pushing:

```html
<script>
window.dataLayer = window.dataLayer || [];
</script>
```

### For ecommerce events, always clear `ecommerce` first

```javascript
window.dataLayer.push({ ecommerce: null });
window.dataLayer.push({
  event: 'add_to_cart',
  ecommerce: {
    currency: 'BRL',
    value: 199.90,
    items: [{
      item_id: 'SKU123',
      item_name: 'Camisa Polo',
      price: 199.90,
      quantity: 1,
      item_brand: 'Brand',
      item_category: 'Roupas',
    }],
  },
});
```

Not clearing `ecommerce` causes data from previous events to persist.

### For custom events

```javascript
window.dataLayer.push({
  event: 'custom_event_name',
  event_category: 'engagement',
  event_label: 'newsletter_signup',
  value: 1,
});
```

## Step 4.3 — VTEX / deco.cx integration

### VTEX IO (React component)

```tsx
import { useEffect } from 'react'

useEffect(() => {
  window.dataLayer = window.dataLayer || []
  window.dataLayer.push({ ecommerce: null })
  window.dataLayer.push({
    event: 'view_item',
    ecommerce: { /* ... */ },
  })
}, [])
```

### VTEX Checkout (`checkout6-custom.js`)

Listen to `orderFormUpdated.vtex`:

```javascript
$(window).on('orderFormUpdated.vtex', function (_, orderForm) {
  window.dataLayer.push({ ecommerce: null });
  window.dataLayer.push({
    event: 'begin_checkout',
    ecommerce: { /* map from orderForm.items */ },
  });
});
```

See the `vtex-checkout` skill for full checkout event hooks.

### deco.cx (island)

Push dataLayer events from an island component on user interaction. Follow the `deco-island` skill patterns. Keep islands minimal — only the event push logic should be client-side.

## Step 4.4 — Guide user to configure GTM panel

If the change requires panel work:

```
Configuração necessária no GTM ({GTM-XXXXXX}):

1. Criar Variable (Data Layer Variable):
   - Nome: dlv - {var_name}
   - Data Layer Variable Name: {path.to.value}

2. Criar Trigger:
   - Tipo: Custom Event
   - Event name: {event_name}
   - Fires on: All Custom Events (ou condição específica)

3. Criar Tag:
   - Tipo: GA4 Event
   - Measurement ID: {{GA4 Measurement ID}}
   - Event Name: {event_name}
   - Event Parameters:
     - currency: {{dlv - ecommerce.currency}}
     - value: {{dlv - ecommerce.value}}
     - items: {{dlv - ecommerce.items}}
   - Trigger: {trigger criado acima}

4. Testar em Preview mode, depois Submit + Publish.
```

## Step 4.5 — Validate after implementation

Always end by running **Flow 2** to confirm the implementation works end-to-end.

---

## Standard GA4 ecommerce events (quick reference)

| Event | When to fire |
|---|---|
| `view_item_list` | User sees product list (PLP, search results) |
| `select_item` | User clicks a product in a list |
| `view_item` | User opens PDP |
| `add_to_cart` | User adds item to cart |
| `remove_from_cart` | User removes item from cart |
| `view_cart` | User opens cart/minicart |
| `begin_checkout` | User starts checkout |
| `add_shipping_info` | User completes shipping step |
| `add_payment_info` | User completes payment step |
| `purchase` | Order placed successfully |

Full payload schemas in [events-ecommerce.md](events-ecommerce.md).

---

## Browser MCP — quick reference

| Tool | Use for |
|---|---|
| `browser_navigate` | Open the validation URL |
| `browser_snapshot` | Get page structure (accessibility tree) |
| `browser_evaluate` | Run JS to inspect `dataLayer`, `window.google_tag_manager` |
| `browser_console_messages` | Capture GTM debug logs, errors |
| `browser_network_requests` | Verify requests to `collect` endpoints (GA4, Meta, etc.) |
| `browser_take_screenshot` | Capture evidence for PR / task comment |

### Useful network filters

| Network pattern | What it tracks |
|---|---|
| `google-analytics.com/g/collect` | GA4 event hits |
| `googletagmanager.com/gtm.js` | GTM container load |
| `facebook.com/tr` | Meta Pixel |
| `bat.bing.com` | Microsoft Ads |
| `analytics.tiktok.com` | TikTok Pixel |

---

## Delivery (integração com runrunit-pr-commit)

When a GTM task is part of a Runrun.it flow, use the `runrunit-pr-commit` skill **Template B** for the comment. Example:

```
Atualização TASK-{id} - GTM {descrição}

O que foi entregue:
- Evento `add_to_cart` agora é disparado no clique do botão de adicionar ao carrinho da vitrine, com schema GA4 correto.
- Ajustado evento `purchase` no checkout para incluir `transaction_id` único.

Links:
- Pull Request (revisão do código): {pr_url}
- Ambiente de validação (workspace): {workspace_url}
- GTM Preview: {tagassistant_url}
- GA4 DebugView: {debugview_url}

Como validar:
1) Acessar o workspace com GTM Preview ativo, adicionar produto ao carrinho e conferir no Tag Assistant o evento `add_to_cart` com `items[]` e `value` corretos.
2) Finalizar uma compra de teste e validar no GA4 DebugView o evento `purchase` com `transaction_id`, `value` e `items` completos.

Evidências (prints):
{url_tag_assistant}
{url_ga4_debugview}
{url_datalayer_console}
```

---

## Important rules

- **Always run Flow 1 (audit) before Flow 3 (troubleshoot) or Flow 4 (implement)** — need to know the current state first.
- **Always clear `ecommerce`** before pushing a new ecommerce event (`{ ecommerce: null }`).
- **Event names are case-sensitive** — use `snake_case` for GA4 standard events.
- **Never commit GTM container IDs as secrets** — they are public (visible in page HTML).
- **Never edit or delete tags in the GTM panel on the user's behalf** — always guide the user step-by-step and ask for confirmation.
- **Always validate after implementation** — run Flow 2 before finishing the task.
- **Ad blockers, CSP, and consent mode** are the top 3 causes of tags not firing — check these first.

## Additional resources

- Full GA4 ecommerce payloads: [events-ecommerce.md](events-ecommerce.md)
- Troubleshooting decision tree: [troubleshooting.md](troubleshooting.md)
