# omie-seed — exemplos

## Skeleton: `cms/scripts/seed-<nome>.js`

Copiar e preencher. Helpers completos em [reference.md](reference.md).

```js
/**
 * Local-only seed: creates/updates Pages in Strapi.
 * Usage (cms/): node scripts/seed-<nome>.js
 * Reads STRAPI_API_URL + STRAPI_API_TOKEN from ../front/.env.local or env.
 */
const fs = require('fs');
const path = require('path');
const { Blob } = require('buffer');

const ROOT = path.resolve(__dirname, '../..');
const FRONT_PUBLIC = path.join(ROOT, 'front', 'public');
const ENV_PATH = path.join(ROOT, 'front', '.env.local');

function loadEnv() {
  const env = { ...process.env };
  if (fs.existsSync(ENV_PATH)) {
    for (const line of fs.readFileSync(ENV_PATH, 'utf8').split(/\r?\n/)) {
      const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.+?)\s*$/);
      if (!m) continue;
      let v = m[2].replace(/\s+#.*$/, '').trim();
      if (
        (v.startsWith('"') && v.endsWith('"')) ||
        (v.startsWith("'") && v.endsWith("'"))
      ) {
        v = v.slice(1, -1);
      }
      env[m[1]] = v;
    }
  }
  return env;
}

const env = loadEnv();
const API = (env.STRAPI_API_URL || 'http://localhost:1337').replace(/\/$/, '');
const TOKEN = env.STRAPI_API_TOKEN;
if (!TOKEN) {
  console.error('Missing STRAPI_API_TOKEN');
  process.exit(1);
}

const headersJson = {
  Authorization: `Bearer ${TOKEN}`,
  'Content-Type': 'application/json',
};

async function api(method, urlPath, body) {
  const res = await fetch(`${API}${urlPath}`, {
    method,
    headers: body ? headersJson : { Authorization: `Bearer ${TOKEN}` },
    body: body ? JSON.stringify(body) : undefined,
  });
  const text = await res.text();
  let json;
  try {
    json = text ? JSON.parse(text) : null;
  } catch {
    json = { raw: text };
  }
  if (!res.ok) {
    const err = new Error(`${method} ${urlPath} -> ${res.status}`);
    err.details = json;
    throw err;
  }
  return json;
}

const mediaCache = new Map();

async function uploadFile(relativePublicPath) {
  const abs = path.join(FRONT_PUBLIC, relativePublicPath.replace(/^\//, ''));
  if (!fs.existsSync(abs)) throw new Error(`File not found: ${abs}`);
  if (mediaCache.has(abs)) return mediaCache.get(abs);

  const buf = fs.readFileSync(abs);
  const fileName = path.basename(abs);
  const form = new FormData();
  const mime = fileName.endsWith('.webp')
    ? 'image/webp'
    : fileName.endsWith('.svg')
      ? 'image/svg+xml'
      : 'image/png';
  form.append('files', new Blob([buf], { type: mime }), fileName);

  const res = await fetch(`${API}/api/upload`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${TOKEN}` },
    body: form,
  });
  const json = await res.json();
  if (!res.ok) {
    const err = new Error(`upload ${relativePublicPath} -> ${res.status}`);
    err.details = json;
    throw err;
  }
  const id = Array.isArray(json) ? json[0]?.id : json?.id;
  if (!id) throw new Error(`upload returned no id for ${relativePublicPath}`);
  mediaCache.set(abs, id);
  console.log('uploaded', relativePublicPath, '->', id);
  return id;
}

function cta(label, link, variant = 'primary-green') {
  return {
    label,
    actionType: 'link',
    link,
    openInNewTab: false,
    variant,
  };
}

function pageChromeLp() {
  return {
    hideHeader: true,
    hideHeaderNavigation: true,
    hideFooter: true,
    showTopBar: false,
  };
}

async function findPage(slug, pathPrefix) {
  const params = new URLSearchParams();
  params.set('filters[slug][$eq]', slug);
  params.set('publicationState', 'preview');
  params.set('pagination[pageSize]', '1');
  if (pathPrefix) {
    params.set('filters[pathPrefix][$eq]', pathPrefix);
  } else {
    params.set('filters[pathPrefix][$null]', 'true');
  }
  const json = await api('GET', `/api/pages?${params}`);
  return json?.data?.[0] || null;
}

