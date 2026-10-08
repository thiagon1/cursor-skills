/**
 * Read-only: fetch a storefront page and dump Site Editor content + matching extensions.
 *
 *   node extract-content.mjs <url> [--auth] [--out file.json] [--match a,b,c]
 *
 * --match: comma-separated substrings (treePath or blockId). Default: all saved entries.
 * --auth: attach `vtex local token` (required for private workspaces).
 */
import { execSync } from "node:child_process";
import { writeFileSync } from "node:fs";

const url = process.argv[2];
const wantAuth = process.argv.includes("--auth");
const out = process.argv.find((a, i, arr) => arr[i - 1] === "--out") || "extract.json";
const matchRaw = process.argv.find((a, i, arr) => arr[i - 1] === "--match");
const needles = (matchRaw || "")
  .split(",")
  .map((s) => s.trim().toLowerCase())
  .filter(Boolean);

if (!url || url.startsWith("--")) {
  console.error("usage: node extract-content.mjs <url> [--auth] [--out file.json] [--match foo,bar]");
  process.exit(1);
}

const UA_MOBILE =
  "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1";

function token() {
  const t = execSync("vtex local token", { encoding: "utf8" }).trim().split(/\r?\n/).pop();
  if (!t) throw new Error("empty vtex local token");
  return t;
}

function matches(tp, blockId) {
  if (!needles.length) return true;
  const s = `${tp} ${blockId || ""}`.toLowerCase();
  return needles.some((n) => s.includes(n));
}

async function fetchHtml(target, cookie) {
  const headers = { "User-Agent": UA_MOBILE, Accept: "text/html" };
  if (cookie) headers.Cookie = `VtexIdclientAutCookie=${cookie}`;
  const res = await fetch(target, { headers, redirect: "follow" });
  return { status: res.status, html: await res.text(), finalUrl: res.url };
}

function extract(html) {
  html = html.replace(/\\u002F/g, "/");
  const blockIds = {};
  const extRe = /"([^"]{3,400})":\{(?:[^{}]{0,400}?)"blockId":"([^"]+)"/g;
  let m;
  while ((m = extRe.exec(html))) blockIds[m[1]] = m[2];

  const entryRe =
    /\{"contentJSON":"((?:[^"\\]|\\.)*)","contentIds":\[([^\]]*)\],"treePath":"((?:[^"\\]|\\.)*)"\}/g;
  const saved = {};
  let total = 0;
  while ((m = entryRe.exec(html))) {
    total += 1;
    const ids = m[2]
      .split(",")
      .map((s) => s.trim().replace(/^"|"$/g, ""))
      .filter(Boolean);
    if (!ids.length) continue;
    const path = JSON.parse(`"${m[3]}"`);
    saved[path] = {
      contentIds: ids,
      blockId: blockIds[path] || null,
      content: JSON.parse(JSON.parse(`"${m[1]}"`)),
    };
  }

  const route = html.match(
    /"route":\{[^}]*"id":"([^"]+)"[^}]*"pageContext":\{"id":"([^"]+)","type":"([^"]+)"\}/
  );
  const binding = html.match(/"binding":\{"id":"([0-9a-f-]+)"/);
  const extensions = [];
  const extRe2 = /"([^"]{3,400})":\{(?:[^{}]{0,400}?)"blockId":"([^"]+)"/g;
  while ((m = extRe2.exec(html))) {
    if (matches(m[1], m[2])) extensions.push({ treePath: m[1], blockId: m[2] });
  }

  return {
    saved,
    total,
    extensions,
    route: route
      ? { template: route[1], pageContextId: route[2], pageContextType: route[3] }
      : null,
    bindingId: binding ? binding[1] : null,
  };
}

const cookie = wantAuth ? token() : null;
const { status, html, finalUrl } = await fetchHtml(url, cookie);
const data = extract(html);
const hits = Object.entries(data.saved)
  .filter(([tp, v]) => matches(tp, v.blockId))
  .map(([treePath, v]) => ({ treePath, ...v }));

const summary = {
  url,
  finalUrl,
  status,
  htmlBytes: html.length,
  route: data.route,
  bindingId: data.bindingId,
  blocksOnPage: data.total,
  match: needles,
  interestingSaved: hits,
  interestingExtensions: data.extensions,
};

writeFileSync(out, JSON.stringify(summary, null, 2), "utf8");
console.log(
  JSON.stringify(
    {
      status: summary.status,
      finalUrl: summary.finalUrl,
      route: summary.route,
      bindingId: summary.bindingId,
      blocksOnPage: summary.blocksOnPage,
      interestingCount: hits.length,
      extensionCount: data.extensions.length,
      treePaths: hits.map((h) => h.treePath),
      extensionTreePaths: data.extensions.map((e) => e.treePath),
      out,
    },
    null,
    2
  )
);
