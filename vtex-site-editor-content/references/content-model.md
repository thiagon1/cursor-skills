# Site Editor content model

## treePath keying

Content is stored against the block's **treePath**: the slash-joined chain of block ids
from the page template to the block, e.g.

```
store.search#subcategory/flex-layout.row#seo-text/gradient-collapse#seo-text/rich-text#seo-title
```

Any change to that chain — moving the block to another parent, renaming an `#instance`,
re-nesting through a different layout — orphans the content stored under the old path.
The data is never deleted; it just stops resolving. This is why "change props in place,
don't rename" is the rule for blocks holding client content, and why a deliberate
structure change requires this migration flow.

## The three scopes

Each saved entry carries `condition.pageContext`:

| Scope | pageContext | Behavior |
|---|---|---|
| **page** | `{id:"104", type:"subcategory"}` | One page only. **Wins over template at render.** |
| **template** | `{id:"*", type:"*"}` | Every page of the template. |
| **sitewide** | (separate storage) | Invisible to `listContentWithSchema`; UI-only to manage. |

The Site Editor UI derives the label it shows from
`isSitewide ? "sitewide" : id === "*" ? "template" : "page"`.

**Inferring scope from a crawl** (no API needed): the same `contentId` appearing on more
than one page ⇒ template/sitewide; unique to one page ⇒ page-scoped. This matters
because the restore should replay only page-scoped, non-empty entries. The inference is
only valid over the COMPLETE page set of the template — a partial crawl can't detect
sharing and will misclassify template entries as page-scoped, which then get replayed
onto every page.

Prefer the authoritative answer: `listContentWithSchema` returns each entry's
`condition.pageContext` directly, and `backup_content.py --confirm-scope` runs that check
over a whole capture.

## contentIds anatomy

`contentId` = `<contentMapId>~<entryId>` (e.g. `g3tndnLvX7n3QecCx7R6y3~ouLxjYxEF46drQ4q9VfGMz`).
The contentMapId groups entries for one block position; the entryId identifies the
specific saved record. Deletions and updates require the FULL string.

## The rendered-page content map

Every VTEX IO page embeds, in its runtime JSON, one record per block:

```json
{"contentJSON":"{\"text\":\"…\"}","contentIds":["g3tn…~ouLx…"],"treePath":"store.search#…/rich-text#seo-title"}
```

- Non-empty `contentIds` ⇒ the value came from Site Editor; empty ⇒ block default.
- `contentJSON` is the saved delta (or the default props when no content).
- The HTML escapes `/` as `/` — normalize before matching.
- Fetch with `--compressed` (the payload is gzip'd; without decompression you see
  binary and every grep finds nothing).
- **Use a mobile UA**: desktop renders omit `search-result-layout.mobile` treePaths;
  the mobile render includes both layouts.
- Desktop and mobile layouts can hold DIFFERENT saved content for the same logical
  block (separately filled in the UI over the years). A migration collapsing them into
  one block forces a per-page choice — surface the diffs to the user.
- The page also embeds `"binding":{"id":"…"}` (needed for API calls),
  `"route":{…"pageContext":{"id":"…","type":"…"}}` (each page's own scope key), and an
  extensions map keyed by treePath carrying `"blockId":"vendor.app@1.x:block#id"` — the
  blockId in exactly the form the API wants.
- **Only the ACTIVE version is in the page.** Site Editor supports content versions,
  scheduling and inactive entries. None of them reach the rendered page, and no API
  lists them; the Site Editor UI is the only place they exist. A crawl captures what the
  storefront serves, which is not the same as everything in the CMS.

Production content = the `master` workspace = what the public domain serves. Content is
workspace-partitioned; `vtex publish`/install moves no content, only
`vtex workspace promote` does.

## Migration file schema (consumed by restore/verify scripts)

```json
{
  "account": "myaccount",
  "bindingId": "4d17936a-62c6-4734-9a17-bece772fc04a",
  "template": "vendor.store-theme@11.x:store.search#subcategory",
  "generatedAt": "YYYY-MM-DD",
  "notes": "anything future-you needs",
  "entries": [
    {
      "url": "https://www.store.com/dept/cat/subcat",
      "pageContext": { "id": "104", "type": "subcategory" },
      "blocks": [
        {
          "treePath": "store.search#subcategory/flex-layout.row#seo-text/gradient-collapse#seo-text/rich-text#seo-title",
          "blockId": "vendor.store-theme@11.x:rich-text#seo-title",
          "content": { "text": "# Sport Boots" },
          "source": { "note": "optional: old treePath + contentIds for audit" }
        }
      ]
    }
  ]
}
```

Rules the scripts enforce (keep them if you edit the scripts):

- `template` and `blockId` are app-prefixed; `treePath` is NOT (hard-fail otherwise).
- Every entry has its own concrete `pageContext` — `id` of `*`/empty is refused, because
  a wildcard write lands on every page of the template.
- `content` is the object to save (it gets JSON-stringified into `contentJSON`).
