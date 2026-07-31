# omie-seed — referência

## Endpoints Strapi 5 (REST)

| Ação | Método | Path |
|---|---|---|
| Listar pages | `GET` | `/api/pages?filters[slug][$eq]=...&publicationState=preview` |
| Criar | `POST` | `/api/pages` body `{ data: payload }` |
| Atualizar | `PUT` | `/api/pages/:documentId` body `{ data: payload }` |
| Publish | `POST` | `/api/pages/:documentId/actions/publish` |
| Upload | `POST` | `/api/upload` multipart field `files` |

Auth: `Authorization: Bearer ${STRAPI_API_TOKEN}`.

Strapi 5 usa `documentId` (string) nas rotas de update/publish — não usar só o `id` numérico antigo.

## loadEnv

Ler `front/.env.local` **e** `process.env`. Crítico: remover comentário inline após o valor.

```js
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '../..');
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
```

## api()

```js
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
```

## uploadFile()

- Path relativo a `front/public/`
- `FormData` + `Blob` (Node 18+)
- **Não** setar `Content-Type` manual no fetch (boundary do multipart)
- Cache por path absoluto para não reenviar a mesma imagem

```js
const { Blob } = require('buffer');
const FRONT_PUBLIC = path.join(ROOT, 'front', 'public');
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
      : fileName.endsWith('.jpg') || fileName.endsWith('.jpeg')
        ? 'image/jpeg'
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
```

No payload da seção, mídia = **id**:

```js
logo: media.logoWhite, // number
speakers: [{ name: '...', image: media.speaker1 }],
```

## findPage + upsertPage

Filtrar por `slug` **e** `pathPrefix` (`$null` quando raiz). Usar `publicationState=preview` para achar draft.

```js
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
```

## Helpers úteis

```js
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
```

Ajustar `cta` / `pageChrome` ao schema real em `cms/src/components/shared/` e atributos de Page.

## Mapear seção a partir do schema

Exemplo mental para `webinar-lp-nav.json`:

```json
{
  "attributes": {
    "visible": { "type": "boolean" },
    "logo": { "type": "media" },
    "logoLink": { "type": "string" },
    "cta": { "type": "component", "component": "shared...." },
    "backgroundColor": { "type": "string", "customField": "plugin::color-picker.color" }
  }
}
```

→ payload:

```js
{
  __component: 'sections.webinar-lp-nav',
  visible: true,
  logo: media.logoWhite,
  logoLink: '/',
  cta: cta('Inscreva-se agora', '#banner'),
  backgroundColor: '#001e27',
}
```

Repetidores = arrays de objetos; mídia aninhada = id em cada item.

## Armadilhas

| Problema | Causa / fix |
|---|---|
| `Missing STRAPI_API_TOKEN` | `.env.local` ausente ou chave errada |
| URL com `# ou sua URL` | Comentário inline — `loadEnv` deve strippar |
| `slug must be unique` | UID global — mudar slug da página irmã |
| `Invalid key ...` | Campo inexistente no schema / typo no `__component` |
| Mídia vazia no front | Passou URL string em vez de id; ou upload falhou |
| Page draft | Publish falhou — fallback `publishedAt` no PUT |
| SSL / CA no Windows | `$env:NODE_OPTIONS='--use-system-ca'` |
| Seed após editar schema | Esperar Strapi reiniciar (`_health`) |
| Token sem Upload | Admin → Settings → API Tokens → permissões Upload + Page |

## Outros content types

O padrão serve para qualquer collection com REST semelhante (`/api/<plural>`). Para Single Types: `GET/PUT /api/<singular>` (sem lista por slug). Adaptar `find`/`upsert`; manter `loadEnv` + `uploadFile` + builders.

## Segurança

- Não logar o token completo
- Não apontar `API` para produção sem OK do usuário
- Preferir token com escopo mínimo (Page + Upload)
