/**
 * Map production saved content onto new workspace treePaths (same block instance id).
 *
 *   node build-migration.mjs --prod prod.json --ws ws.json --out migration.json --account lojamm [--prefer conteudos-seo] [--theme-prefix lojamm.store-theme@10.x]
 */
import { readFileSync, writeFileSync } from "node:fs";

function arg(name, fallback) {
  const i = process.argv.indexOf("--" + name);
  return i >= 0 ? process.argv[i + 1] : fallback;
}

const prodPath = arg("prod");
const wsPath = arg("ws");
const out = arg("out", "migration.json");
const account = arg("account");
const prefer = arg("prefer", "");
const themePrefix = arg("theme-prefix", "");

if (!prodPath || !wsPath || !account) {
  console.error(
    "usage: node build-migration.mjs --prod prod.json --ws ws.json --out migration.json --account lojamm [--prefer conteudos-seo] [--theme-prefix vendor.theme@10.x]"
  );
  process.exit(1);
}

const prod = JSON.parse(readFileSync(prodPath, "utf8"));
const ws = JSON.parse(readFileSync(wsPath, "utf8"));

const wsByLast = {};
for (const e of ws.interestingExtensions || []) {
  const last = e.treePath.split("/").pop();
  if (!wsByLast[last] || (prefer && e.treePath.includes(prefer))) {
    wsByLast[last] = e;
  }
}

const blocks = [];
for (const h of prod.interestingSaved || []) {
  const last = h.treePath.split("/").pop();
  const neu = wsByLast[last];
  if (!neu) {
    console.error("NO NEW PATH for", last);
    continue;
  }
  if (h.treePath === neu.treePath) {
    console.error("PATH UNCHANGED, skip", last);
    continue;
  }
  blocks.push({
    treePath: neu.treePath,
    blockId: h.blockId || neu.blockId,
    content: { ...h.content },
    source: { oldTreePath: h.treePath, contentIds: h.contentIds },
  });
}

const prefix =
  themePrefix ||
  (blocks[0]?.blockId || "").split(":")[0] ||
  "";
if (!prefix) {
  console.error("could not infer --theme-prefix from blockId");
  process.exit(1);
}

const templateName = prod.route?.template;
if (!templateName) {
  console.error("prod extract missing route.template");
  process.exit(1);
}

const migration = {
  account,
  bindingId: prod.bindingId,
  template: `${prefix}:${templateName}`,
  generatedAt: new Date().toISOString().slice(0, 10),
  notes: "treePath remap; restore into a non-master workspace first",
  entries: [
    {
      url: prod.url,
      pageContext: {
        id: prod.route.pageContextId,
        type: prod.route.pageContextType,
      },
      blocks,
    },
  ],
};

writeFileSync(out, JSON.stringify(migration, null, 2), "utf8");
console.log("blocks", blocks.length, "->", out);
for (const b of blocks) console.log("-", b.treePath.split("/").pop());