async function upsertPage(payload) {
  const existing = await findPage(payload.slug, payload.pathPrefix || null);
  if (existing?.documentId) {
    console.log('updating', payload.slug, existing.documentId);
    await api('PUT', `/api/pages/${existing.documentId}`, { data: payload });
    await api('POST', `/api/pages/${existing.documentId}/actions/publish`).catch(
      async () => {
        await api('PUT', `/api/pages/${existing.documentId}`, {
          data: { ...payload, publishedAt: new Date().toISOString() },
        });
      },
    );
    return existing.documentId;
  }
  console.log('creating', payload.slug, payload.pathPrefix || '(root)');
  const created = await api('POST', '/api/pages', { data: payload });
  const documentId = created?.data?.documentId;
  if (documentId) {
    await api('POST', `/api/pages/${documentId}/actions/publish`).catch(
      async () => {
        await api('PUT', `/api/pages/${documentId}`, {
          data: { ...payload, publishedAt: new Date().toISOString() },
        });
      },
    );
  }
  return documentId;
}

async function buildLanding(media) {
  return {
    title: 'Minha LP',
    slug: 'minha-lp',
    pathPrefix: null,
    seo: {
      metaTitle: 'Minha LP | Omie',
      metaDescription: 'Descrição curta',
      canonicalUrl: 'https://www.omie.com.br/minha-lp/',
      noindex: false,
    },
    pageChrome: pageChromeLp(),
    sections: [
      {
        __component: 'sections.webinar-lp-nav',
        visible: true,
        logo: media.logoWhite,
        logoLink: '/',
        cta: cta('Inscreva-se agora', '#banner'),
        backgroundColor: '#001e27',
      },
      // ... demais seções mapeadas do schema
    ],
  };
}

async function main() {
  console.log('Seeding pages into', API);

  const media = {
    logoWhite: await uploadFile('assets/images/logo-omie.png'),
    // ...
  };

  const pages = [await buildLanding(media)];

  for (const page of pages) {
    try {
      const id = await upsertPage(page);
      console.log('OK', page.slug, page.pathPrefix || '', '->', id);
    } catch (e) {
      console.error('FAIL', page.slug, e.message);
      console.error(JSON.stringify(e.details, null, 2));
      process.exitCode = 1;
    }
  }
}

main().catch((e) => {
  console.error(e);
  if (e.details) console.error(JSON.stringify(e.details, null, 2));
  process.exit(1);
});
```

## Exemplo real: webinar pages

Referência histórica do monorepo omie: `cms/scripts/seed-webinar-pages.js` (TASK-14816).

Padrão usado:

1. **4 pages** — TikTok landing + thank-you, Soluções Financeiras landing + thank-you
2. **Upload batch** no `main()` → objeto `media` com ids
3. **Builders** `buildTikTokLanding(media)`, `buildSolucoesLanding(media)`, …
4. **Slug único** no thank-you de Soluções (`omie-solucoes-financeiras-agradecimento`) porque `agradecimento` já existia
5. **Re-seed** após ajustar layout/conteúdo (upsert sobrescreve sections)

Trecho de seção com mídia + CTA:

```js
{
  __component: 'sections.webinar-hero-speakers',
  visible: true,
  variant: 'landing',
  badgeImage: media.tiktokLogo,
  title: 'EP.2 TikTok Shop na prática:',
  titleHighlight: 'EP.2',
  subtitle: 'Como transformar visualizações em vendas',
  eventDateLabel: '14/7',
  eventTimeLabel: '10H',
  dateIcon: media.calendarIcon,
  timeIcon: media.clockIcon,
  cta: cta('Inscreva-se', '#banner'),
  speakers: [
    {
      name: 'Natanael',
      role: 'Especialista TikTok Shop',
      bio: '...',
      image: media.natanael,
    },
  ],
  backgroundColor: '#ffffff',
},
```

Form HubSpot (quando o schema tiver `integration`):

```js
integration: {
  provider: 'hubspot',
  hubspotPortalId: '50669433',
  hubspotFormId: '9d18bfe9-a9b3-4951-a73d-a9d66a968213',
},
postSubmitRedirectUrl: '/omie-tiktok/agradecimento/',
```

## Patch pontual (sem re-seed completo)

Para ajustar 1 campo sem reescrever a Page inteira, script `_tmp-*.js` que:

1. `GET` page com populate mínimo necessário
2. Mutar `sections` em memória
3. `PUT` + publish

Apagar o `_tmp-` ao terminar. Preferir re-seed completo quando o conteúdo for grande.

## Como rodar (PowerShell)

```powershell
$env:NODE_OPTIONS = "--use-system-ca"
cd C:\Users\usuario\Documents\projetos\omie\cms
node scripts/seed-minha-lp.js
```

Saída esperada:

```
Seeding pages into http://localhost:1337
uploaded assets/images/logo-omie.png -> 42
creating minha-lp (root)
OK minha-lp  -> abcDocumentId
```
