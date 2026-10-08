# Migration pipeline (block structure changed)

Read this when content has been orphaned by a treePath change, or is about to be. For
seeding content into a page that never had any, read `seeding.md` instead — this pipeline's
gates exist to protect real client-entered data and are overkill for preview content.

Work through the phases in order. Each gate exists because skipping it has already caused
real data loss or false confidence — don't proceed past a gate that fails.

## Phase 0 — Scope the migration

1. Diff the theme change to list every block whose treePath changes (moved between
   parents, renamed `#instance`, removed from a layout). Renames and moves are the same
   thing to the CMS: old path dies, new path is born empty.
2. Write the mapping: old treePath → new treePath, per template. `treePath` starts at
   the template id (`store.search#subcategory/...`) with NO app prefix.
3. Enumerate affected pages with `scripts/enumerate_pages.py`. The output feeds
   `backup_content.py --urls-file`, and the list must be the **complete** page set of the
   template — scope inference and "did we capture everything?" both depend on it.

   ```
   # category-driven templates (department = level 1, category = 2, sub-category = 3)
   python3 scripts/enumerate_pages.py --base-url https://www.store.com --catalog-tree 3 --level subcategory --auth --out pages.txt

   # anything else: landing pages, institutional, brands
   python3 scripts/enumerate_pages.py --base-url https://www.store.com --sitemap --match '/collection/' --out pages.txt
   ```

   Use `--out`, not a `>` redirect: PowerShell 5.1 writes redirects as UTF-16, which the
   next script cannot read.

   `--auth` cross-checks the public tree against the private one. Different counts mean
   pages exist that the public tree does not list, and a crawl would silently miss them.
   Also grep the theme for other bindings of the same template.
4. Find the storefront `bindingId`: fetch any rendered page and read
   `"binding":{"id":"..."}` from the embedded runtime JSON. Multi-binding stores have
   per-binding content — repeat the whole flow per binding.

**Gate:** you can state exactly which treePaths die, which pages are affected, and the
bindingId. If the user hasn't confirmed the structure change is intentional, stop here.

## Phase 1 — Backup from production (BEFORE the new structure reaches it)

The backup source is the **rendered page**: every VTEX IO page embeds its full content
map as `{"contentJSON":..., "contentIds":[...], "treePath":...}` entries — the exact
payload pages-graphql feeds the renderer. Old treePaths only appear where the old
structure still renders, so capture before the change ships to the crawl target.

```
python3 scripts/backup_content.py --base-url https://www.store-domain.com --urls-file pages.txt --out backup-YYYY-MM-DD.json --confirm-scope --account myaccount
```

- The script uses a **mobile UA** (mobile-layout treePaths are omitted for desktop UAs;
  the mobile render includes both).
- Non-empty `contentIds` = saved in Site Editor; `contentJSON` is the saved delta, not
  merged block props.
- The script annotates **scope** per entry. Without `--confirm-scope` that scope is
  *inferred*: the same contentId on more than one page ⇒ template, unique to one page ⇒
  page. The inference is only valid over the complete page set, so **run
  `--confirm-scope`** — it reads each entry's own `condition.pageContext` from
  pages-graphql and reports every entry where the inference was wrong. Entries it cannot
  resolve are marked `unconfirmed` and keep the inferred value; check those by hand
  before replaying, because replaying a template entry writes it onto every page.
- Desktop and mobile layouts may hold *different* content for the same logical block —
  keep both and flag diffs.
- **The capture is active content only.** A rendered page carries the content version
  that is live right now. Other saved versions, scheduled content and inactive entries
  exist in the CMS, never appear in the crawl, and no API enumerates them — the Site
  Editor UI is the only place they are visible. If the client uses versions or
  scheduling on these blocks, say so before promising a complete backup.
- Store backups in a git-ignored folder in the repo (for example `.ai/backups/`). Confirm
  the folder really is ignored before assuming the files stay private.
- Run the script twice some time apart and diff: identical output proves the capture is
  stable and nothing is being edited mid-migration.

**Gate:** 0 fetch errors, 0 unexplained `unconfirmed` entries among the ones you plan to
replay, and the with-content page counts look plausible to the user.

## Phase 2 — Build the restore input

Produce one migration JSON (schema in `content-model.md`) containing ONLY:
- **page-scoped** entries with non-empty content (template-scoped placeholder/empty
  entries usually should not be replayed — confirm with the user),
- the **new** treePath per block,
- each entry's own `pageContext` (`{"id": "<categoryId>", "type": "subcategory"}` etc.,
  read from the backup's per-page route data),
- `template` in **app-prefixed** form: `vendor.app@MAJOR.x:store.search#subcategory`.

