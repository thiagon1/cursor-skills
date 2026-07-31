---
name: omie-seed
description: >-
  Creates local-only Strapi seed scripts for the OMIE CMS (Next.js + Strapi)
  that upsert Pages with page-builder sections and Media Library uploads.
  Use when the user asks for a seed script, popular CMS, seed pages, seed
  Strapi, preencher dados no CMS, ou recriar conteúdo de LP no localhost.
---

# OMIE — seed de conteúdo no CMS (Strapi)

Cria scripts Node em `cms/scripts/` que **preenchem/atualizam** conteúdo no Strapi local via REST (Pages + Dynamic Zone + upload de mídia), no padrão do seed de webinars.

**Escopo:** local/dev. Não rodar contra produção sem confirmação explícita.

## Quando usar

- "criar seed", "seed no Strapi", "popular o CMS", "preencher páginas no CMS"
- Recriar LP migrada (HTML/estática → page builder) com textos/imagens
- Re-seed após mudar schema de seção ou restaurar mídias/speakers

## Pré-requisitos

1. CMS rodando (`cd cms && npm run develop`) — Admin em `http://localhost:1337`
2. `front/.env.local` com:
   - `STRAPI_API_URL=http://localhost:1337` (strip comentário inline `# ...`)
   - `STRAPI_API_TOKEN` com permissão de create/update/publish em **Page** + **Upload**
3. Front com assets em `front/public/` (paths usados no upload)
4. Seções já existem no schema (`cms/src/components/sections/<uid>.json`) e estão no Dynamic Zone de Page (`cms/section-components.json` + sync se necessário)

Se faltar token/URL: **parar** e pedir ao usuário.

## Workflow (obrigatório)

```
Task Progress:
- [ ] 1. Confirmar CMS up + .env.local
- [ ] 2. Mapear schema das seções (campos reais)
- [ ] 3. Coletar copy + assets (prod/HTML/Figma)
- [ ] 4. Pedir OK para criar cms/scripts/seed-<nome>.js
- [ ] 5. Implementar helpers + builders + main
- [ ] 6. Rodar seed e corrigir erros de API
- [ ] 7. Validar Pages no Admin e URLs no front
```

### 1) Confirmar ambiente

```powershell
# health
try { (Invoke-WebRequest -Uri "http://localhost:1337/_health" -UseBasicParsing -TimeoutSec 5).StatusCode } catch { "DOWN" }
```

Ler `front/.env.local`. Em Windows, preferir `NODE_OPTIONS=--use-system-ca` se houver erro de CA.

### 2) Mapear schema → payload

Para cada `__component: 'sections.<uid>'`:

1. Ler `cms/src/components/sections/<uid>.json`
2. Ler nested `cms/src/components/shared/*.json` quando houver
3. Montar payload **só com campos do schema** (`visible`, mídias como **id numérico**, CTAs no shape do componente shared)
4. Cores: hex string (campos color-picker)

Fonte de verdade = JSON do CMS, não o transformer do front.

### 3) Coletar conteúdo

- Textos: produção, HTML legado (`front/public/...`), seed anterior, ou copy do usuário
- Imagens: paths relativos a `front/public/` (ex.: `assets/images/...`)
- Forms HubSpot: `portalId` / `formId` se a seção tiver `integration`

### 4) Criar o arquivo (pedir OK)

Padrão:

```
cms/scripts/seed-<nome-kebab>.js
```

Exemplos: `seed-webinar-pages.js`, `seed-lp-xyz.js`.

Antes de escrever: *"Vou criar `cms/scripts/seed-<nome>.js`. OK?"*

Não commitar tokens. Scripts temporários de debug: prefixo `_tmp-` e apagar ao terminar.

### 5) Implementar

Estrutura fixa do script:

1. Header + `loadEnv()` (lê `front/.env.local`, remove `# comentário` inline)
2. `api(method, path, body)` — Bearer + JSON; erro com `details`
3. `uploadFile(relativePublicPath)` — `POST /api/upload` com `FormData` + cache `Map`
4. Helpers de domínio (`cta()`, `pageChromeLp()`, etc.)
5. `findPage(slug, pathPrefix)` + `upsertPage(payload)` (PUT se existe, POST se não; publish)
6. `buildX(media)` por página — retorna payload completo da Page
7. `main()` — upload mídias → builders → loop upsert

Detalhes e snippets: [reference.md](reference.md).  
Skeleton completo: [examples.md](examples.md).

### 6) Rodar

```powershell
$env:NODE_OPTIONS = "--use-system-ca"
cd cms
node scripts/seed-<nome>.js
```

Em falha `4xx/5xx`: logar `e.details`, ajustar campo/UID/relação, re-rodar (upsert é idempotente por slug+pathPrefix).

### 7) Validar

- Admin → Content Manager → Page → seções + mídias
- Front: `http://localhost:3000/{slug}/` ou `/{pathPrefix}/{slug}/`
- Confirmar publish (draft não aparece no front sem preview)

## Regras OMIE / Strapi

| Regra | Detalhe |
|---|---|
| `slug` é UID **global** | Dois thank-yous não podem ambos ser `agradecimento`. Usar slug único (ex.: `omie-solucoes-financeiras-agradecimento`) |
| URL | `pathPrefix` vazio → `/{slug}`; preenchido → `/{pathPrefix}/{slug}` |
| Mídia | Sempre **id** do upload (`number`), nunca URL solta no relation |
| Dynamic Zone | Cada bloco: `__component: 'sections.<uid>'` + `visible: true` |
| Local only | Default `localhost:1337`. Produção só com OK explícito |
| Não misturar populate | Seed usa REST write; populate do front é outro fluxo |
| Editar `cms/` | Reinicia Strapi — esperar health antes de re-seed |

## Page payload (mínimo)

```js
{
  title: string,
  slug: string,              // único global
  pathPrefix: string | null, // null = raiz
  seo: { metaTitle, metaDescription, canonicalUrl, noindex },
  pageChrome: { hideHeader, hideHeaderNavigation, hideFooter, showTopBar },
  sections: [ { __component, visible, ...fields } ],
}
```

Mídias no payload: `logo: media.logoWhite` onde `media.logoWhite` é o **id** retornado por `uploadFile`.

## Checklist antes de concluir

- [ ] Script em `cms/scripts/seed-*.js` (não em `front/`)
- [ ] Env lido de `front/.env.local` com strip de comentário
- [ ] Upload com cache; paths existem em `front/public`
- [ ] Campos batem com schema JSON das seções
- [ ] Upsert por `slug` + `pathPrefix` + publish
- [ ] Slugs únicos (thank-you / páginas irmãs)
- [ ] Seed rodou sem `Invalid key` / 400
- [ ] Página renderiza no Next com mídias

## Permissões

| Ação | Pedir OK? |
|---|---|
| Criar `cms/scripts/seed-*.js` | Sim |
| Rodar seed em localhost | Não (após criar) |
| Apontar seed para API não-local | **Sempre** |
| Deletar Pages no CMS | **Sempre** |
| Commitar o seed | Só se o usuário pedir |

## Recursos

- [reference.md](reference.md) — helpers, endpoints, armadilhas
- [examples.md](examples.md) — skeleton + trechos do seed de webinar
- Docs do monorepo omie: `docs/DEV-ONBOARDING-SECTIONS.md`, `docs/INTEGRATION-PATTERNS.md`
