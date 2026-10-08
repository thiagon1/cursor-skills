# pages-graphql API contract (Site Editor content)

Verified against `vtex.pages-graphql@2.x` / `vtex.admin-pages@4.59.2` (2026-07). If calls
behave oddly, re-derive the contract — see the last section.

## Endpoint & auth

```
POST https://{account}.myvtex.com/_v/private/graphql/v1
  ?workspace={ws}&maxAge=short&appsEtag=remove&domain=admin&locale=en-US
  &extensions={"persistedQuery":{"provider":"vtex.pages-graphql@2.x","sender":"vtex.admin-pages@4.59.2"}}
```

- `extensions` is URL-encoded JSON in the query string; the POST body is plain
  `{"query": "...", "variables": {...}}`.
- Auth: cookie `VtexIdclientAutCookie=<token>` where token comes from `vtex local token`
  (valid ~24h). Works from plain `curl`/python — no browser session needed.
- `workspace` selects the content partition. `master` = production content.
- Responses may be gzip'd — send `Accept-Encoding: gzip` and decompress.

## Operations

### ListContent (read)

```graphql
query ListContent($bindingId: String, $blockId: String, $pageContext: PageContextInput,
                  $template: String, $treePath: String)
  @context(sender: "vtex.admin-pages@4.59.2") {
  listContentWithSchema(bindingId: $bindingId, blockId: $blockId,
                        pageContext: $pageContext, template: $template, treePath: $treePath) {
    content { contentId contentJSON label origin
              condition { allMatches id pageContext { id type } statements { objectJSON subject verb } } }
    schemaJSON
  }
}
```

Variables that actually work (all five matter):

```json
{
  "bindingId":  "4d17936a-…",
  "blockId":    "vendor.app@11.x:rich-text#seo-title",
  "template":   "vendor.app@11.x:store.search#subcategory",
  "treePath":   "store.search#subcategory/flex-layout.row#seo-text/…/rich-text#seo-title",
  "pageContext": { "id": "104", "type": "subcategory" }
}
```

Returns the block-default entry (empty `contentId`, pageContext `{*,*}`) plus any saved
entries whose condition matches the given pageContext. Query with a concrete pageContext
to see that page's entry AND the template-wide entry together. `pageContext` is required
in practice (omitting it → internal server error).

### saveContent (write)

```graphql
mutation saveContent($bindingId: String, $blockId: String,
                     $configuration: ContentConfigurationInput,
                     $template: String, $treePath: String, $lang: String)
  @context(sender: "vtex.admin-pages@4.59.2") {
  saveContent(bindingId: $bindingId, blockId: $blockId, configuration: $configuration,
              template: $template, treePath: $treePath, lang: $lang) { contentId }
}
```

`configuration`:

```json
{
  "status": "ACTIVE",
  "condition": { "allMatches": true, "id": "",
                 "pageContext": { "id": "104", "type": "subcategory" }, "statements": [] },
  "contentId": null,
  "contentJSON": "{\"text\":\"…\"}",
  "label": null,
  "origin": null
}
```

- `status` is the enum `ACTIVE` / `INACTIVE` — lowercase is rejected with a clear error.
- `contentId: null` creates; passing an existing full contentId updates that entry.
- `contentJSON` is a **string** of JSON — the saved delta only, not full block props.
- `lang` = locale, e.g. `en-US`.

### DeleteContent

```graphql
mutation DeleteContent($template: String, $treePath: String,
                       $pageContext: PageContextInput, $contentId: String)
  @context(sender: "vtex.admin-pages@4.59.2") {
  deleteContent(template: $template, treePath: $treePath,
                pageContext: $pageContext, contentId: $contentId)
}
```

`pageContext` must match the entry's own condition. The mutation echoes the contentId
whether or not anything was deleted (truncated id, wrong context, sitewide entry → still
"success"). Always confirm with a follow-up ListContent.

### routes (list every page, including admin-created ones)

```graphql
query Routes @context(provider: "vtex.pages-graphql@2.x", sender: "vtex.admin-pages@4.59.2") {
  routes(domain: "store") {
    routeId path blockId declarer context domain interfaceId title uuid auth
  }
}
```

- `@context(provider: …)` is mandatory whenever the account has two `vtex.pages-graphql`
  majors installed: without it the call is HTTP 500, `Multiple app dependencies have
  defined "routes"`.
- `domain` picks the route set — `"store"` for storefront pages, `"admin"` for admin
  pages. Omitting it returns an empty list.
- `blockId` is the app-prefixed template the page renders
  (`vendor.theme@12.x:store.custom#my-template`). Group by it to get every page built on
  one template — the answer to "which pages use this template", which no theme file holds.
- `declarer` is `null` for a page created in the admin, and the app id for a route
  declared in the theme's `store/routes.json`.

Introspection is blocked (`__type` → `GraphQL validation failed`) and a validation error
never names the offending field, so an unverified subfield set can only be narrowed by
bisection. The fields above are verified; `pages { … }` subfields are not.

## Silent-failure traps (ranked by damage)

1. **Bare `template`** (no `vendor.app@MAJOR.x:` prefix): save "succeeds", ListContent
   with the same bare template echoes your writes back — a perfectly consistent parallel
   universe the renderer never reads. Symptom: store state looks right, page never
   changes. `treePath` conversely stays UNprefixed.
2. **Concurrent saves to one page**: one write silently lost. Serialize + re-read.
3. **429 inside HTTP 200**: retry on the GraphQL error message containing `429`/`rate`,
   with growing sleeps (10s, 20s, 30s worked against a real 164-write run).
4. **`routes` without `domain`**: returns `{"data":{"routes":[]}}` with no error, which
   reads as "this account has no pages". Always pass `domain: "store"`.
5. **Occasional 500s** on reads: plain transient, retry with backoff.

## Propagation timing

- Page-scoped saves reach the rendered storefront in **~30s**, no relink needed.
- Deletes keep rendering for minutes after the store confirms removal.
- After installing a new app version in a workspace, **routes warm up independently** —
  mixed old/new versions and 504s for several minutes are normal, not failures.

## Re-deriving the contract if it changed

1. Open `https://{account}.myvtex.com/admin/cms/site-editor` (NOT `admin/new-cms/…`,
   which is Headless CMS) in an authenticated browser.
2. The editor iframe loads `vtex.admin-pages` JS bundles — list them via
   `performance.getEntriesByType('resource')`, download, and grep for
   `query ListContent` / `mutation saveContent` / `mutation DeleteContent`: the full
   operation texts are embedded as string literals.
3. For the exact **variables** shape, click a block in the Site Editor UI and inspect
   the resulting network request: `GET /_v/segment/graphql/v1` with base64-encoded
   `variables` inside the `extensions` query param — decode it. This capture is how the
   app-prefixed `template` requirement was discovered.
4. Synthetic DOM events don't drive the Site Editor React tree reliably; use real
   clicks (a11y-tree based clicking) when you need the UI to fire requests.
