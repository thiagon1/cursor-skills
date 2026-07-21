---
name: runrunit-pr-commit
description: Full task lifecycle via Runrun.it — start tasks (fetch data, create branch, plan execution), develop with deco.cx/VTEX skills, and finish (commit, PR, comment, deliver). Use when the user provides a Runrun.it task link and wants to start, develop, commit, open a PR, or document a task.
---

# Runrun.it — Task Lifecycle (Start → Develop → Finish)

Two main flows:

- **Flow A — Start Task:** fetch task data, verify workspace, create branch, analyze requirements, plan execution
- **Flow B — Finish Task:** create commits, open PR, comment on task, deliver

## Input

| Campo | Obrigatório | Descrição |
|-------|-------------|-----------|
| **Link da task** | Sim | URL da tarefa (ex.: `https://runrun.it/en-US/tasks/14003`) ou ID numérico |
| **URLs antes/depois** | Não | Para evidências visuais no PR e na task (Flow B, Template A) |
| **Branch destino** | Não | Padrão: `development` |
| **Link da PR** | Não | URL da Pull Request (Bitbucket ou GitHub). Se não fornecido, é criado no Step F4. |
| **Link do workspace** | Não | URL de validação (ex.: `https://task14002--lojamm.myvtex.com/lancamentos`) |
| **Links extras** | Não | GTM, Figma, documentos ou qualquer link adicional relevante |
| **Prints/evidências** | Não | URLs de screenshots (prnt.sc, Cloudinary, etc.) |
| **Descrição da entrega** | Não | O que foi entregue, em linguagem de negócio. Se não fornecido, é derivado da task. |
| **Produção — tema/app novo** | Não | URL do **Admin** da versão **em produção** (setup), ex.: `https://{conta}.myvtex.com/admin/apps/{vendor}.{app}@{versao}/setup` |
| **Produção — tema/app anterior** | Não | URL do setup da versão **anterior** (referência para comparação ou rollback) |
| **Conta VTEX (para montar URL)** | Não | Ex.: `leeloo` — use quando souber `vendor.app@ver` mas faltar o host completo |

---

# Flow A — Start Task (Iniciar tarefa)

Triggered when the user says "iniciar tarefa", "começar task", "pega essa task", or provides a Runrun.it link asking to start work.

## Step A1 — Fetch task data from Runrun.it

Extract the numeric ID from the URL (e.g. `.../tasks/14003` → `14003`).

Call `runrunit_get_task` via MCP:

```
server: user-runrunit-mcp
toolName: runrunit_get_task
arguments: { "id": <task_id> }
```

From the response, extract:
- `title` — task title
- `id` — task ID
- `project_id` / `project_name` — project context (used to identify the correct workspace)
- `responsible_name` — assigned developer
- `tags` — tags to determine change type and technology
- `description` — detailed requirements
- `board_stage_name` — current stage

Also fetch comments and subtasks for full context:

```
server: user-runrunit-mcp
toolName: runrunit_list_task_comments
arguments: { "task_id": <task_id> }
```

```
server: user-runrunit-mcp
toolName: runrunit_list_subtasks
arguments: { "task_id": <task_id> }
```

## Step A2 — Verify workspace / project folder

Before creating a branch, confirm the user is in the correct project folder.

1. Check the current working directory (`pwd` or workspace path from Cursor context).
2. Cross-reference with the `project_name` from the task to identify the expected repository.
3. Look for project indicators: `manifest.json` (VTEX IO), `deno.json`/`mod.ts` (deco.cx), `package.json`, `.git` folder.

**If the workspace looks wrong:**
- STOP and ask the user: "O workspace atual é `{cwd}`, mas a task é do projeto `{project_name}`. Deseja continuar aqui ou trocar para outro diretório?"
- Do NOT proceed until the user confirms.

**If the workspace looks correct:**
- Inform the user: "Workspace confirmado: `{cwd}` ({project_name})"

## Step A3 — Create or checkout branch

### Branch naming convention (POR PROJETO)

O padrão de branch **depende do repositório**. Detecte o projeto (pelo `project_name` da task, pelo `git remote -v` ou pela pasta) e use a convenção certa. Chame o nome final de `{branch}`:

| Projeto / repo | Convenção | Exemplo |
|---|---|---|
| Padrão (VTEX IO, deco.cx, geral) | `task{id}` | `task14003` |
| **omie** (Next.js + Strapi — `C:\projetos\omie`) | `{tipo}/{descricao-kebab}` — **NÃO** usar `task{id}` (ver skill `omie-commit`) | `feat/blog-page`, `feat/new-home-blog`, `fix/popup-form` |

