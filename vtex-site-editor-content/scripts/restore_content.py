"""Restore Site Editor content to a new block structure via pages-graphql.

Reads a migration JSON (schema: references/content-model.md) and re-creates each
block's content at its NEW treePath, scoped to that entry's own page.

Dry run by default — nothing is written without --apply. Idempotent: re-run until the
summary is all SKIP. Writes are serialized with read-back verification because parallel
saves to the same page silently lose entries.

  python3 restore_content.py --workspace <ws> --file migration.json            # dry run
  python3 restore_content.py --workspace <ws> --file migration.json --apply
  python3 restore_content.py --workspace <ws> --file migration.json --only /sport-boots --apply

Auth: `vtex local token` unless VTEX_AUTH_TOKEN is set.
"""

import argparse, gzip, io, json, sys, time, urllib.error, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

from vtex_auth import auth_token

SENDER = "vtex.admin-pages@4.59.2"
PROVIDER = "vtex.pages-graphql@2.x"

LIST_Q = """query ListContent($bindingId: String, $blockId: String, $pageContext: PageContextInput, $template: String, $treePath: String) @context(sender: "%s") {
  listContentWithSchema(bindingId: $bindingId, blockId: $blockId, pageContext: $pageContext, template: $template, treePath: $treePath) {
    content { contentId contentJSON condition { pageContext { id type } } }
  }
}""" % SENDER

SAVE_M = """mutation saveContent($bindingId: String, $blockId: String, $configuration: ContentConfigurationInput, $template: String, $treePath: String, $lang: String) @context(sender: "%s") {
  saveContent(bindingId: $bindingId, blockId: $blockId, configuration: $configuration, template: $template, treePath: $treePath, lang: $lang) { contentId }
}""" % SENDER


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
                    # gateway reports rate limits INSIDE a 200 response
                    if "429" in msg or "rate" in msg.lower():
                        last = RuntimeError(msg)
                        time.sleep(10 * (attempt + 1))
                        continue
                    raise RuntimeError(msg)
                return payload["data"]
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
                last = e
                time.sleep(2 * (attempt + 1))
        raise RuntimeError("request failed after %d attempts: %s" % (retries, last))


def page_entry(entries, ctx_id):
    for e in entries:
        if e["condition"]["pageContext"]["id"] == ctx_id:
            return e
    return None


def process(client, data, page, block, apply_changes, lang):
    ctx = page["pageContext"]
    common = {
        "bindingId": data["bindingId"],
        "blockId": block["blockId"],
        "template": data["template"],
        "treePath": block["treePath"],
    }
    label = "%s | %s" % (page["url"].rsplit("/", 1)[-1], block["treePath"].rsplit("/", 1)[-1])
    wanted = block["content"]

    try:
        current = client.call(LIST_Q, dict(common, pageContext=ctx))["listContentWithSchema"]["content"]
    except Exception as e:
        return {"label": label, "action": "ERROR-READ", "detail": str(e)[:120]}

    existing = page_entry(current, ctx["id"])
    if existing and json.loads(existing["contentJSON"]) == wanted:
        return {"label": label, "action": "SKIP", "detail": "already restored"}

    action = "UPDATE" if existing else "CREATE"
    if not apply_changes:
        return {"label": label, "action": "WOULD-" + action, "detail": json.dumps(wanted)[:60]}

    for attempt in range(3):
        cfg = {
            "status": "ACTIVE",
            "condition": {"allMatches": True, "id": "", "pageContext": ctx, "statements": []},
            "contentId": existing["contentId"] if existing else None,
            "contentJSON": json.dumps(wanted),
            "label": None,
            "origin": None,
        }
        try:
            client.call(SAVE_M, dict(common, configuration=cfg, lang=lang))
        except Exception as e:
            return {"label": label, "action": "ERROR-WRITE", "detail": str(e)[:120]}

        time.sleep(1.5)
        after = client.call(LIST_Q, dict(common, pageContext=ctx))["listContentWithSchema"]["content"]
        saved = page_entry(after, ctx["id"])
        if saved and json.loads(saved["contentJSON"]) == wanted:
            return {"label": label, "action": action, "detail": "attempt %d" % (attempt + 1)}
        existing = saved

    return {"label": label, "action": "VERIFY-FAILED", "detail": json.dumps(wanted)[:60]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--file", required=True)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--lang", default="en-US")
    ap.add_argument("--limit", type=int, help="only the first N pages")
    ap.add_argument("--only", help="only pages whose url contains this string")
    ap.add_argument("--allow-master", action="store_true",
                    help="escape hatch for repairing lost content in master; normally wrong")
    args = ap.parse_args()

    if args.workspace == "master" and not args.allow_master:
        sys.exit(
            "refusing to write to master — master IS live production content.\n"
            "The order is: dev workspace (prove it) -> production workspace (real run) -> "
            "the user promotes.\n"
            "Writing to master skips both gates and cannot be rolled back by discarding a "
            "workspace.\n"
            "If you are repairing already-lost content and no workspace exists to promote, "
            "re-run with --allow-master."
        )
    if args.workspace == "master" and args.apply:
        print("WARNING writing directly to master (live production content). "
              "There is no workspace to discard if this is wrong.\n")

    data = json.load(open(args.file, encoding="utf-8-sig"))
    for key in ("account", "bindingId", "template", "entries"):
        if not data.get(key):
            sys.exit("migration file missing required key: %s" % key)
    if ":" not in data["template"]:
        sys.exit("template must be app-prefixed (vendor.app@MAJOR.x:store...) — bare "
                 "templates make saves invisible to the renderer while reading back fine")

    pages = data["entries"]
    if args.only:
        pages = [p for p in pages if args.only in p["url"]]
    if args.limit:
        pages = pages[: args.limit]

    jobs = [(p, b) for p in pages for b in p["blocks"]]
    for p, b in jobs:
        if ":" in b["treePath"].split("/")[0]:
            sys.exit("treePath must NOT be app-prefixed: %s" % b["treePath"])
        if p["pageContext"].get("id") in ("*", "", None):
            sys.exit("refusing wildcard pageContext for %s — it would write to EVERY "
                     "page of the template" % p["url"])

    client = Client(data["account"], args.workspace, auth_token())
    mode = "APPLY" if args.apply else "DRY RUN"
    print("%s | account=%s workspace=%s | %d pages | %d blocks\n"
          % (mode, data["account"], args.workspace, len(pages), len(jobs)))

    if args.apply:
        results = []
        for i, (p, b) in enumerate(jobs, 1):
            results.append(process(client, data, p, b, True, args.lang))
            print("  [%d/%d] %-13s %s" % (i, len(jobs), results[-1]["action"], results[-1]["label"]),
                  flush=True)
    else:
        with ThreadPoolExecutor(max_workers=4) as ex:
            results = list(ex.map(lambda j: process(client, data, j[0], j[1], False, args.lang), jobs))

    counts = {}
    for r in results:
        counts[r["action"]] = counts.get(r["action"], 0) + 1
        if r["action"].startswith(("ERROR", "VERIFY")):
            print("  %-13s %-55s %s" % (r["action"], r["label"], r["detail"]))
    print("\nsummary:")
    for k in sorted(counts):
        print("  %-15s %d" % (k, counts[k]))
    if not args.apply:
        print("\nno changes written — re-run with --apply")
    if any(k.startswith(("ERROR", "VERIFY")) for k in counts):
        sys.exit(1)


if __name__ == "__main__":
    main()
