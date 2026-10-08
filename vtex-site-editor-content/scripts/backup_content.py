"""Backup VTEX IO Site Editor content by crawling rendered storefront pages.

Each rendered page embeds its full content map (contentJSON / contentIds / treePath).
This captures it for every URL given, plus the page's route pageContext, bindingId and
each block's blockId, and annotates every entry's scope (page vs template).

Scope comes from one of two sources, and they are not equal:
  inferred  — the same contentId seen on >1 page means template scope. Only valid over
              the COMPLETE page set of a template; a partial crawl misclassifies.
  confirmed — --confirm-scope asks pages-graphql for each entry's own
              condition.pageContext. Authoritative, needs auth, one call per entry.

Read-only in both modes. Run against the PRODUCTION domain before the structure change
ships there; re-run later and diff to confirm nothing changed.

  python3 backup_content.py --base-url https://www.store.com --urls-file pages.txt --out backup.json
  python3 backup_content.py --base-url https://ws--acct.myvtex.com --auth --urls-file pages.txt --out ws.json
  python3 backup_content.py --base-url https://www.store.com --urls-file pages.txt --out backup.json --confirm-scope --account myaccount

--urls-file: one URL or absolute path per line (paths are joined to --base-url).
--auth: attach the vtex local token cookie (needed for *.myvtex.com workspaces).

LIMITATION: a rendered page carries only the content version that is ACTIVE now. Other
saved versions, scheduled content and inactive entries exist in the CMS and never appear
here. There is no API to enumerate them — the Site Editor UI is the only place they are
visible. Treat this file as "what the storefront serves", not "everything in the CMS".
"""

import argparse, gzip, io, json, re, sys, time, urllib.error, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

from vtex_auth import auth_token

UA_MOBILE = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
             "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")
ENTRY = re.compile(r'\{"contentJSON":"((?:[^"\\]|\\.)*)","contentIds":\[([^\]]*)\],"treePath":"((?:[^"\\]|\\.)*)"\}')
ROUTE = re.compile(r'"route":\{[^}]*"id":"([^"]+)"[^}]*"pageContext":\{"id":"([^"]+)","type":"([^"]+)"\}')
BINDING = re.compile(r'"binding":\{"id":"([0-9a-f-]+)"')
# extensions map: "<treePath>":{…,"blockId":"vendor.app@1.x:block#id",…}
# [^{}] stops the match at a nested object, so a miss yields no blockId rather than a wrong one.
EXT = re.compile(r'"([^"]{3,300})":\{(?:[^{}]{0,300}?)"blockId":"([^"]+)"')

SENDER = "vtex.admin-pages@4.59.2"
PROVIDER = "vtex.pages-graphql@2.x"
LIST_Q = """query ListContent($bindingId: String, $blockId: String, $pageContext: PageContextInput, $template: String, $treePath: String) @context(sender: "%s") {
  listContentWithSchema(bindingId: $bindingId, blockId: $blockId, pageContext: $pageContext, template: $template, treePath: $treePath) {
    content { contentId condition { pageContext { id type } } }
  }
}""" % SENDER


def fetch(url, token=None, retries=4):
    last = None
    for attempt in range(retries):
        headers = {"User-Agent": UA_MOBILE, "Accept-Encoding": "gzip"}
        if token:
            headers["Cookie"] = "VtexIdclientAutCookie=%s" % token
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=90) as r:
                raw = r.read()
                enc = r.headers.get("Content-Encoding")
            if enc == "gzip":
                raw = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
            return raw.decode("utf-8", "replace")
        except Exception as e:
            last = e
            time.sleep(4 * (attempt + 1))
    raise RuntimeError("failed after %d attempts: %s" % (retries, last))