- No padrão `{tipo}/{descricao}`: `{tipo}` segue conventional commits (`feat`, `fix`, `refactor`, `docs`, `style`, `chore`) e `{descricao}` é um resumo curto em **kebab-case** derivado do título da task.
- Ao detectar o repositório **omie**, confirmar o nome com o usuário: "Projeto omie usa `{tipo}/<descricao>`. Sugiro `feat/{descricao}` (da task '{title}'). Confirma esse nome ou prefere outro?"
- Se não tiver certeza da convenção ou da descrição, **perguntar ao usuário** antes de criar a branch.

### Passos

1. Run `git status` to check for uncommitted changes.
   - If there are uncommitted changes, STOP and ask: "Existem alterações não commitadas na branch atual. Deseja fazer stash, commit ou descartar antes de trocar?"
   - Wait for user confirmation before proceeding.

2. Definir `{branch}` conforme a convenção do projeto (tabela acima) e checar se já existe:
   ```
   git branch --list {branch}
   git branch -r --list "*/{branch}"
   ```

3. **If branch exists locally:** ask the user: "A branch `{branch}` já existe. Deseja fazer checkout para ela?"
   - On confirmation: `git checkout {branch}`

4. **If branch exists only on remote:** ask: "A branch `{branch}` existe no remoto. Deseja fazer checkout?"
   - On confirmation: `git checkout -b {branch} origin/{branch}`

5. **If branch does not exist:** ask: "Vou criar a branch `{branch}` a partir de `{current_branch}`. Confirma?"
   - The base branch should typically be `development` or `main` — ask if unclear.
   - On confirmation: `git checkout -b {branch} {base_branch}`

6. Confirm to the user: "Branch `{branch}` pronta. Trabalhando a partir de `{base_branch}`."

## Step A4 — Analyze task and identify technology / skills

Parse the task `title`, `description`, `tags`, and `comments` to determine:

### Technology detection

| Signal in task data | Technology | Relevant skills |
|---|---|---|
| `vtex`, `vtex io`, `store-theme`, `site editor`, `shelf`, `checkout` | VTEX IO | `vtex-io-component`, `vtex-css`, `vtex-io-node-graphql`, `vtex-checkout`, `vtex-checkout-config` |
| `css`, `estilo`, `style`, `layout`, `handle`, `seletor`, `tema`, `cor`, `responsiv` (em projeto VTEX) | VTEX IO CSS | `vtex-css` (+ `vtex-io-component` se criar componente) |
| `deco`, `deco.cx`, `fresh`, `section`, `loader`, `island` | deco.cx | `deco-section`, `deco-loader`, `deco-island`, `deco-app`, `deco-vtex` |
| `checkout`, `orderForm`, `checkout6-custom` | VTEX Checkout | `vtex-checkout`, `vtex-checkout-config` |
| `graphql`, `node`, `resolver`, `client`, `middleware` | VTEX IO Node/GraphQL | `vtex-io-node-graphql` |
| link do **Figma** (`figma.com/design/...`), `design`, `layout no figma`, `protótipo`, `mockup` | Design/Figma | `figma-assets` (+ skill de implementação da stack) |
| **omie** (projeto `C:\projetos\omie`), `next.js`/`nextjs`, `strapi`, `cms`, `page builder`/`section`, `landing page`/`LP`, `blog`, `popup`, `component`/`componente`, `TBT`/`performance`/`pagespeed` | omie (Next.js + Strapi) | Skills **do projeto omie** (project-scoped): `component-creator`, `strapi-single-cpts`, `page-builder-section-mapper`, `section-performance-optimizer`, `frontend-performance`, `popup-form-template-creator`, `legacy-lp-text-sync`, `legacy-lp-css-background-sync`, `legacy-lp-section-precos` |

**Regra:** em qualquer tarefa da **plataforma VTEX (VTEX IO)** que envolva CSS/estilo/layout/CSS Handles, **sempre** incluir a skill **`vtex-css`** no plano (Step A5) e lê-la antes de editar CSS.

**Regra (Figma):** se a task tiver um **link do Figma** (na descrição, comentários ou enviado pelo usuário), incluir a skill **`figma-assets`** no plano e usá-la para extrair design, tipografia/espaçamentos exatos e assets (SVG/imagens) antes de implementar.

**Regra (omie):** quando o repositório for o **omie** (`C:\projetos\omie`, stack Next.js + Strapi), as skills relevantes são **project-scoped** e ficam em `C:\projetos\omie\.cursor\skills\{skill}\SKILL.md` (o Cursor as carrega automaticamente ao trabalhar nesse repo). Incluir a(s) skill(s) apropriada(s) no plano (Step A5) e **ler antes de executar**. Para **branch e commit**, seguir a skill **`omie-commit`**: branch `feat/<descricao>` (ver Step A3, **não** `task{id}`) e commit Conventional Commits com corpo detalhado (contexto/porquê).

### Task type detection

