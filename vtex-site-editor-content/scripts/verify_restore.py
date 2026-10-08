"""Verify a restored workspace against the migration file. Read-only.

Fetches each entry's page from the target workspace and compares the content the
rendered page actually resolves at the NEW treePath against the migration file.
This is the render-side check; the restore script's read-back is the store-side check.
For a non-circular final proof, also spot-check a few pages against the LIVE
production text by hand.

  python3 verify_restore.py --workspace <ws> --file migration.json
"""

import argparse, gzip, io, json, re, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

from vtex_auth import auth_token

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36")
ENTRY = re.compile(r'\{"contentJSON":"((?:[^"\\]|\\.)*)","contentIds":\[([^\]]*)\],"treePath":"((?:[^"\\]|\\.)*)"\}')


def fetch(url, token, retries=4):
    last = None
    for attempt in range(retries):
        req = urllib.request.Request(url, headers={
            "User-Agent": UA, "Accept-Encoding": "gzip",
            "Cookie": "VtexIdclientAutCookie=%s" % token,
        })
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                raw = r.read()
                enc = r.headers.get("Content-Encoding")
            if enc == "gzip":
                raw = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
            return raw.decode("utf-8", "replace")
        except Exception as e:
            last = e
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("failed after %d attempts: %s" % (retries, last))


def rendered_content(html):
    html = html.replace("\\u002F", "/")
    out = {}
    for cjson, _ids, tp in ENTRY.findall(html):
        out[json.loads('"' + tp + '"')] = json.loads(json.loads('"' + cjson + '"'))
    return out


def check(entry, account, workspace, token):
    path = "/" + entry["url"].split("/", 3)[3]
    url = "https://%s--%s.myvtex.com%s" % (workspace, account, path)
    try:
        live = rendered_content(fetch(url, token))
    except Exception as e:
        return {"url": entry["url"], "status": "FETCH-ERROR", "detail": str(e)[:90]}

    problems = []
    for block in entry["blocks"]:
        want = block["content"]
        got = live.get(block["treePath"])
        if got is None:
            problems.append("%s: MISSING" % block["treePath"].rsplit("/", 1)[-1])
        elif got != want:
            problems.append("%s: differs (want %s, got %s)" % (
                block["treePath"].rsplit("/", 1)[-1],
                json.dumps(want)[:40], json.dumps(got)[:40]))
    return {"url": entry["url"], "status": "OK" if not problems else "MISMATCH",
            "detail": "; ".join(problems)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--file", required=True)
    args = ap.parse_args()

    data = json.load(open(args.file, encoding="utf-8-sig"))
    token = auth_token()
    entries = data["entries"]
    print("verifying %d pages against %s\n" % (len(entries), args.workspace))

    with ThreadPoolExecutor(max_workers=6) as ex:
        results = list(ex.map(lambda e: check(e, data["account"], args.workspace, token), entries))

    bad = [r for r in results if r["status"] != "OK"]
    for r in bad:
        print("  %-14s %-55s %s" % (r["status"], r["url"].rsplit("/", 1)[-1], r["detail"]))
    print("\n  OK       %d" % sum(1 for r in results if r["status"] == "OK"))
    print("  PROBLEMS %d" % len(bad))
    if bad:
        sys.exit(1)


if __name__ == "__main__":
    main()
