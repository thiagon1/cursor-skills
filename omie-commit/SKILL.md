---
name: omie-commit
description: >-
  Branch, commit and pull request standard for the OMIE project (Next.js +
  Strapi). Use when creating a branch, writing a git commit, or opening a PR in
  C:/projetos/omie: enforces feat/<descricao> branch naming, Conventional
  Commits with a rich context-first body, and the official OMIE PR template.
  Use whenever the user asks to commit, branch, open a PR, or "seguir o padrão do omie".
---

# OMIE — padrão de branch, commit e PR

Padrão de **branch**, **mensagem de commit** e **descrição de Pull Request** do projeto OMIE (`C:\projetos\omie`, Next.js `front/` + Strapi `cms/`). Use ao criar branch, commitar ou abrir PR neste repo.

## Quando usar

- "criar branch no omie", "commit no omie", "abrir PR no omie", "seguir o padrão do omie", "commitar isso"
- Sempre que estiver commitando ou abrindo PR dentro de `C:\projetos\omie`

---

## 1. Branch

Convenção: **`{tipo}/{descricao-kebab}`** — nunca `task{id}`.

| Tipo | Quando |
|---|---|
| `feat/` | nova feature/bloco/página |
| `fix/` | correção de bug |
| `refactor/` | refatoração sem mudança de comportamento |
| `chore/` | build, deps, config, tarefas de manutenção |
| `docs/` | documentação |
| `style/` | formatação/estilo sem lógica |

- `{descricao-kebab}`: resumo curto em **kebab-case**, em português, derivado do título da task.
- Exemplos reais do repo: `feat/blog-posts-per-page-36`, `fix/json-ld-author-url`, `feat/sitemap-paginas-autor`, `feat/seo-activities`, `fix/uploads-disk-rewrites`.

### Branch base
O repo tem várias branches de integração (`main`, `master`, `preview`, `develop`). **Confirmar com o usuário** de qual branch criar e para onde o PR vai (varia por fluxo/ambiente). Não assumir sozinho.

```
git checkout {base}
git pull
git checkout -b {tipo}/{descricao-kebab}
```

---

## 2. Commit — Conventional Commits + corpo rico

### Assunto (primeira linha)

```
{tipo}: {descrição no imperativo, em português}
```

- `{tipo}`: `feat`, `fix`, `refactor`, `chore`, `docs`, `style` (mesmos da branch).
- Assunto curto (~50–72 chars), imperativo, **sem ponto final**.
- **`[TASK-{id}]` é opcional**: quando o trabalho vem de uma task do Runrun.it, pode prefixar para rastreio — `[TASK-14793] feat: ...`. Sem task, usar só `{tipo}: ...`.

### Corpo (obrigatório para mudanças não triviais)

Linha em branco após o assunto, depois um corpo **explicando o CONTEXTO e o PORQUÊ**, não só o quê. Quebrar linhas ~72 colunas. Estrutura recomendada (em parágrafos, não precisa de títulos):

1. **Contexto / motivação** — o que originou a mudança (validação de time, bug reportado, ferramenta que acusou o erro, commit/preview de referência).
2. **Problema** — o que estava errado (com o dado concreto: valor antigo, mensagem de erro, etc.).
3. **Solução** — o que foi feito e **por que dessa forma** (reuso de helper, sem fetch extra, decisão de origem do dado).
4. **Casos de borda** — o que acontece quando falta dado, condição especial, fallback.
5. **Testes** — cobertura adicionada/alterada, se houver.

### Exemplo de referência (gold standard do time)

```
fix: adicionar author.url ao JSON-LD de BlogPosting

O time de SEO validou a correcao de posicionamento dos dados estruturados
(4e5880b, ja em master e no preview) e apontou um erro remanescente: o
Rich Results Test acusa "O campo 'url' nao foi encontrado" no author do
Article. Confirmado no preview: author saia como
{"@type":"Person","name":"Kaleu Florio"}, sem url.

O objeto author era hardcoded com @type e name apenas. Como Post ja
carrega authorSlug da relacao do Strapi, a URL sai sem fetch extra,
reusando buildBlogAuthorHref (mesmo helper do link da assinatura do
post), o que garante trailing slash + encoding e aponta para a canonica
da pagina de autor, evitando o redirect 308 de /blog/autor/.

A origem vem do proprio postUrl para nao divergir da URL do post
(getOrganizationUrl nao serve: devolve a url do Strapi com barra final).
Quando o post nao tem autor relacionado, a chave url e omitida, seguindo
o mesmo spread condicional que publisher ja usa.

Primeira cobertura de teste de structured-data.ts.
```

### Anti-padrões
- Assunto genérico ("ajustes", "update", "wip") — descreva a mudança real.
- Corpo ausente em mudança relevante — sempre explique o porquê.
- Misturar várias mudanças não relacionadas num commit — separar por assunto.