| Signal | Type | Approach |
|---|---|---|
| `criar`, `novo`, `adicionar`, `implementar` | New feature | Create new files/components |
| `ajustar`, `corrigir`, `fix`, `bug` | Fix/adjustment | Find and modify existing code |
| `alterar`, `mudar`, `atualizar`, `layout` | Update | Modify existing components |
| `configurar`, `config`, `setup` | Configuration | Update config files, settings |

### Codebase exploration

Before presenting the plan, explore the project structure to understand what already exists:
1. List key directories (`ls`, `Glob`) to map the project layout.
2. If VTEX IO: check `manifest.json` for app name/version, `store/` for blocks, `react/` for components.
3. If deco.cx: check `deno.json`, `sections/`, `loaders/`, `islands/`, `apps/`.
4. Search for files related to the task (e.g., if task mentions "shelf", search for shelf-related components).

## Step A5 — Present plan and ask for permission

**CRITICAL: NEVER start coding without user approval.**

Present a structured plan to the user:

```
Tarefa: TASK-{id} — {title}
Projeto: {project_name}
Branch: task{id}
Tecnologia: {detected technology}

Plano de execução:
1. {Step 1 — what will be created/modified and why}
2. {Step 2 — ...}
3. {Step 3 — ...}

Arquivos que serão criados:
- {path/to/new/file.tsx} — {brief description}

Arquivos que serão modificados:
- {path/to/existing/file.tsx} — {what changes}

Skills que serão utilizadas:
- {skill name} — {why}

Posso prosseguir com esse plano?
```

Wait for the user to confirm, adjust, or reject the plan.

## Step A6 — Execute task with appropriate skills

After user approval, execute the plan step by step:

1. **Read the relevant skill** before starting (e.g., `deco-section`, `vtex-io-component`, `vtex-css` para CSS/estilo em VTEX IO, `figma-assets` quando houver link do Figma).
2. **Follow the skill instructions** to create/modify files.
3. **After each significant change**, briefly inform the user what was done.
4. **Before creating new files:** confirm with the user ("Vou criar o arquivo `{path}`. OK?").
5. **Before deleting files or code:** ALWAYS ask ("Preciso remover `{path/code}`. Posso prosseguir?").
6. **If the task is ambiguous** at any point, stop and ask for clarification.

### Permission rules during execution

| Action | Permission required? |
|---|---|
| Read/search files | No |
| Modify existing file (small change) | No (inform after) |
| Modify existing file (large refactor) | Yes — ask before |
| Create new file | Yes — ask before |
| Delete file | **Always** — ask before |
| Delete code block | **Always** — ask before |
| Install dependency | Yes — ask before |
| Change config files | Yes — ask before |

## Step A7 (optional) — Move task stage on Runrun.it

If the user asks, move the task to "In Progress" or the appropriate stage:

```
server: user-runrunit-mcp
toolName: runrunit_move_task_stage
arguments: { "task_id": <task_id>, "board_stage_name": "In Progress" }
```

---

# Flow B — Finish Task (Finalizar tarefa)

Triggered when the user says "faz commit", "abre PR", "entrega a task", "comenta na task", or any finish-related action. Steps are numbered F1–F6 to distinguish from Flow A.

## Step F1 — Fetch task data from Runrun.it

Extract the numeric ID from the URL (e.g. `.../tasks/13631` → `13631`).

Call `runrunit_get_task` via MCP:

```
server: user-runrunit-mcp
toolName: runrunit_get_task
arguments: { "id": <task_id> }
```

From the response, extract:
- `title` — task title (used for PR title and commit message)
- `id` — task ID (used for references)
- `project_id` / `project_name` — project context
- `responsible_name` — assigned developer
- `tags` — tags to determine change type
- `description` — detailed requirements (useful for PR description)
- `board_stage_name` — current stage

Also fetch comments for extra context:

```
server: user-runrunit-mcp
toolName: runrunit_list_task_comments
arguments: { "task_id": <task_id> }
```

## Step F2 — Determine change type

Map the task info to one of the PR change types:

| Tag / Keyword in title | Type |
|---|---|
| `bug`, `fix`, `correção` | 🐛 Correção de bug |
| `feature`, `novo`, `criar`, `adicionar` | ✨ Novo recurso |
| `refactor`, `refatoração`, `melhoria` | ♻️ Refatoração |
| `doc`, `documentação` | 📖 Documentação |
| `layout`, `css`, `estilo`, `visual`, `ajust` | 🎨 Alteração de layout |

If ambiguous, ask the user or default to 🎨 Alteração de layout.

## Step F3 — Create semantic commits

### Commit message format

Formato padrão (qualquer stack):

```
[TASK-{id}] {type}: {short description}

{optional body with more details}
```

**Formato VTEX IO (theme / app publicável) — a linha `Release:` vai no INÍCIO, antes do assunto:**

