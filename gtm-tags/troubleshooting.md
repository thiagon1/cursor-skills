# GTM Troubleshooting — Decision Tree

Systematic approach to diagnose GTM / dataLayer / tag firing issues.

## Problem: "A tag não dispara"

Work through these checks in order. Stop when you find the cause.

### 1. Container GTM carregou?

```javascript
() => ({
  hasGtm: typeof window.google_tag_manager !== 'undefined',
  containers: Object.keys(window.google_tag_manager || {})
    .filter(k => k.startsWith('GTM-')),
  dataLayerSize: (window.dataLayer || []).length,
})
```

- **No container / empty dataLayer?** → Script GTM não foi injetado. Verifique:
  - Snippet GTM está no `<head>` e `<body>` (noscript fallback)
  - CSP headers bloqueando `googletagmanager.com`? Veja console.
  - Ad blocker ativo? Teste em aba anônima ou desabilite uBlock/Ghostery.
  - Consent Mode bloqueando? Veja check 5.

### 2. Evento chegou no dataLayer?

```javascript
() => (window.dataLayer || [])
  .filter(d => d.event)
  .map(d => ({ event: d.event, keys: Object.keys(d) }))
```

- **Evento não está no dataLayer?** → O push nunca aconteceu. Verifique:
  - O código de push está sendo executado? Coloque `console.log` antes do push.
  - Timing: o push acontece antes do GTM carregar? Eventos muito cedo são perdidos se GTM ainda não estiver pronto. Para eventos iniciais, use `gtm.dom` ou `gtm.load` como trigger.
  - Nome do evento tem typo? `add_to_cart` ≠ `addToCart` ≠ `AddToCart`.

### 3. Trigger do GTM está configurado corretamente?

Abra GTM Preview e inspecione:

- **Tag aparece em "Tags Not Fired"?** → Trigger não bateu. Clique para ver qual condição falhou.
- **Custom Event name confere?** Case-sensitive.
- **Filtros adicionais (ex.: Page Path, URL contains)?** Valide um a um.
- **Exception trigger?** Alguma trigger de exceção está bloqueando?

### 4. Variáveis mapeadas corretamente?

Em GTM Preview, selecione a tag → aba **Variables**:

- Todas as variáveis têm valor?
- `{{ecommerce.items}}` está vazio ou `undefined`?
- Data Layer Variable com path correto? (ex.: `ecommerce.items.0.item_id` vs `ecommerce.items`)

### 5. Consent Mode / Privacy tools

```javascript
() => ({
  consent: window.google_tag_data?.ics?.getAllGroups?.() || 'no consent mode',
  cookiebot: typeof window.Cookiebot !== 'undefined',
  oneTrust: typeof window.OneTrust !== 'undefined',
})
```

- **`ad_storage: denied` ou `analytics_storage: denied`?** → Consent Mode bloqueando. Aceite cookies e retestee.
- Verifique se a plataforma de consentimento (Cookiebot, OneTrust, LGPD banner) está funcionando corretamente.

### 6. Tag está pausada / publicada?

- GTM Admin → versão publicada atual contém a tag?
- Tag não está com status "Paused"?
- Publicou depois da última alteração? (Muda em Preview mas não em Production.)

### 7. Ad blockers / network

No DevTools → Network → filtre por:
- `collect` (GA4): retornou 204? Ou bloqueado (ERR_BLOCKED_BY_CLIENT)?
- `gtm.js`: status 200?
- `gtag/js`: status 200?

Se bloqueado por ad blocker, o problema é do ambiente do testador, não do código.

### 8. SPA / route change (Single Page Application)

Em SPAs (React, Vue), o `pageview` padrão só dispara no load inicial.

Para tracking de mudanças de rota, faça push manual:

```javascript
// No router.afterEach / useEffect de route change
window.dataLayer.push({
  event: 'page_view',
  page_path: newPath,
  page_title: document.title,
});
```

E configure no GTM uma tag GA4 Event com trigger em `Custom Event: page_view`.

---

## Problem: "Evento dispara duas vezes"

1. **DOM event bound multiple times?** Cada navegação em SPA adiciona mais um listener? Use `{ once: true }` ou clean up no unmount.
2. **GTM tag tem mais de um trigger?** Ex.: trigger específico + All Pages.
3. **gtag global + GTM container?** Se ambos estão instalados, eventos podem duplicar. Use apenas um.
4. **React Strict Mode?** Em dev, `useEffect` roda 2x. Testar em build de produção.

---

## Problem: "Items / ecommerce vem vazio no GA4"

1. **`ecommerce: null` foi esquecido** antes do push? → Valores do evento anterior ficaram em cache.
2. **`items` é objeto em vez de array**?
3. **Data Layer Variable não usa "Version 2"?** Use Version 2 para acessar arrays corretamente.
4. **Campo incorreto**: GA4 espera `items`, não `products` (esse era o Universal Analytics).
5. **GA4 Enhanced Ecommerce desabilitado** na configuração da tag?

---

## Problem: "Purchase duplica / não dispara"

- **Transaction ID duplicado?** GA4 deduplica `purchase` pelo `transaction_id` em ~24h. Use um ID único real (não de teste).
- **Thank-you page recarregada** dispara purchase de novo? Use flag em `sessionStorage`:
  ```javascript
  const key = `purchase_${orderId}`;
  if (!sessionStorage.getItem(key)) {
    window.dataLayer.push({ event: 'purchase', ... });
    sessionStorage.setItem(key, '1');
  }
  ```
- **Server-side checkout (one-page)**: o evento precisa disparar APÓS confirmação real do pedido, não antes.

---

## Problem: "Consent mode / LGPD quebrou tracking"

1. Verifique categorias: `analytics_storage`, `ad_storage`, `ad_user_data`, `ad_personalization`, `functionality_storage`, `personalization_storage`, `security_storage`.
2. Com Consent Mode v2, GA4 envia "cookieless pings" mesmo sem consent, mas ecommerce completo só vem com `analytics_storage: granted`.
3. No GTM, tags podem ter "Consent Settings" → verifique se "Require additional consent" está configurado corretamente.

---

## Problem: "Preview mode não conecta"

1. Desabilite ad blocker para `tagassistant.google.com` e o domínio testado.
2. Third-party cookies precisam estar habilitados.
3. HTTPS mismatch: GTM Preview com HTTPS e site com HTTP não conecta.
4. iframe / X-Frame-Options: se a página está dentro de iframe com CSP restrita, Preview pode não injetar o debug.
5. Use `?gtm_auth=...&gtm_preview=env-N&gtm_cookies_win=x` na URL como fallback (valores vêm do GTM Admin → Environments).

---

## Útil para diagnóstico rápido

### Inspecionar todo o dataLayer

```javascript
() => JSON.stringify(window.dataLayer, null, 2)
```

### Listar eventos únicos já disparados

```javascript
() => [...new Set((window.dataLayer || [])
  .filter(d => d.event)
  .map(d => d.event))]
```

### Escutar novos pushes em tempo real

```javascript
(() => {
  const original = window.dataLayer.push;
  window.dataLayer.push = function(...args) {
    console.log('[dataLayer push]', args);
    return original.apply(this, args);
  };
  return 'hooked';
})()
```

### Ver todas as tags executadas pelo GTM

```javascript
(containerId) => {
  const gtm = window.google_tag_manager?.[containerId];
  if (!gtm) return 'Container not found';
  const tags = gtm.dataLayer.get('gtm.tags') || {};
  return Object.entries(tags).map(([id, t]) => ({
    id,
    name: t.name,
    status: t.status,
    type: t.tagType,
  }));
}
```
