# Seeding content (fill a page so someone can review it)

Read this when a template exists but renders empty, and you need real content in it so a
manager or client can validate the page in a dev workspace. Typical trigger: you just
built a page template and the next step is "add preview content so we can validate it".

The migration pipeline is the wrong tool here — its gates protect client-entered
production data. Seeding touches a dev workspace where nothing is at risk, and usually
means writing a handful of props on 3–6 blocks.

## Why not just use the Site Editor UI

You can, and for one text field it is genuinely faster. But the admin UI is a React app
that resists automation in ways that cost real time:

- Array fields (banner lists, card lists) live in accordions whose form **opens blank
  until you expand the specific item** — expanding item 0 when your content is in item 1
  looks exactly like "the save didn't work", and the natural next move (re-typing
  everything) creates a duplicate empty entry that then renders as a blank slide.
- Image fields are uploaders, not URL inputs. There is no text box to paste a URL into.
- Delete lives behind a kebab menu (`[data-testid="menu-option-1"]`), not a visible button.
- Panels close on save without a persistent confirmation, so "did that work?" needs a
  separate check anyway.

Every one of those is avoidable by writing through the API and confirming through the
rendered runtime. Reach for the UI only when a field has no API equivalent, or when the
user explicitly wants to see the admin flow.

## The loop

### 1. Read what is actually saved

The fastest ground truth is the rendered page itself. Every VTEX IO page embeds its
resolved extension map, so in a browser console on the workspace URL:

```js
window.__RUNTIME__.extensions['<treePath>'].content   // saved content, merged over code defaults
window.__RUNTIME__.extensions['<treePath>'].blockId   // exactly what saveContent wants
```

This gives you the treePath, the blockId **in the form the API expects**, and the current
values — all three of the things a write needs. It is also how you confirm the write later.

To list every editable path on a page:

```js
Object.keys(window.__RUNTIME__.extensions).filter(k => k.startsWith('store.custom#my-page'))
```

`listContentWithSchema` also works (see `pages-graphql-api.md`) and is the right call in a
headless context, but it returns only code defaults if the `template` argument is wrong —
see the trap in SKILL.md before trusting an empty result.

### 2. Write

Use `scripts/seed_content.py`, which does read-modify-write on a single treePath so you
only supply the props you want to change.

Put those props in a file. A JSON file reaches the script byte-for-byte in every shell,
while an inline `--set-json` loses its double quotes in PowerShell 5.1:

`patch.json`

```json
{"querySchema": {"queryField": "155", "mapField": "productClusterIds"}}
```

Then one command, on one line — line continuations differ per shell, so the docs avoid
them:

```
python3 scripts/seed_content.py --workspace <ws> --template 'vendor.app@11.x:store.custom#specialpagev3' --tree-path 'store.custom#specialpagev3/search-result-layout.customQuery#specialv3' --block-id 'vendor.app@11.x:search-result-layout.customQuery#specialv3' --set-json-file patch.json --template-wide
```

`--set-json '{"…"}'` still works and is fine in bash, zsh and Git Bash.

**Scope is required — there is no default.** Pick one:

- **`store.custom#…` route** → route scope, and it needs the bindingId:
  `--page-context-id 'store.custom#my-page' --page-context-type route --binding-id <id>`.
  Read both off the live page: `__RUNTIME__.route.pageContext` and `__RUNTIME__.binding.id`.
- **One page of a many-page template** → `--page-context-id 104 --page-context-type
  subcategory`, from that page's `"route":{…"pageContext":{"id":"…","type":"…"}}`.
- **Every page of a many-page template** → `--template-wide` (`pageContext {*,*}`).

`--template-wide` on a `store.custom#…` route is a trap, so the script refuses it: the
entry lands **sitewide**, the renderer never reads it, and `saveContent` still returns a
contentId. Verified on a real store — a first seed went sitewide and looked successful.

Getting this wrong is not loud. A wildcard write lands on every page of the template, and
the save still returns a contentId either way.

Dry run by default; add `--apply`. It refuses a bare (unprefixed) template and a prefixed
treePath, because both fail silently rather than erroring.

The script prints which entry it merged over — `page-scoped entry`, `template-wide
entry`, or `block default — nothing saved here yet`. Read that line before applying: it
tells you whether you are about to extend a client's saved content or start from code
defaults.

### 3. Verify on the rendered page, not the response

A save response proves the write was accepted, not that the renderer sees it. Reload the
workspace URL and re-read `__RUNTIME__.extensions[treePath].content`. Saves land in ~30s
with no relink.

## Choosing content that actually validates the page

Preview content exists so someone can judge the layout. Placeholder text and grey boxes
defeat that, so prefer real data from the account:

- **Product queries** — find a collection that returns a healthy count rather than
  copying an id from a sibling store (`/api/catalog_system/pvt/collection/search`, then
  confirm it actually returns products via
  `/api/catalog_system/pub/products/search?fq=productClusterIds:<id>`). An id borrowed
  from another store usually returns nothing and reads as a broken page.
- **Links** — resolve every path against
  `/api/catalog_system/pub/portal/pagetype/<slug>`. A slug that returns `FullText` is a
  search fallback, not a real page; the site will render it without a 404, so a broken
  link looks fine until someone clicks it.
- **Images** — reuse assets already in the account's file manager where you can. If you
  must upload through an image widget, build the `File` from a fetched blob and **name it
  with the extension that matches the blob's real MIME type** — VTEX CDNs often serve
  `.png` URLs as `image/webp`, and a mismatched name is rejected with a generic
  "Something went wrong".

## Responsive image slots are a recurring trap

Several agency carousel blocks expose separate desktop / mobile / tablet image fields.
Filling only the desktop slot renders a **blank strip on phones** — the component picks
the empty variant rather than falling back. Some VTEX-native blocks (`vtex.carousel`) do
fall back, which is why this is easy to miss when comparing two blocks on the same page.

After seeding any image content, check the small breakpoint before calling it done. The
cheap detector is counting images with no `src` or `naturalWidth === 0`:

```js
[...document.querySelectorAll('img')]
  .filter(i => !i.getAttribute('src') || (i.complete && i.naturalWidth === 0)).length
```

## Before you destructively test

Clearing blocks to see an empty state is a normal thing to want. Capture the current
content first — reading
`__RUNTIME__.extensions[tp].content` for each affected treePath gives you a restore
payload verbatim, which beats retyping alt text and URLs from memory afterwards.

Toggling a mode prop (for example a carousel's type to "none") usually hides content
without deleting it, so it is a gentler way to blank a block than emptying its array.