```
Release: {vendor}.{name}@{version}

[TASK-{id}] {type}: {short description}

{optional body with more details}
```

Where `{type}` follows conventional commits:
- `fix:` for bug fixes
- `feat:` for new features
- `refactor:` for refactoring
- `docs:` for documentation
- `style:` for layout/visual changes

### Example (VTEX IO — ajuste/homolog, SEM mudar versão)

```
[TASK-13631] style: adjust mobile shelf/search with sizes

Updated shelf and search layouts for mobile viewport
to properly display product size variations.
```

### Example (VTEX IO — commit de PRODUÇÃO, com bump confirmado)

```
Release: store.theme-mm@3.5.12

[TASK-13631] style: adjust mobile shelf/search with sizes

Updated shelf and search layouts for mobile viewport
to properly display product size variations.
```

### Example (não-VTEX IO, ex.: deco.cx)

```
[TASK-13631] style: adjust mobile shelf/search with sizes

Updated shelf and search layouts for mobile viewport
to properly display product size variations.
```

### VTEX IO — versão e release (themes / apps da loja)

Quando o repositório for um app **VTEX IO** (raiz com `manifest.json` contendo `vendor`, `name`, `version` e `builders`), ao preparar o commit de entrega de task:

1. **Detectar** o app: `{vendor}.{name}` e a versão atual em `"version"` (semver `x.y.z`).
2. **NÃO subir a versão em qualquer ajuste.** Durante o desenvolvimento/ajustes/homolog (commits de branch, workspace de teste), **manter a `version` do `manifest.json` como está**. Commits comuns da task **não** alteram o `manifest.json` nem levam linha `Release:`.
3. **Só alterar a versão quando for para PRODUÇÃO** (publicação do tema/app na conta principal — `vtex publish`/deploy). Só nesse momento se faz o bump no `manifest.json`.
4. **Ao ir para produção, SEMPRE perguntar ao usuário qual incremento** (não decidir sozinho): patch, minor ou major.

   Pergunte assim (sugerindo uma opção com base na mudança, mas aguardando confirmação):

   ```
   Vou publicar {vendor}.{name} (versão atual {x.y.z}).
   Qual incremento de versão?
   - patch → {x.y.(z+1)}  (correções, ajustes de layout/CSS)
   - minor → {x.(y+1).0}  (novas features/blocos compatíveis)
   - major → {(x+1).0.0}  (breaking changes)
   ```

   - **patch**: correções, ajustes de layout/CSS, pequenas correções.
   - **minor**: novas features ou blocos visíveis, mudanças compatíveis.
   - **major**: breaking changes.

   Só aplicar o bump depois da resposta do usuário.
5. **`CHANGELOG.md`:** se existir no repo, acrescentar entrada com **TASK-{id}**, resumo da mudança e o número da nova versão **apenas no commit de release/produção** (seguir o padrão já usado no arquivo).
6. **Linha `Release:` só no commit de produção.** Quando o bump acontecer, a linha `Release:` é a **primeira linha** da mensagem (vem **antes** do `[TASK-…]`), seguida de uma linha em branco e depois o assunto/corpo:

   ```
   Release: {vendor}.{name}@{version}

   [TASK-{id}] {type}: {short description}
   ```

   Exemplo: `Release: store.theme-mm@3.5.12` (use a versão **nova** confirmada e já refletida no `manifest.json`). Não usar a linha `Release:` como rodapé/trailer — neste fluxo ela é o **início** da mensagem. Em commits que **não** são de produção, **não** incluir a linha `Release:`.
7. **Staging (commit de produção):** incluir `manifest.json` (e `CHANGELOG.md` se alterado) **no mesmo commit** do release.
8. **Monorepo / vários apps:** aplicar bump e linha `Release` apenas no(s) app(s) que vão para produção; se o mesmo release tocar **dois** apps publicáveis, usar duas linhas `Release:` no topo, uma por app.

**Resumo:** ajuste/homolog = sem mudar versão e sem `Release:`. Produção = perguntar o incremento (patch/minor/major), fazer o bump no `manifest.json` e usar a linha `Release:` no topo do commit.

### How to commit

1. Run `git status` and `git diff` to understand changes
2. Run `git log --oneline -5` to follow existing commit style
3. Stage relevant files: `git add <files>`
4. Write the commit message to a temp file, then commit with `-F`:

```powershell
# Write message to temp file (use the Write tool to create .git/COMMIT_MSG_TEMP)
# Then commit using git.exe directly to bypass Cursor --trailer injection:
& "C:\Program Files\Git\bin\git.exe" commit -F .git\COMMIT_MSG_TEMP
```

