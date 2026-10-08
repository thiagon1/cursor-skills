#!/usr/bin/env python3
"""Read-modify-write a single Site Editor block's content.

Built for seeding preview content into a dev workspace: you supply only the props you
want to change and the script merges them over whatever is already saved, so you never
have to reconstruct a full contentJSON by hand.

Dry run by default. Pass --apply to write.

Auth: `vtex local token`, or VTEX_AUTH_TOKEN in the environment.
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request

from vtex_auth import auth_token, infer_account

PROVIDER = "vtex.pages-graphql@2.x"
SENDER = "vtex.admin-pages@4.x"

LIST_QUERY = """
query ListContentWithSchema($blockId: String!, $pageContext: PageContextInput!,
                            $template: String!, $treePath: String!) {
  listContentWithSchema(blockId: $blockId, pageContext: $pageContext,
                        template: $template, treePath: $treePath) {
    content { contentId contentJSON origin
              condition { allMatches pageContext { id type }
                          statements { subject verb objectJSON } } }
  }
}
"""

SAVE_MUTATION = """
mutation SaveContent($bindingId: String, $blockId: String,
                     $configuration: ContentConfigurationInput,
                     $template: String, $treePath: String, $lang: String) {
  saveContent(bindingId: $bindingId, blockId: $blockId, configuration: $configuration,
              template: $template, treePath: $treePath, lang: $lang) { contentId }
}
"""


def gql(account: str, workspace: str, token: str, query: str, variables: dict) -> dict:
    """POST to the private GraphQL gateway, retrying the failures that are transient.

    Rate limiting arrives as a GraphQL error inside an HTTP 200, so status codes alone
    are not enough to decide whether to back off.
    """
    url = (
        f"https://{workspace}--{account}.myvtex.com"
        f"/_v/private/graphql/v1?workspace={workspace}"
    )
    body = json.dumps(
        {
            "query": query,
            "variables": variables,
            "extensions": {"persistedQuery": {"provider": PROVIDER, "sender": SENDER}},
        }
    ).encode()

    for attempt, backoff in enumerate((10, 20, 30, 0)):
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Cookie": f"VtexIdclientAutCookie={token}",
                "Proxy-Authorization": token,
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                payload = json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            if exc.code in (500, 502, 503, 504) and backoff:
                time.sleep(backoff)
                continue
            sys.exit(f"HTTP {exc.code} from pages-graphql: {exc.read()[:400]!r}")
        except urllib.error.URLError as exc:
            if backoff:
                time.sleep(backoff)
                continue
            sys.exit(f"network error talking to pages-graphql: {exc}")

        errors = payload.get("errors")
        if not errors:
            return payload["data"]

        message = "; ".join(str(e.get("message", "")) for e in errors)
        if backoff and ("429" in message or "rate" in message.lower()):
            time.sleep(backoff)
            continue
        sys.exit(f"pages-graphql error: {message[:500]}")

    sys.exit("pages-graphql kept failing after retries")


def deep_merge(base: dict, patch: dict) -> dict:
    """Merge patch into base, recursing into nested objects.

    Nested merge matters because props like querySchema are objects: setting one key
    should not silently drop the siblings the block relies on.
    """
    out = dict(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def pick_entry(entries: list, page_context: dict):
    """Choose the entry this write will actually update, and say which one it is.

    listContentWithSchema returns the block-DEFAULT entry first (empty contentId,
    pageContext {*,*}), then the saved entries whose condition matches the query's
    pageContext. Taking entries[0] therefore reads code defaults and reports
    "(new entry)" even for a block holding live client content — so the operator sees
    "nothing is saved here" over a client's banner, and the merge starts from the wrong
    base.
    """
    wanted = page_context.get("id")

    def ctx(entry):
        return ((entry.get("condition") or {}).get("pageContext") or {})

    if wanted != "*":
        for entry in entries:
            if entry.get("contentId") and ctx(entry).get("id") == wanted:
                return entry, "page-scoped entry (pageContext id %s)" % wanted
    for entry in entries:
        if entry.get("contentId") and ctx(entry).get("id") == "*":
            return entry, "template-wide entry (pageContext {*,*})"
    for entry in entries:
        if entry.get("contentId"):
            return entry, "saved entry (pageContext %s)" % json.dumps(ctx(entry))
    return {}, "block default — nothing saved here yet"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--account", help="defaults to the account in `vtex whoami`")
    ap.add_argument("--workspace", required=True)
    ap.add_argument(
        "--template",
        required=True,
        help="app-PREFIXED, e.g. vendor.app@11.x:store.custom#my-page",
    )
    ap.add_argument("--tree-path", required=True, help="UNprefixed, starts at the template id")
    ap.add_argument("--block-id", required=True, help="from __RUNTIME__.extensions[tp].blockId")
    patch_src = ap.add_mutually_exclusive_group(required=True)
    patch_src.add_argument("--set-json", help="props to merge, as a JSON object")
    patch_src.add_argument("--set-json-file",
                           help="path to a UTF-8 file holding that JSON object; prefer this "
                                "in PowerShell, which mangles inline double quotes")
    ap.add_argument("--page-context-id", help="e.g. 104 — the id of the ONE page to write")
    ap.add_argument("--page-context-type", help="e.g. subcategory, category, department")
    ap.add_argument("--template-wide", action="store_true",
                    help="write pageContext {*,*}: EVERY page of this template")
    ap.add_argument("--binding-id", default=None)
    ap.add_argument("--lang", default="en-US")
    ap.add_argument("--apply", action="store_true", help="write (default is dry run)")
    ap.add_argument("--allow-master", action="store_true",
                    help="escape hatch for deliberately editing live content; normally wrong")
    args = ap.parse_args()

    if args.workspace == "master" and not args.allow_master:
        sys.exit(
            "refusing to write to master — master IS live production content.\n"
            "Seed into a dev workspace and review it there. If you must change production "
            "content, use a production workspace and let the user promote it.\n"
            "Re-run with --allow-master only if you are deliberately editing live content."
        )
    if args.workspace == "master" and args.apply:
        print("WARNING writing directly to master (live production content).\n")

    # Both of these fail silently rather than erroring, which is what makes them
    # dangerous: the write is accepted and echoed back, but nothing the renderer reads
    # ever changes. Refuse up front instead.
    if ":" not in args.template:
        sys.exit(
            "--template must be app-prefixed (vendor.app@MAJOR.x:store.custom#page).\n"
            "A bare template writes to a store the renderer never reads."
        )
    if ":" in args.tree_path:
        sys.exit("--tree-path must NOT be app-prefixed — it starts at the template id.")

    if args.set_json_file:
        label = "--set-json-file"
        try:
            with open(args.set_json_file, encoding="utf-8-sig") as fh:
                raw = fh.read()
        except OSError as exc:
            sys.exit(f"could not read --set-json-file: {exc}")
    else:
        label = "--set-json"
        raw = args.set_json

    try:
        patch = json.loads(raw)
    except json.JSONDecodeError as exc:
        sys.exit(f"{label} is not valid JSON: {exc}")
    if not isinstance(patch, dict):
        sys.exit(f"{label} must be a JSON object")

    # Scope has to be a decision, not a default. A wildcard write lands on every page of
    # the template, and on some routes it lands somewhere the renderer never reads while
    # saveContent still returns a contentId — a no-op indistinguishable from success.
    if args.template_wide and (args.page_context_id or args.page_context_type):
        sys.exit("--template-wide and --page-context-* are mutually exclusive")
    if args.template_wide:
        page_context = {"id": "*", "type": "*"}
        # Verified on a store.custom route (2026-08-07): a {*,*} write there lands
        # sitewide, the renderer ignores it, and saveContent still returns a contentId.
        if "store.custom#" in args.template:
            sys.exit(
                "--template-wide is wrong for a store.custom#… route.\n"
                "A {*,*} write there lands sitewide and the renderer never reads it, while\n"
                "saveContent still returns a contentId — a silent no-op.\n"
                "Use the route scope instead:\n"
                "  --page-context-id '%s' --page-context-type route --binding-id <id>\n"
                "Read both off the live page: __RUNTIME__.route.pageContext and "
                "__RUNTIME__.binding.id"
                % args.template.split(":", 1)[-1]
            )
    elif args.page_context_id and args.page_context_type:
        page_context = {"id": args.page_context_id, "type": args.page_context_type}
    else:
        sys.exit(
            "choose the scope explicitly:\n"
            "  --page-context-id 104 --page-context-type subcategory   one page only\n"
            "  --template-wide                                         EVERY page of the template\n"
            "Read the page's own scope key from the rendered runtime JSON: "
            '"route":{…"pageContext":{"id":"…","type":"…"}}'
        )

    if args.page_context_type == "route" and not args.binding_id:
        sys.exit(
            "route scope needs --binding-id too — without it the entry lands where the\n"
            "renderer does not look. Read it from the live page: __RUNTIME__.binding.id"
        )

    account = args.account or infer_account()

    token = auth_token()

    data = gql(
        account,
        args.workspace,
        token,
        LIST_QUERY,
        {
            "blockId": args.block_id,
            "pageContext": page_context,
            "template": args.template,
            "treePath": args.tree_path,
        },
    )
    entries = (data.get("listContentWithSchema") or {}).get("content") or []
    existing, source = pick_entry(entries, page_context)
    current = json.loads(existing.get("contentJSON") or "{}")
    content_id = existing.get("contentId") or None

    merged = deep_merge(current, patch)
    if merged == current:
        print(f"no change — the {source} already matches the patch")
        return

    print(f"treePath : {args.tree_path}")
    print(f"scope    : {json.dumps(page_context)}")
    print(f"merging over: {source}")
    print(f"contentId: {content_id or '(new entry)'}")
    print(f"before   : {json.dumps(current, sort_keys=True)[:400]}")
    print(f"after    : {json.dumps(merged, sort_keys=True)[:400]}")

    if not args.apply:
        print("\ndry run — re-run with --apply to write")
        return

    result = gql(
        account,
        args.workspace,
        token,
        SAVE_MUTATION,
        {
            "bindingId": args.binding_id,
            "blockId": args.block_id,
            "configuration": {
                "status": "ACTIVE",
                "condition": {
                    "allMatches": True,
                    "id": "",
                    "pageContext": page_context,
                    "statements": [],
                },
                "contentId": content_id,
                "contentJSON": json.dumps(merged),
                "label": None,
                "origin": None,
            },
            "template": args.template,
            "treePath": args.tree_path,
            "lang": args.lang,
        },
    )
    print(f"\nsaved contentId: {(result.get('saveContent') or {}).get('contentId')}")
    print(
        "The response only proves the write was accepted. Reload the workspace page and\n"
        "re-read __RUNTIME__.extensions[treePath].content to confirm the renderer sees it\n"
        "(~30s, no relink needed)."
    )


if __name__ == "__main__":
    main()
