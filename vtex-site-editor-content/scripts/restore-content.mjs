/**
 * Restore Site Editor content into a workspace (never master unless --allow-master).
 * Dry-run by default. Pass --apply to write.
 *
 *   node restore-content.mjs --workspace task15081 --file migration.json
 *   node restore-content.mjs --workspace task15081 --file migration.json --apply
 */
import { execSync } from "node:child_process";
import { readFileSync } from "node:fs";

function arg(name) {
  const i = process.argv.indexOf("--" + name);
  return i >= 0 ? process.argv[i + 1] : undefined;
}

const file = arg("file");
const workspace = arg("workspace");
const apply = process.argv.includes("--apply");
const allowMaster = process.argv.includes("--allow-master");
const lang = arg("lang") || "pt-BR";

if (!file || !workspace) {
  console.error("usage: node restore-content.mjs --workspace <ws> --file migration.json [--apply]");
  process.exit(1);
}
if (workspace === "master" && !allowMaster) {
  console.error("refusing to write to master — prove it in a workspace, then a production workspace, then promote");
  process.exit(1);
}

const data = JSON.parse(readFileSync(file, "utf8"));
for (const key of ["account", "bindingId", "template", "entries"]) {
  if (!data[key]) throw new Error("missing " + key);
}
if (!data.template.includes(":")) throw new Error("template must be app-prefixed");

function token() {
  return execSync("vtex local token", { encoding: "utf8" }).trim().split(/\r?\n/).pop();
}

const SENDER = "vtex.admin-pages@4.59.2";
const PROVIDER = "vtex.pages-graphql@2.x";
const LIST_Q = `query ListContent($bindingId: String, $blockId: String, $pageContext: PageContextInput, $template: String, $treePath: String) @context(sender: "${SENDER}") {
  listContentWithSchema(bindingId: $bindingId, blockId: $blockId, pageContext: $pageContext, template: $template, treePath: $treePath) {
    content { contentId contentJSON condition { pageContext { id type } } }
  }
}`;
const SAVE_M = `mutation saveContent($bindingId: String, $blockId: String, $configuration: ContentConfigurationInput, $template: String, $treePath: String, $lang: String) @context(sender: "${SENDER}") {
  saveContent(bindingId: $bindingId, blockId: $blockId, configuration: $configuration, template: $template, treePath: $treePath, lang: $lang) { contentId }
}`;

async function gql(tok, query, variables) {
  const ext = encodeURIComponent(
    JSON.stringify({ persistedQuery: { provider: PROVIDER, sender: SENDER } })
  );
  const url =
    `https://${data.account}.myvtex.com/_v/private/graphql/v1?workspace=${workspace}` +
    `&maxAge=short&appsEtag=remove&domain=admin&locale=pt-BR&extensions=${ext}`;
  const res = await fetch(url, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      cookie: `VtexIdclientAutCookie=${tok}`,
    },
    body: JSON.stringify({ query, variables }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const payload = await res.json();
  if (payload.errors) throw new Error(payload.errors[0].message);
  return payload.data;
}

function pageEntry(entries, ctxId) {
  return (entries || []).find((e) => e.condition?.pageContext?.id === ctxId) || null;
}

const tok = token();
const jobs = data.entries.flatMap((p) => p.blocks.map((b) => ({ p, b })));
for (const { p, b } of jobs) {
  if (b.treePath.split("/")[0].includes(":")) throw new Error("prefixed treePath " + b.treePath);
  if (["*", "", null, undefined].includes(p.pageContext?.id)) {
    throw new Error("wildcard pageContext for " + p.url);
  }
}

console.log(`${apply ? "APPLY" : "DRY RUN"} | ${data.account} ${workspace} | ${jobs.length} blocks\n`);
const counts = {};

for (const [i, { p, b }] of jobs.entries()) {
  const label = `${p.url.split("/").pop()} | ${b.treePath.split("/").pop()}`;
  const common = {
    bindingId: data.bindingId,
    blockId: b.blockId,
    template: data.template,
    treePath: b.treePath,
  };
  const ctx = p.pageContext;
  let action;
  let detail = "";
  try {
    const listed = await gql(tok, LIST_Q, { ...common, pageContext: ctx });
    const current = listed.listContentWithSchema.content;
    const existing = pageEntry(current, ctx.id);
    const wanted = b.content;
    if (existing && JSON.stringify(JSON.parse(existing.contentJSON)) === JSON.stringify(wanted)) {
      action = "SKIP";
      detail = "already restored";
    } else {
      action = existing ? "UPDATE" : "CREATE";
      if (apply) {
        const cfg = {
          status: "ACTIVE",
          condition: { allMatches: true, id: "", pageContext: ctx, statements: [] },
          contentId: existing ? existing.contentId : null,
          contentJSON: JSON.stringify(wanted),
          label: null,
          origin: null,
        };
        await gql(tok, SAVE_M, { ...common, configuration: cfg, lang });
        await new Promise((r) => setTimeout(r, 1500));
        const after = await gql(tok, LIST_Q, { ...common, pageContext: ctx });
        const saved = pageEntry(after.listContentWithSchema.content, ctx.id);
        if (!(saved && JSON.stringify(JSON.parse(saved.contentJSON)) === JSON.stringify(wanted))) {
          action = "VERIFY-FAILED";
        }
      } else {
        action = "WOULD-" + action;
      }
    }
  } catch (e) {
    action = "ERROR";
    detail = String(e.message || e).slice(0, 180);
  }
  counts[action] = (counts[action] || 0) + 1;
  console.log(`  [${i + 1}/${jobs.length}] ${action.padEnd(13)} ${label}${detail ? " | " + detail : ""}`);
}

console.log("\nsummary:");
for (const k of Object.keys(counts).sort()) console.log(`  ${k.padEnd(15)} ${counts[k]}`);
if (!apply) console.log("\nno changes written — re-run with --apply");
if (Object.keys(counts).some((k) => k.startsWith("ERROR") || k.startsWith("VERIFY"))) process.exit(1);