**IMPORTANT — Cursor `--trailer` workaround:**
Cursor automatically injects `--trailer 'Made-with: Cursor'` into every `git commit` call.
Git versions older than 2.32 do NOT support `--trailer` and will fail with `error: unknown option 'trailer'`.

To work around this:
1. Write the commit message to `.git/COMMIT_MSG_TEMP` using the Write tool
2. Append `Made-with: Cursor` as the last line of the message (as a manual trailer)
3. Call `git.exe` directly via its full path to bypass Cursor's wrapper:
   `& "C:\Program Files\Git\bin\git.exe" commit -F .git\COMMIT_MSG_TEMP`
4. If the full path doesn't work, try: `cmd /c "git.exe commit -F .git\COMMIT_MSG_TEMP"`
5. If hooks (lint, etc.) block the commit in projetos **sem** a exceção abaixo, use `commit ... --no-verify` **only** when the failure is from hooks, not the trailer (never use `--no-verify` to hide real errors the user should fix in VTEX/Node projects unless agreed).

**deco.cx — loja / projeto VFOR (e projetos Deco equivalentes):** nos commits deste contexto, use **quase sempre** `--no-verify` com o `git.exe` e `-F` acima, porque os *hooks* do repositório (Deno, fmt, checagens longas) costumam atrapalhar o fluxo de tarefa no agente. Comando padrão:

```powershell
& "C:\Program Files\Git\bin\git.exe" commit -F .git\COMMIT_MSG_TEMP --no-verify
```

- Confirme com o usuário o workspace: `deno.json` / `mod.ts` + repositório da loja Deco **VFOR** = aplicar o padrão.
- Não use `--no-verify` por padrão em repositórios **VTEX IO** (store theme, apps) ou outros se o time exigir hooks — a regra geral de hook failure acima continua.

This applies to ALL git commit operations in this skill (commit, amend, etc.) — ajuste `--no-verify` conforme a stack do repositório aberto.

## Step F4 — Open GitHub PR

### PR title format

```
[{Project Name}] {task title}
```

Example: `[Clovis B2C] vitrine/pesquisa mobile com numerações`

### PR body template

Use this exact template, filling in data from the task:

```markdown
# Título do PR: [{Project Name}] {task title}

## 🎯 Tipo de Mudança

> Marque o tipo de mudança que este PR introduz

- [{x or space}] 🐛 **Correção de bug** (alteração que corrige um problema)
- [{x or space}] ✨ **Novo recurso** (alteração que adiciona uma funcionalidade)
- [{x or space}] ♻️ **Refatoração** (uma alteração de código que não corrige um bug nem adiciona um recurso)
- [{x or space}] 📖 **Documentação** (atualizações na documentação)
- [{x or space}] 🎨 Alteração de layout (Mudança no layout sem alterar o comportamento de uma funcionalidade existente)

---

## 📝 Descrição

> {Description derived from task title, description, and comments. Summarize what was done.}

---

## 📸 Evidências Visuais (Se aplicável)

> Adicione capturas de tela, GIFs ou vídeos para demonstrar as mudanças de UI/UX.

**Antes:**
![Antes]({before_screenshot_url or empty})

**Depois:**
![Depois]({after_screenshot_url or empty})

---

## ✅ Checklist de Qualidade

- [x] Meu código segue as diretrizes deste projeto.
- [x] Realizei uma revisão do meu próprio código.
- [ ] Testei o fluxo de navegação.
- [ ] Comentei meu código nas áreas de difícil compreensão.
- [x] Minhas alterações não geram novos warnings.

---

## 🔗 Referências

> Adicione links para tarefas, épicos ou outras referências.

- **Tarefa:** [TASK-{id}](https://runrun.it/en-US/tasks/{id})
- **Versão publicável (VTEX IO):** `{vendor}.{name}@{version}` — usar a mesma versão do `manifest.json` deste PR (se aplicável)
- **Design no Figma:** [Link para o design]({figma_url or "https://..."})
- **Documento:** [Link]({doc_url or "https://..."})
```

### Create the PR

```bash
git push -u origin HEAD

gh pr create --title "[{Project}] {task title}" --body "$(cat <<'EOF'
{filled template above}
EOF
)"
```

Return the PR URL to the user.

## Step F5 — Update task on Runrun.it

### Save PR link in the task

```
server: user-runrunit-mcp
toolName: runrunit_update_task
arguments: { "id": <task_id>, "task": { "link_da_branch": "<pr_url>" } }
```

### Post comment on the task

```
server: user-runrunit-mcp
toolName: runrunit_create_comment
arguments: {
  "task_id": <task_id>,
  "text": "<comment text>"
}
```

Choose the comment template based on context:

#### Template A — Comentário técnico (default para evidências antes/depois)

Use when the user provides before/after URLs and the focus is on visual evidence of changes.