def extract(html):
    html = html.replace("\\u002F", "/")
    block_ids = dict(EXT.findall(html))
    saved, total = {}, 0
    for cjson, ids, tp in ENTRY.findall(html):
        total += 1
        ids = [i.strip('"') for i in ids.split(",") if i.strip('"')]
        if not ids:
            continue
        path = json.loads('"' + tp + '"')
        saved[path] = {
            "contentIds": ids,
            "blockId": block_ids.get(path),
            "content": json.loads(json.loads('"' + cjson + '"')),
        }
    route = ROUTE.search(html)
    binding = BINDING.search(html)
    return saved, total, route, binding


def work(url, token):
    try:
        html = fetch(url, token)
        saved, total, route, binding = extract(html)
        return {
            "url": url,
            "route": ({"template": route.group(1), "pageContextId": route.group(2),
                       "pageContextType": route.group(3)} if route else None),
            "bindingId": binding.group(1) if binding else None,
            "blocksOnPage": total,
            "savedContent": saved,
        }
    except Exception as e:
        return {"url": url, "error": repr(e)}


def annotate_scope(results):
    pages_by_entry = {}
    for r in results:
        for tp, v in r.get("savedContent", {}).items():
            for cid in v["contentIds"]:
                pages_by_entry.setdefault((tp, cid), set()).add(r["url"])
    for r in results:
        for tp, v in r.get("savedContent", {}).items():
            shared = max(len(pages_by_entry[(tp, cid)]) for cid in v["contentIds"])
            v["scope"] = "template" if shared > 1 else "page"
            v["scopeSource"] = "inferred"
            v["sharedByPages"] = shared


class Client:
    def __init__(self, account, workspace, token):
        ext = json.dumps({"persistedQuery": {"provider": PROVIDER, "sender": SENDER}})
        self.url = (
            "https://%s.myvtex.com/_v/private/graphql/v1"
            "?workspace=%s&maxAge=short&appsEtag=remove&domain=admin&locale=en-US"
            "&extensions=%s" % (account, workspace, urllib.parse.quote(ext))
        )
        self.token = token

    def call(self, query, variables, retries=3):
        body = json.dumps({"query": query, "variables": variables}).encode()
        last = None
        for attempt in range(retries):
            req = urllib.request.Request(self.url, data=body, method="POST", headers={
                "content-type": "application/json",
                "accept-encoding": "gzip",
                "cookie": "VtexIdclientAutCookie=%s" % self.token,
            })
            try:
                with urllib.request.urlopen(req, timeout=90) as r:
                    raw = r.read()
                    if r.headers.get("Content-Encoding") == "gzip":
                        raw = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
                payload = json.loads(raw.decode("utf-8", "replace"))
                if payload.get("errors"):
                    msg = payload["errors"][0].get("message", "graphql error")
                    # the gateway reports rate limits INSIDE a 200 response
                    if "429" in msg or "rate" in msg.lower():
                        last = RuntimeError(msg)
                        time.sleep(10 * (attempt + 1))
                        continue
                    raise RuntimeError(msg)
                return payload["data"]
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
                last = e
                time.sleep(2 * (attempt + 1))
        raise RuntimeError("graphql call failed: %s" % last)