---

## 3. Como commitar (Windows / Cursor)

O `front/` usa **husky + lint-staged** (eslint + prettier nos arquivos staged no pre-commit). Deixe os hooks rodarem — eles formatam/validam o que está sendo commitado.

Por causa da injeção de `--trailer` do Cursor (falha em git < 2.32), escrever a mensagem em arquivo e commitar com `-F` via `git.exe`:

1. Escrever a mensagem em `.git/COMMIT_MSG_TEMP` (Write tool), com `Made-with: Cursor` como última linha.
2. Stage dos arquivos relevantes: `git add <arquivos>` (nunca `git add .` cego — conferir `git status`/`git diff`).
3. Commit:

```powershell
& "C:\Program Files\Git\bin\git.exe" commit -F .git\COMMIT_MSG_TEMP
```

- **NÃO usar `--no-verify` por padrão.** Só usar se o hook falhar por motivo espúrio (não relacionado à mudança) e após avisar o usuário — nunca para esconder erro de lint/tipo que o time deve corrigir.
- Se lint/prettier alterar arquivos no pre-commit, revisar o diff resultante e refazer o `git add` + commit.

---

## 4. Pull Request — template do omie

Ao abrir PR no repo omie, usar **exatamente** o template abaixo (Markdown completo). Preencher a descrição, **marcar** os checkboxes de tipo/áreas/checklist que se aplicam (`[x]`), anexar screenshots quando houver UI e só marcar itens do checklist que **de fato** foram verificados.

```markdown
# 📋 Pull Request

## 📝 Descrição

<!-- Descreva o que foi alterado e o motivo. Seja objetivo. -->

---

## 🏷️ Tipo de mudança

- [ ] ✨ `feat` — Nova funcionalidade
- [ ] 🐛 `fix` — Correção de bug
- [ ] 📚 `docs` — Alteração em documentação
- [ ] 🔧 `refactor` — Refatoração (sem mudança de comportamento)
- [ ] 💄 `style` — Ajuste de estilo (formato, lint, etc.)
- [ ] 🧹 `chore` — Manutenção, configuração, deps
- [ ] ⚡ `perf` — Melhoria de performance

---

## 📂 Áreas afetadas

- [ ] `front/` — Next.js (App Router, componentes, lib)
- [ ] `cms/` — Strapi (content-types, controllers, services)
- [ ] `docs/` — Documentação de arquitetura
- [ ] Outro: ___

---

## 🔗 Issue relacionada

<!-- Ex.: Fixes #123 ou Relacionado a #456 -->

---

## ✅ Checklist

### 🛠️ Build e Lint

- [ ] `cd front && npm run build` — passa sem erros
- [ ] `cd front && npm run lint` — passa sem warnings/erros
- [ ] `cd front && npm run typecheck` — passa sem erros
- [ ] `cd front && npm run test:contracts` — passa sem erros *(se alterou sections/populate)*
- [ ] `cd front && npm run audit:cms-populate` — passa sem erros *(se alterou sections/populate)*
- [ ] `cd cms && npm run build` — passa sem erros *(se alterou o CMS)*

### 💻 Código *(ver [IMPLEMENTATION-CHECKLIST.md](docs/IMPLEMENTATION-CHECKLIST.md))*

- [ ] Sem `any` em tipos/props
- [ ] Componentes só importam de `lib/*/client.ts` e `lib/*/types.ts` *(anti-corruption layer)*
- [ ] Sem `fetch` direto para Strapi em componentes
- [ ] URLs e tokens em variáveis de ambiente *(nunca hardcoded)*
- [ ] Sem `'use client'` desnecessário *(Server Component por padrão)*

### 🎨 Visual *(se houver alteração de UI)*

- [ ] Componentes consultam `site/design-system.html` e seguem os tokens
- [ ] Variáveis de cor utilizadas *(text-foreground, bg-ciano, etc.)* — sem hex direto
- [ ] Tailwind classes utilizadas *(sem `style` inline)*
- [ ] Responsivo testado *(mobile, tablet, desktop)*
- [ ] Screenshots ou GIFs anexados abaixo *(quando aplicável)*

### 🔌 Integração *(se houver nova API ou alteração em `lib/strapi/`)*

- [ ] Nova pasta em `lib/<nome>/` com client, types e transformers
- [ ] Timeout e tratamento de erro configurados
- [ ] Variáveis de ambiente documentadas em `.env.example`

---

## 📸 Screenshots / Preview

<!-- Anexe imagens ou GIFs quando houver mudanças visuais. -->

---

## 📌 Notas adicionais

<!-- Considerações para reviewers, breaking changes, migrações, etc. -->
```

### Regras de preenchimento