```
Resumo do que foi feito:
{Summary of changes based on commit messages and PR description}

Link da PR: {pr_url}

Passo a passo para testar:
1. Acesse {test_url or workspace URL}
2. {Step to reproduce/validate}
3. {What to check}

Evidências:
Antes (Desktop): {url}
Depois (Desktop): {url}
Antes (Mobile): {url}
Depois (Mobile): {url}
```

#### Template B — Comentário de entrega (handoff para validação)

Use when the user finishes a task and wants to document what was delivered, provide validation links (workspace, GTM, etc.), explain how to validate, attach evidence prints, **or document theme/app versions live in production (VTEX Admin setup URLs)**. This is the preferred template when the user says "comenta na task", "entrega", "passa pra validação", "foi pra produção", or provides PR + prints + workspace links.

```
Atualização TASK-{id} - {task title}

O que foi entregue:
- {Bullet point describing deliverable 1 in business language, not technical jargon}
- {Bullet point describing deliverable 2}
- {Add as many bullets as needed}

Links:
- Pull Request (revisão do código): {pr_url}
- Ambiente de validação (workspace): {workspace_url}
{Include any extra links the user provides, e.g.:}
- GTM: {gtm_url}
- Figma: {figma_url}
- Documento: {doc_url}

{If the theme or store app was deployed to production on the main account, include the VTEX Admin setup URLs — see block below.}

Produção (VTEX Admin):
Versão nova do tema (ou app)
https://{conta}.myvtex.com/admin/apps/{vendor}.{nome-do-app}@{versao_nova}/setup

Versão antiga do tema (ou app)
https://{conta}.myvtex.com/admin/apps/{vendor}.{nome-do-app}@{versao_antiga}/setup

Como validar:
1) {Step-by-step instruction with specific actions to verify deliverable 1}
2) {Step-by-step instruction to verify deliverable 2}
{Number of steps should match the deliverables; be specific about what to check and where}

Evidências (prints):
{url_1}
{url_2}
{List each screenshot/print URL on its own line}

Ou, quando quiser destacar um único capture de produção ou do Admin:

Print:
https://prnt.sc/exemplo
```

**Exemplo completo (produção + print) — texto simples, sem Markdown:**

```
Atualização TASK-12345 - Ajuste vitrine

O que foi entregue:
- ...

Links:
- Pull Request (revisão do código): https://bitbucket.org/...

Produção (VTEX Admin):
Versão nova do tema
https://leeloo.myvtex.com/admin/apps/leeloo.store-theme@1.5.7/setup

Versão antiga do tema
https://leeloo.myvtex.com/admin/apps/leeloo.store-theme@1.5.6/setup

Como validar:
1) ...

Print:
https://prnt.sc/rwQq3HEvKLbr
```

**Guidelines for Template B:**
- Write "O que foi entregue" in **business language** — explain what the user/stakeholder sees, not what code was changed.
- **Produção (theme/app):** se a entrega **foi para produção** na conta principal, inclua o bloco "Produção (VTEX Admin)" com **versão nova** e, quando fizer sentido, **versão anterior** (rollback/referência). Se o usuário não passar as URLs, monte com `https://{conta}.myvtex.com/admin/apps/{vendor}.{app}@{semver}/setup` usando conta + app + versões do `manifest`/`Release:` ou do que foi publicado. **Não** incluir o bloco se a task foi só homolog/workspace de teste.
- "Links" section is flexible: always include PR and workspace if provided; add any extra links the user passes (GTM, Figma, docs, etc.).
- "Como validar" steps should be actionable and map to the deliverables — tell the validator exactly where to go and what to check.
- **Evidências / Print:** URLs puras (Runrun.it sem Markdown). Use "Print:" com uma linha de URL quando for uma evidência única (ex.: tela do Admin).
- If the user provides the content for each section, use it as-is. If not, derive it from the task data, PR description, and commit messages.
- Ask the user for clarification if the deliverables or validation steps are unclear.

**URL pattern (Admin):** `https://{conta}.myvtex.com/admin/apps/{vendor}.{nome}@{versao}/setup` — use o semver que aparece no VTEX Admin ou na linha `Release:` do commit / `manifest.json` publicado.

## Step F6 (optional) — Move task stage

If the user asks, move the task to the next stage:

```
server: user-runrunit-mcp
toolName: runrunit_move_task_stage
arguments: { "task_id": <task_id>, "board_stage_name": "Manager Validation" }
```

## Upload de prints/evidências via Cloudinary

Sempre que houver **prints/screenshots** para anexar (na task, no PR ou nos docs), hospedar via **Cloudinary** com a ferramenta MCP `runrunit_upload_image_cloudinary` e usar a `secure_url` retornada. Ver também a skill `upload-image-cloudinary`.

### Ferramenta MCP

