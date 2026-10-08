"""List every page URL of a template, to feed backup_content.py --urls-file.

Scope inference and "did we back up everything?" both depend on this list being the
COMPLETE page set for the template. Guessing a few URLs is what makes a migration lose
content on the pages nobody thought to check.

  # every sub-category page (catalog level 3 = department > category > sub-category)
  python3 enumerate_pages.py --base-url https://www.store.com --catalog-tree 3 --level subcategory --out pages.txt

  # every category page, cross-checked against the private tree for hidden nodes
  python3 enumerate_pages.py --base-url https://www.store.com --catalog-tree 3 --level category --auth --out pages.txt

  # non-catalog templates (landing pages, institutional, brands)
  python3 enumerate_pages.py --base-url https://www.store.com --sitemap --match '/collection/' --out pages.txt

Levels map to catalog depth: department = level 1, category = 2, subcategory = 3.
Deeper trees are supported — --level 4 and beyond work by number.

Read-only. Writes one URL per line to --out (UTF-8) or to stdout, and a summary to stderr.
Prefer --out over a `>` redirect: PowerShell 5.1 redirects to UTF-16, which backup_content
cannot read.
"""

import argparse, gzip, io, json, re, sys, urllib.request

from vtex_auth import auth_token

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
LEVELS = {"department": 1, "category": 2, "subcategory": 3}


def fetch(url, token=None):
    headers = {"User-Agent": UA, "Accept-Encoding": "gzip"}
    if token:
        headers["Cookie"] = "VtexIdclientAutCookie=%s" % token
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=90) as r:
        raw = r.read()
        enc = r.headers.get("Content-Encoding")
    if enc == "gzip":
        raw = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
    return raw.decode("utf-8", "replace")


def walk(nodes, depth, want, out):
    for n in nodes:
        if depth == want:
            out.append(n["url"])
        walk(n.get("children") or [], depth + 1, want, out)


def count_nodes(nodes):
    return sum(1 + count_nodes(n.get("children") or []) for n in nodes)


def from_catalog(base, depth, want, token):
    tree = json.loads(fetch("%s/api/catalog_system/pub/category/tree/%d" % (base, depth)))
    urls = []
    walk(tree, 1, want, urls)
    print("public tree: %d nodes total, %d at level %d" % (count_nodes(tree), len(urls), want), file=sys.stderr)
    if token:
        # identical counts prove the public tree hides nothing; a difference means
        # inactive or unindexed categories exist that the crawl would silently miss
        try:
            pvt = json.loads(fetch("%s/api/catalog_system/pvt/category/tree/%d" % (base, depth), token))
            pvt_urls = []
            walk(pvt, 1, want, pvt_urls)
            if len(pvt_urls) != len(urls):
                print("WARNING private tree has %d pages at this level, public has %d — "
                      "%d page(s) are not publicly listed and will be missed"
                      % (len(pvt_urls), len(urls), abs(len(pvt_urls) - len(urls))), file=sys.stderr)
                extra = [u for u in pvt_urls if u not in set(urls)]
                for u in extra[:10]:
                    print("  only in private tree: %s" % u, file=sys.stderr)
            else:
                print("private tree matches (%d) — the public list is complete" % len(pvt_urls), file=sys.stderr)
        except Exception as e:
            print("could not cross-check the private tree (%s) — completeness unverified"
                  % type(e).__name__, file=sys.stderr)
    return urls


def from_sitemap(base, match):
    seen, urls = set(), []
    queue = ["%s/sitemap.xml" % base]
    while queue:
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        try:
            body = fetch(url)
        except Exception as e:
            print("skip %s (%s)" % (url, type(e).__name__), file=sys.stderr)
            continue
        locs = re.findall(r"<loc>\s*([^<]+?)\s*</loc>", body)
        if "<sitemapindex" in body:
            queue.extend(locs)
        else:
            urls.extend(locs)
    if match:
        rx = re.compile(match)
        urls = [u for u in urls if rx.search(u)]
    print("sitemap: %d URLs%s" % (len(urls), " matching %s" % match if match else ""), file=sys.stderr)
    return urls


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--catalog-tree", type=int, metavar="DEPTH", help="walk the catalog category tree")
    ap.add_argument("--level", help="department | category | subcategory, or a depth number")
    ap.add_argument("--sitemap", action="store_true", help="read sitemap.xml instead")
    ap.add_argument("--match", help="regex filter, used with --sitemap")
    ap.add_argument("--auth", action="store_true", help="cross-check against the private catalog tree")
    ap.add_argument("--out", help="write the list here as UTF-8 instead of stdout; use this "
                                  "rather than a `>` redirect, which PowerShell 5.1 writes as UTF-16")
    args = ap.parse_args()

    base = args.base_url.rstrip("/")
    if args.sitemap:
        urls = from_sitemap(base, args.match)
    elif args.catalog_tree:
        if not args.level:
            sys.exit("--catalog-tree needs --level (department | category | subcategory | <number>)")
        want = LEVELS.get(args.level) or (int(args.level) if args.level.isdigit() else None)
        if not want:
            sys.exit("unknown --level %r" % args.level)
        urls = from_catalog(base, args.catalog_tree, want, auth_token() if args.auth else None)
    else:
        sys.exit("choose --catalog-tree DEPTH or --sitemap")

    unique = sorted(set(urls))
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write("\n".join(unique) + "\n")
    else:
        for u in unique:
            print(u)
    print("wrote %d unique URLs%s" % (len(unique), " to " + args.out if args.out else ""),
          file=sys.stderr)


if __name__ == "__main__":
    main()
