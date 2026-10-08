---
name: vtex-site-editor-content
description: Backup, seed and migrate VTEX IO Site Editor (CMS) content via pages-graphql and the rendered-page content map. Use when Site Editor content disappeared after a block move/wrapper/rename (treePath change), when recadastrar conteúdo, when copying SEO/FAQ lists between production and a workspace, or when seeding Site Editor without clicking the admin UI. Do not use for FastStore, Headless CMS, catalog, or CSS.
---

# VTEX Site Editor content

Responder em **pt-BR**. Identifiers (`treePath`, `blockId`, `template`, `workspace`, `binding`) ficam em inglês, como a API espera.

O Site Editor grava conteúdo no **`treePath`** (cadeia de ids do template até o bloco), não só no `#id`. Isso vive **fora** do tema e **sobrescreve** as `props` do jsonc. O `schema.js` só descreve o formulário — **não contém** HTML/FAQ.

`updateThemeIds` (major do tema) **não** remapeia bloco antigo → wrapper novo. Mudou o parent = conteúdo órfão.

## Segurança

Conteúdo é **por workspace**. `vtex publish` / install **não** copia CMS.

| Destino | Afeta `www`? |
|---|---|
| Workspace de **dev** | Não |
| Workspace de **produção** (`{ws}--{conta}.myvtex.com`) | Não, até o **promote** |
| **`master`** | Sim, na hora; não dá para desfazer descartando o WS |

Ordem: prova no **dev** → restore no **WS de produção** (tema novo já instalado) → o usuário promove. Scripts recusam `--workspace master` sem `--allow-master`.

Backup na URL pública é **só leitura**. Restore **nunca** em `master` num teste.

## Pré-requisitos

```
vtex whoami
```

Tem que estar na **conta certa**. Workspace privado precisa de `--auth` (`vtex local token`).

- **Windows sem Python:** usar os scripts **Node** em `scripts/*.mjs` (Node 18+).
- **Com Python 3:** usar `scripts/*.py` — pipeline completo em [references/migration-pipeline.md](references/migration-pipeline.md).

Não commitar dumps (`prod-*.json`, `migration-*.json`) — têm HTML da loja.

## Três armadilhas da API

1. `template` **com** prefixo `vendor.app@MAJOR.x:store.search#subcategory`; `treePath` **sem** prefixo.
2. Diagnóstico = `listContentWithSchema` ou `__RUNTIME__` na página, não só o HTML visível. Saves levam ~30s.
3. Resposta de `saveContent` ≠ conteúdo visível. Sempre reler.

Contrato GraphQL: [references/pages-graphql-api.md](references/pages-graphql-api.md). Modelo: [references/content-model.md](references/content-model.md). Seed (página vazia, sem dado de cliente): [references/seeding.md](references/seeding.md).

## Qual modo

- **Seed** — template novo, ninguém cadastrou. → seeding.md + `seed_content.py`.
- **Migração de treePath** — wrapper, rename, re-nest. Cliente já cadastrou. → fluxo abaixo.

`schema.js` / colar JSON no jsonc **não** substitui o overlay do CMS. Jsonc só vale se o `treePath` novo **não** tiver entrada no Site Editor (nem um save vazio).

## Playbook rápido (1 página, Node) — o que validou na TASK-15081

Teste **page-scoped** numa URL. Outras páginas do WS ficam vazias de propósito (não grava wildcard de template).

1. Confirmar `vtex whoami` (conta + workspace de **dev** com o tema **novo**).
2. Extrair **produção** (estrutura antiga, conteúdo vivo):

```
node scripts/extract-content.mjs "https://www.loja.com/{path}" --out prod.json --match n1-search-page-text-seo,faq-categories,textSEO,conteudos-seo
```

3. Extrair o **workspace** (estrutura nova; `--auth`). `interestingSaved` pode ser 0; o que importa é `interestingExtensions` com os `treePath` novos:

```
node scripts/extract-content.mjs "https://{ws}--{conta}.myvtex.com/{path}" --auth --out ws.json --match n1-search-page-text-seo,faq-categories,textSEO,conteudos-seo
```

4. Mapear old → new pelo **último segmento** do `treePath` (`#instance`). Se o mesmo `#id` aparecer duas vezes (ex. tablet + bottom), `--prefer` o parent novo:

```
node scripts/build-migration.mjs --prod prod.json --ws ws.json --out migration.json --account {conta} --prefer conteudos-seo
```

`template` sai `vendor.theme@MAJOR.x:{route.template}`. `pageContext` sai da rota da página (`id` + `type`).

5. Dry-run no WS de dest (nunca `master`):

```
node scripts/restore-content.mjs --workspace {ws} --file migration.json
```

Esperado: `WOULD-CREATE` (ou `WOULD-UPDATE`), 0 `ERROR`.

6. `--apply`, esperar ~30s, reler o WS (`interestingCount` deve subir). Conferir Site Editor + vitrine desktop e mobile.

7. Re-rodar restore: tudo `SKIP`.

### Componentes com lista por ID (ex. SearchPageTextSEO)

Não é um HTML por URL. É **uma lista** (`department_seo_list` / `category_seo_list`) e o React escolhe pelo `pageContext.id`. O backup de **uma** PLP já traz a lista inteira. Restore **page-scoped** nessa URL basta para o teste; no go-live, ou repete por URL ou (com confirmação explícita) um save de **template** — o restore Node **recusa** `pageContext.id = "*"`.

FAQ accordion (`questions`) é **outro** bloco / outro `treePath`. Migrar junto se o match incluir o id.

## Pipeline completo (todas as páginas, Python)

Quando o conteúdo é **por URL** (não uma lista no bloco) e precisa cobrir o template inteiro: [references/migration-pipeline.md](references/migration-pipeline.md).

Resumo: `enumerate_pages.py` (árvore do catálogo completa) → `backup_content.py` na **produção antes** do tema novo ir para o alvo do crawl (UA mobile) → montar migration com `treePath` **novos** → dry-run / 1 página / arquivo no **dev** → só então WS de produção.

`backup_content.py --confirm-scope --account {conta}` confirma page vs template. Inference de scope só vale no conjunto **completo** de páginas do template.

## Workspace de produção vs master

Restore no WS de produção **funciona** igual ao de dev: o GraphQL usa `?workspace=`. Não publica no `www`. Só o **promote** leva CMS + tema para `master`. Não fazer A/B nesse WS enquanto o recadastro estiver incompleto.

## Checklist

- [ ] `vtex whoami` na conta certa
- [ ] Tema **novo** já renderiza os wrappers no WS de dest
- [ ] Backup de produção **antes** de o tema novo chegar no alvo do crawl
- [ ] `template` prefixado; `treePath` sem prefixo; `pageContext` concreto
- [ ] Dry-run 0 erro → apply 1 página → SKIP na segunda passagem
- [ ] Dumps fora do git
- [ ] Sem `--allow-master` a menos que o conteúdo em `master` já esteja perdido e o usuário pediu