Where desktop and mobile previously held different content and the new structure has a
single block, a human must pick the winner per page — surface the list of diffs, don't
choose silently.

## Phase 3 — Prove it end-to-end in a dev workspace

**Never `master`.** `master` is live production content. There is no undo: a dev
workspace can be discarded, a bad write to `master` cannot. The write scripts refuse
`--workspace master` outright, and the `--allow-master` escape hatch exists only for
repairing content that is already lost. This phase runs in a **dev workspace**, Phase 4
runs in a **production workspace**, and only the user promotes.

Use a workspace already serving the **new** structure. Prefer a **fresh** dev workspace:
a workspace you have been testing in already holds stray entries, and those make the
verification lie.

Work through these in order, and stop at the first one that fails:

1. **Dry run, whole file.** Expect `WOULD-CREATE` for every block and 0 errors.
   ```
   python3 scripts/restore_content.py --workspace <dev-ws> --file migration.json
   ```
2. **Apply one page.** Smallest possible blast radius, and it proves the write path.
   ```
   python3 scripts/restore_content.py --workspace <dev-ws> --file migration.json --only /one-page --apply
   ```
3. **Re-run that page.** Expect all `SKIP` — this proves the run is idempotent and safe
   to repeat after a partial failure.
4. **Apply the whole file**, then re-run until the summary is **all SKIP**. A second
   pass is normal; rate limits and transient errors leave work behind.
5. **Verify against the file.**
   ```
   python3 scripts/verify_restore.py --workspace <dev-ws> --file migration.json
   ```
6. **Verify against reality.** Open a restored page at desktop **and** mobile widths.
   Confirm the content renders in its new position. Confirm a **sibling page that should
   have different content still does** — that is what catches a wildcard or
   template-scoped write. Saves appear in ~30s with no relink.

**Gate — every one of these, or Phase 4 does not start:**

- final run reports **all SKIP**, 0 errors, 0 `VERIFY-FAILED`
- `verify_restore.py` reports 0 problems
- one page confirmed rendering at both breakpoints
- one sibling page confirmed **unchanged**
- any test entries you created by hand are deleted and confirmed gone (Phase 5)

Report these results to the user and let them confirm before touching a production
workspace. The dev run is the only rehearsal you get.

## Phase 4 — The real run (production workspace)

Start only after **Phase 3's gate passed** and the user published the new theme version
and installed it in a **production workspace**.

**Still not `master`.** A production workspace is a copy that the user promotes when they
are satisfied. Writing to `master` instead skips their review and cannot be undone.
Promoting is the user's action, never yours.

1. Confirm the workspace serves the new version on the affected routes. After install,
   routes warm up independently — some serve the old cached version for minutes and 504s
   are normal. Wait; don't write against a route still rendering old paths.
2. Re-run the backup against production and diff against the Phase-1 capture. Non-zero
   diff = content was edited since — rebuild the restore input first.
3. Dry run → `--apply` → re-run until all SKIP → `verify_restore.py` → spot-check a few
   pages against the LIVE production text (not just against your own backup file — that
   check would be circular).
4. Hand the user 2–3 concrete URL pairs (workspace vs production) to eyeball, then let
   them promote.

## Phase 5 — Cleanup

Delete any test entries you created (full contentId required — see gotchas), verify
deletion via `listContentWithSchema` (the delete response is not proof), and restore any
browser viewport emulation you changed.

## Migration-specific gotchas

The traps that apply to *any* content write live in SKILL.md. These are the ones that
only bite during a bulk migration:

- **Never write concurrently.** Two parallel `saveContent` calls touching the same page
  silently lose one (success response, entry absent). Writes are serialized in the
  script with read-back verification — keep them that way. Reads can stay parallel.
- **Rate limits hide inside HTTP 200.** The gateway returns 429 as a GraphQL error
  message in a 200 response. Back off on message content, not status code.
- **Wildcard scope is a footgun.** `pageContext {id:"*", type:"*"}` writes a
  template-wide entry hitting every page of that template. The restore script hard-fails
  on it; a Site Editor UI session can also create one accidentally — page scope beats
  template scope at render, so a leaked template entry shows on every page that lacks
  page content.
- **Sitewide scope is invisible to the API.** Entries saved sitewide never come back
  from `listContentWithSchema` and `deleteContent` won't match them — they can only be
  removed via the Site Editor UI.
- **`deleteContent` lies twice.** It echoes success for a truncated contentId (deletes
  nothing — the full `mapId~entryId` is required) and even a real delete keeps rendering
  for minutes. Verify deletions with a list call, never the response or the page.
- **Workspace partitioning.** Content is per-workspace; publishing an app moves zero
  content; only `vtex workspace promote` does. Dev-workspace experiments cannot leak to
  production — and equally, a restore into a dev workspace helps production not at all.