- **Tipo de mudança:** marcar o mesmo tipo do commit/branch (`feat`/`fix`/etc.).
- **Áreas afetadas:** marcar só o que o diff realmente toca (`front/`, `cms/`, `docs/`).
- **Checklist Build e Lint:** só marcar `[x]` os comandos que **rodou e passaram**. Rodar no mínimo `build`, `lint` e `typecheck` do `front/`; os condicionais só quando aplicável (alterou sections/populate → `test:contracts`/`audit:cms-populate`; alterou CMS → `cd cms && npm run build`).
- **Screenshots:** para mudança de UI, anexar imagens (hospedar via Cloudinary — ver `upload-image-cloudinary`/`runrunit-pr-commit`).
- **Issue/Task:** vincular a issue do GitHub e/ou a task do Runrun.it (`TASK-{id}`) quando houver.

### Criar o PR (gh)

```bash
git push -u origin HEAD

gh pr create --title "{tipo}: {descrição}" --body "$(cat <<'EOF'
{template preenchido acima}
EOF
)"
```

- Confirmar com o usuário a **branch base** do PR (o repo usa `main`/`master`/`preview`/`develop` conforme o fluxo).

---

## 5. Comentário no Runrun.it (deploy manual + hash do merge)

**Contexto do omie:** nada no repositório tem **deploy automático**. Todo deploy depende do **time da Omie**. O fluxo é:

1. Dev desenvolve e faz **merge na branch `master`**.
2. A Omie é avisada (**via John**) com o **hash do merge** para publicar.

Por isso, o comentário de entrega da task **precisa do hash do merge na `master`**. Sem o hash, a Omie não consegue subir.

### Como obter o hash do merge

Depois que o PR for mergeado na `master`:

```powershell
# Via GitHub (PR já mergeado):
gh pr view <pr_url_ou_numero> --json mergeCommit -q .mergeCommit.oid

# Ou localmente, após atualizar a master:
git checkout master ; git pull ; git log -1 --format=%H   # hash completo
git log -1 --format=%h                                     # hash curto (ex.: 4e5880b)
```

- Use o hash do **commit de merge na `master`** (não o da branch de feature).
- Pode usar o hash curto (7+ chars) no comentário; se a Omie pedir, passar o completo.

### Template do comentário (texto puro — Runrun.it não aceita Markdown)

```
Atualização TASK-{id} - {task title}

O que foi entregue:
- {bullet em linguagem de negócio 1}
- {bullet em linguagem de negócio 2}

Merge na master:
Hash: {merge_hash}
PR: {pr_url}

Deploy (importante):
Nada no repositorio tem deploy automatico. O deploy depende do time da Omie.
Fluxo: dev faz merge na master e avisamos a Omie (via John) com o hash do
merge acima para publicar em producao.

Como validar:
1) {passo objetivo — onde ir e o que conferir}
2) {passo}

Evidencias (prints):
{url_1}
{url_2}
```

- **Hash é obrigatório** para tasks do omie — é o que a Omie usa para publicar.
- Prints: hospedar via Cloudinary (`upload-image-cloudinary` / `runrunit_upload_image_cloudinary`) e colar a `secure_url` (uma por linha).
- Se ainda **não** houve merge na `master` (task só em review/preview), deixar claro no comentário que o merge/deploy está pendente e que o hash será enviado após o merge.

---

## 6. Integração

- **`runrunit-pr-commit`**: ao iniciar/entregar uma task do omie, usar **esta** skill para nome de branch (`feat/<descricao>`), mensagem de commit, **descrição do PR** (template do omie, em vez do genérico do Step F4) **e comentário no Runrun.it** (template com hash do merge acima, em vez dos Templates A/B genéricos). O restante do fluxo (upload de prints via Cloudinary, mover stage) segue a `runrunit-pr-commit`.
- Skills de implementação do omie: `component-creator`, `strapi-single-cpts`, `page-builder-section-mapper`, `section-performance-optimizer`, `frontend-performance`, `popup-form-template-creator`, `legacy-lp-*`.

## Regras

- Branch: `{tipo}/{descricao-kebab}`, nunca `task{id}`. Confirmar branch base.
- Commit: Conventional Commits com assunto em português + **corpo explicando o porquê** (contexto, problema, solução, casos de borda, testes).
- `[TASK-{id}]` no assunto é opcional (usar quando vier do Runrun.it).
- Commitar com `git.exe -F .git\COMMIT_MSG_TEMP`; deixar husky/lint-staged rodar; `--no-verify` só em falha espúria e com aviso.
- **PR:** usar o template oficial do omie (seção 4). Marcar só checkboxes verificados de fato; rodar build/lint/typecheck do `front/` antes de marcar. Confirmar a branch base do PR.
- **Comentário no Runrun.it:** usar o template da seção 5 com o **hash do merge na `master`** (obrigatório — a Omie publica manualmente com esse hash, avisada via John). Deploy nunca é automático.