```
server: user-runrunit-mcp
toolName: runrunit_upload_image_cloudinary
arguments: {
  "file_path": "<caminho absoluto ou relativo da imagem no disco>",
  "public_id": "task-{id}-{descricao}-{before|after}-{viewport}"   // opcional
}
```

- **Retorno:** `{ "secure_url": "https://res.cloudinary.com/.../arquivo.png" }` — usar **apenas** a `secure_url` (HTTPS pública).
- `public_id` é opcional; se informado, padronizar (ex.: `task-14003-vitrine-depois-mobile`). Reenviar com o mesmo `public_id` sobrescreve a imagem.
- Pré-requisito: variáveis `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` configuradas no MCP (`mcp.json`). Se o upload falhar, verificar essas credenciais e se o servidor `user-runrunit-mcp` está **ready** (não "loading").

### De onde vêm os arquivos

| Origem | Como obter o `file_path` |
|---|---|
| Print que o usuário já tem no disco | Usar o caminho informado (ex.: `C:\Users\...\print.png`) |
| Captura de página web (antes/depois) | `browser_take_screenshot` via browser MCP → usar o caminho retornado |
| Múltiplos viewports | Capturar em mobile (~375px) e desktop (~1440px) e subir cada um |

### Fluxo

1. Reunir os arquivos de imagem (do usuário ou capturados via browser MCP).
2. Para **cada** imagem, chamar `runrunit_upload_image_cloudinary` e guardar a `secure_url`.
3. (Opcional) Validar o link com um HEAD HTTP — deve retornar **200** e `Content-Type: image/*`.
4. Usar as URLs:
   - **Comentário da task (Runrun.it):** texto simples, uma URL por linha (Template A "Evidências" ou Template B "Evidências (prints)" / "Print:").
   - **Corpo do PR (Markdown):** `![Antes](secure_url)` / `![Depois](secure_url)`.

### Exemplo

```
1) browser_take_screenshot → C:\...\depois-mobile.png
2) runrunit_upload_image_cloudinary { file_path: "C:\...\depois-mobile.png", public_id: "task-14003-vitrine-depois-mobile" }
   → secure_url: https://res.cloudinary.com/xxxx/image/upload/v.../task-14003-vitrine-depois-mobile.png
3) Usar essa URL no comentário da task (linha pura) e no PR (![Depois](...))
```

## Partial execution

The user may request only part of the flow:

### Flow A — Start triggers

| Request | Steps to execute |
|---|---|
| "Iniciar tarefa" / "Começar task" / "Pega essa task" | A1 → A6 (full start flow) |
| "Pega dados da task" | A1 only |
| "Cria a branch" / "Checkout pra task" | A1 → A3 |
| "Analisa a task" / "O que precisa fazer?" | A1, A4 → A5 (analyze + plan, no branch) |
| "Inicia e já começa a codar" | A1 → A6 (full start + execute) |

### Flow B — Finish triggers

| Request | Steps to execute | Comment template |
|---|---|---|
| "Faz commit" | F1 → F3 | — |
| "Abre PR" | F1 → F4 | — |
| "Abre PR e comenta na task" | F1 → F5 | Template A or B (ask if unclear) |
| "Faz tudo" / "Finaliza" | F1 → F6 | Template A or B (ask if unclear) |
| "Só comenta na task" | F1, F5 | Template A or B (ask if unclear) |
| "Entrega a task" / "Passa pra validação" | F1, F5 (with user-provided PR/links) | **Template B** |
| "Comenta com PR e prints" | F1, F5 | **Template B** |

### Combined triggers

| Request | Steps to execute |
|---|---|
| "Pega a task e faz tudo" | A1 → A6, then F1 → F6 when done |
| "Inicia, desenvolve e abre PR" | A1 → A6, then F1 → F4 |

Always confirm with the user which steps to perform if unclear.

## MCP tools reference

| Tool | Purpose |
|---|---|
| `runrunit_get_task` | Fetch task data (title, description, tags, stage) |
| `runrunit_list_task_comments` | Get task comments for context |
| `runrunit_list_subtasks` | List subtasks of a parent task |
| `runrunit_update_task` | Save PR link (`link_da_branch`) in the task |
| `runrunit_create_comment` | Post comment on the task (plain text) |
| `runrunit_create_external_comment` | Post comment on guest/external channel |
| `runrunit_move_task_stage` | Move task to next board stage |
| `runrunit_upload_image_cloudinary` | Upload screenshot, returns `secure_url` |

## Important rules

### Permission & safety
- **ALWAYS ask permission** before creating files, deleting files/code, installing dependencies, or changing config files
- **ALWAYS verify workspace** before creating/checking out branches — never operate on the wrong repo
- **ALWAYS check for uncommitted changes** before switching branches
- **NEVER start coding without presenting a plan** and getting user approval (Flow A)
- **NEVER delete files or code** without explicit user confirmation