def confirm_scope(results, client, template_prefix=None):
    """Replace inferred scope with each entry's own condition.pageContext.

    An entry the API cannot resolve keeps its inferred scope and is marked unconfirmed —
    never silently treated as page-scoped, because replaying a template entry writes it
    onto every page of the template.
    """
    stats = {"confirmed": 0, "unconfirmed": 0, "mismatch": 0, "slots": 0}
    mismatches = []
    for r in results:
        route = r.get("route")
        if not route or not r.get("bindingId"):
            for v in r.get("savedContent", {}).values():
                v["scopeSource"] = "unconfirmed: no route/bindingId on page"
                stats["unconfirmed"] += 1
            continue
        page_ctx = {"id": route["pageContextId"], "type": route["pageContextType"]}
        for tp, v in r.get("savedContent", {}).items():
            # $-segments are runtime layout slots ($after_footer, $before_footer …), not
            # content blocks. They carry contentIds in the page payload but the API does
            # not resolve them, so they are expected non-answers, not failures.
            if "$" in tp:
                v["scopeSource"] = "slot placeholder — not a content block"
                stats["slots"] += 1
                continue
            block_id = v.get("blockId")
            if not block_id:
                v["scopeSource"] = "unconfirmed: no blockId in page payload"
                stats["unconfirmed"] += 1
                continue
            prefix = template_prefix or block_id.split(":")[0]
            template = "%s:%s" % (prefix, route["template"])
            try:
                data = client.call(LIST_Q, {
                    "bindingId": r["bindingId"], "blockId": block_id, "template": template,
                    "treePath": tp, "pageContext": page_ctx,
                })
                entries = (data.get("listContentWithSchema") or {}).get("content") or []
            except Exception as e:
                v["scopeSource"] = "unconfirmed: %s" % type(e).__name__
                stats["unconfirmed"] += 1
                continue
            by_id = {c.get("contentId"): c for c in entries}
            match = next((by_id[cid] for cid in v["contentIds"] if cid in by_id), None)
            if not match:
                v["scopeSource"] = "unconfirmed: contentId not returned by the API"
                stats["unconfirmed"] += 1
                continue
            ctx = ((match.get("condition") or {}).get("pageContext") or {})
            real = "template" if ctx.get("id") in ("*", None) else "page"
            if real != v["scope"]:
                stats["mismatch"] += 1
                mismatches.append((r["url"], tp.split("/")[-1], v["scope"], real))
            v["scope"] = real
            v["scopeSource"] = "confirmed"
            v["pageContext"] = {"id": ctx.get("id"), "type": ctx.get("type")}
            stats["confirmed"] += 1
    return stats, mismatches


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--urls-file", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--auth", action="store_true", help="attach vtex local token cookie")
    ap.add_argument("--confirm-scope", action="store_true",
                    help="ask pages-graphql for each entry's real scope (needs --account)")
    ap.add_argument("--account", help="VTEX account, required with --confirm-scope")
    ap.add_argument("--workspace", default="master", help="workspace to confirm against (default master)")
    ap.add_argument("--template-prefix", help="override the app prefix, e.g. vendor.store-theme@11.x")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()

    if args.confirm_scope and not args.account:
        sys.exit("--confirm-scope needs --account")

    base = args.base_url.rstrip("/")
    urls = []
    for line in open(args.urls_file, encoding="utf-8-sig"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        urls.append(line if line.startswith("http") else base + line)

    token = auth_token() if (args.auth or args.confirm_scope) else None
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        results = list(ex.map(lambda u: work(u, token), urls))

    annotate_scope(results)

    stats, mismatches = None, []
    if args.confirm_scope:
        client = Client(args.account, args.workspace, token)
        stats, mismatches = confirm_scope(results, client, args.template_prefix)

    json.dump(results, open(args.out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    ok = [r for r in results if "error" not in r]
    err = [r for r in results if "error" in r]
    n_page = sum(1 for r in ok for v in r["savedContent"].values() if v["scope"] == "page")
    n_tmpl = sum(1 for r in ok for v in r["savedContent"].values() if v["scope"] == "template")
    print("pages: %d | ok: %d | errors: %d" % (len(results), len(ok), len(err)))
    print("saved entries: %d page-scoped, %d template-scoped" % (n_page, n_tmpl))
    if stats:
        print("scope confirmed via API: %d | unconfirmed: %d | inference was wrong: %d "
              "| layout slots skipped: %d"
              % (stats["confirmed"], stats["unconfirmed"], stats["mismatch"], stats["slots"]))
        for url, block, was, real in mismatches[:10]:
            print("  MISMATCH %s | %s | inferred %s -> real %s" % (url, block, was, real))
        if stats["unconfirmed"]:
            print("  unconfirmed entries keep their inferred scope — check them before replaying")
    else:
        print("scope is INFERRED. Valid only if these URLs are the complete page set of the "
              "template. Re-run with --confirm-scope --account <acct> to make it authoritative.")
    for r in err[:10]:
        print("  ERR", r["url"], r["error"])
    if err:
        sys.exit(1)


if __name__ == "__main__":
    main()