### Runrun.it
- Comments are **plain text only** — no Markdown
- Always include `TASK-{id}` reference in commits, PRs, and comments
- **Prints/evidências:** hospedar sempre via Cloudinary (`runrunit_upload_image_cloudinary`) e usar a `secure_url`; nunca colar caminho local do disco no comentário/PR (ver "Upload de prints/evidências via Cloudinary")

### Git
- Always include `TASK-{id}` reference in commits and PR
- **VTEX IO (theme / app):** **não** subir `"version"` em ajustes/homolog; só alterar a versão **ao ir para produção** e **sempre perguntar** o incremento (patch/minor/major). No commit de produção: bump no `manifest.json`, `CHANGELOG.md` se existir, e **primeira linha** da mensagem = `Release: {vendor}.{name}@{version}` (antes do `[TASK-…]`). Ver Step F3
- Check `git status` before committing — never commit unrelated files
- Never force push or amend unless explicitly asked
- Branch naming: **depende do projeto** (ver Step A3) — padrão `task{id}` (ex.: `task14003`); **omie** usa `feat/<descricao>` (ex.: `feat/blog-page`), nunca `task{id}`
- **Git commit workaround:** ALWAYS use `& "C:\Program Files\Git\bin\git.exe" commit -F .git/COMMIT_MSG_TEMP` instead of `git commit -m "..."` to avoid the Cursor `--trailer` injection issue on git < 2.32. Write the message to `.git/COMMIT_MSG_TEMP` first using the Write tool, including `Made-with: Cursor` as the last line. **deco.cx / loja VFOR:** add `--no-verify` to that command by default (see Step F3).

### PR
- PR body uses **full Markdown** with the project template
- The PR template from the project must be followed exactly

### Skills integration
- When the task involves deco.cx or VTEX, **read the appropriate skill** before executing
- **Plataforma VTEX + CSS/estilo/layout/CSS Handles:** SEMPRE usar a skill `vtex-css` (seletores permitidos, CSS Handles, padrão do time para seletores legados em `vtex.login`/`vtex.my-account`)
- **Task com link do Figma:** usar a skill `figma-assets` para extrair design, tipografia/espaçamentos exatos e assets (SVG/imagens) antes de implementar
- **Validar/debugar no workspace VTEX IO (URL `{ws}--{conta}.myvtex.com`):** usar a skill `vtex-io-workspace-debug` — ela abre o workspace privado no navegador, **espera o usuário logar** e então debuga/valida/captura evidências
- **Prints/evidências:** usar a skill `upload-image-cloudinary` (ou a ferramenta `runrunit_upload_image_cloudinary`) para hospedar imagens antes de referenciá-las
- **Projeto omie (Next.js + Strapi):** as skills são **project-scoped** e ficam em `C:\projetos\omie\.cursor\skills\`. Use conforme a task:
  - `omie-commit` — **padrão de branch (`feat/<descricao>`) e commit** (Conventional Commits + corpo detalhado) do omie; usar sempre que for branchar/commitar nesse repo
  - `component-creator` — criar/extrair/refatorar componentes React (front Next.js, Tailwind v4, DS)
  - `strapi-single-cpts` — criar/evoluir Single Types e CPTs no Strapi (`cms/`) + tipagem no front
  - `page-builder-section-mapper` — mapear uma URL em seções do page builder (screenshots + campos CMS)
  - `section-performance-optimizer` — otimizar seções do page builder em lotes de 5 UIDs (TBT/PageSpeed)
  - `frontend-performance` — diagnosticar/otimizar performance Next.js (Lighthouse, bundle, Core Web Vitals)
  - `popup-form-template-creator` — criar/editar popups e templates de formulário (mapeamento HubSpot)
  - `legacy-lp-text-sync` — sincronizar textos de LPs estáticas legadas com produção
  - `legacy-lp-css-background-sync` — trazer imagens de background (CSS) de LPs legadas da produção
  - `legacy-lp-section-precos` — ligar preços globais (Strapi) em LPs estáticas legadas
- Available skills (globais, `~/.cursor/skills`): `deco-section`, `deco-loader`, `deco-island`, `deco-app`, `deco-vtex`, `vtex-io-component`, `vtex-css`, `vtex-io-node-graphql`, `vtex-checkout`, `vtex-checkout-config`, `vtex-io-workspace-debug`, `figma-assets`, `upload-image-cloudinary`, `registrar-evidencias`
- Skills globais ficam em `C:\Users\agencian1\.cursor\skills\{skill-name}\SKILL.md`; skills **project-scoped** (ex.: omie) ficam em `{repo}\.cursor\skills\{skill-name}\SKILL.md`
- Follow the skill instructions exactly — they contain project-specific conventions and patterns
