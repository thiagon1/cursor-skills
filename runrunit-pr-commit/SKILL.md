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

Branch naming convention: `task{id}` (e.g. `task14003`).

1. Run `git status` to check for uncommitted changes.
   - If there are uncommitted changes, STOP and ask: "Existem alterações não commitadas na branch atual. Deseja fazer stash, commit ou descartar antes de trocar?"
   - Wait for user confirmation before proceeding.

2. Check if the branch already exists:
   ```
   git branch --list task{id}
   git branch -r --list "*/task{id}"
   ```

3. **If branch exists locally:** ask the user: "A branch `task{id}` já existe. Deseja fazer checkout para ela?"
   - On confirmation: `git checkout task{id}`

4. **If branch exists only on remote:** ask: "A branch `task{id}` existe no remoto. Deseja fazer checkout?"
   - On confirmation: `git checkout -b task{id} origin/task{id}`

5. **If branch does not exist:** ask: "Vou criar a branch `task{id}` a partir de `{current_branch}`. Confirma?"
   - The base branch should typically be `development` or `main` — ask if unclear.
   - On confirmation: `git checkout -b task{id} {base_branch}`

6. Confirm to the user: "Branch `task{id}` pronta. Trabalhando a partir de `{base_branch}`."

## Step A4 — Analyze task and identify technology / skills

Parse the task `title`, `description`, `tags`, and `comments` to determine:

### Technology detection

| Signal in task data | Technology | Relevant skills |
|---|---|---|
| `vtex`, `vtex io`, `store-theme`, `site editor`, `shelf`, `checkout` | VTEX IO | `vtex-io-component`, `vtex-io-node-graphql`, `vtex-checkout`, `vtex-checkout-config` |
| `deco`, `deco.cx`, `fresh`, `section`, `loader`, `island` | deco.cx | `deco-section`, `deco-loader`, `deco-island`, `deco-app`, `deco-vtex` |
| `checkout`, `orderForm`, `checkout6-custom` | VTEX Checkout | `vtex-checkout`, `vtex-checkout-config` |
| `graphql`, `node`, `resolver`, `client`, `middleware` | VTEX IO Node/GraphQL | `vtex-io-node-graphql` |

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

1. **Read the relevant skill** before starting (e.g., `deco-section`, `vtex-io-component`).
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

```
[TASK-{id}] {type}: {short description}

{optional body with more details}
```

Where `{type}` follows conventional commits:
- `fix:` for bug fixes
- `feat:` for new features
- `refactor:` for refactoring
- `docs:` for documentation
- `style:` for layout/visual changes

### Example

```
[TASK-13631] style: adjust mobile shelf/search with sizes

Updated shelf and search layouts for mobile viewport
to properly display product size variations.
```

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
5. As a last resort, use `--no-verify` only if hooks are the issue (not the trailer)

This applies to ALL git commit operations in this skill (commit, amend, etc.).

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

Use when the user finishes a task and wants to document what was delivered, provide validation links (workspace, GTM, etc.), explain how to validate, and attach evidence prints. This is the preferred template when the user says "comenta na task", "entrega", "passa pra validação", or provides PR + prints + workspace links.

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

Como validar:
1) {Step-by-step instruction with specific actions to verify deliverable 1}
2) {Step-by-step instruction to verify deliverable 2}
{Number of steps should match the deliverables; be specific about what to check and where}

Evidências (prints):
{url_1}
{url_2}
{List each screenshot/print URL on its own line}
```

**Guidelines for Template B:**
- Write "O que foi entregue" in **business language** — explain what the user/stakeholder sees, not what code was changed.
- "Links" section is flexible: always include PR and workspace if provided; add any extra links the user passes (GTM, Figma, docs, etc.).
- "Como validar" steps should be actionable and map to the deliverables — tell the validator exactly where to go and what to check.
- "Evidências" is a simple list of URLs (prints, screenshots). No labels needed unless the user provides them.
- If the user provides the content for each section, use it as-is. If not, derive it from the task data, PR description, and commit messages.
- Ask the user for clarification if the deliverables or validation steps are unclear.

## Step F6 (optional) — Move task stage

If the user asks, move the task to the next stage:

```
server: user-runrunit-mcp
toolName: runrunit_move_task_stage
arguments: { "task_id": <task_id>, "board_stage_name": "Manager Validation" }
```

## Evidence capture flow (when URLs provided)

If the user provides before/after URLs:

1. Use browser MCP to capture screenshots at multiple viewports (mobile 375px, desktop 1440px)
2. Upload each screenshot via `runrunit_upload_image_cloudinary`:
   ```
   server: user-runrunit-mcp
   toolName: runrunit_upload_image_cloudinary
   arguments: { "file_path": "<screenshot_path>", "public_id": "task-{id}-{viewport}-{before|after}" }
   ```
3. Use the returned `secure_url` in both the PR body (markdown images) and the task comment (plain URLs)

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

### Git
- Always include `TASK-{id}` reference in commits and PR
- Check `git status` before committing — never commit unrelated files
- Never force push or amend unless explicitly asked
- Branch naming: `task{id}` (e.g. `task14003`)
- **Git commit workaround:** ALWAYS use `& "C:\Program Files\Git\bin\git.exe" commit -F .git/COMMIT_MSG_TEMP` instead of `git commit -m "..."` to avoid the Cursor `--trailer` injection issue on git < 2.32. Write the message to `.git/COMMIT_MSG_TEMP` first using the Write tool, including `Made-with: Cursor` as the last line.

### PR
- PR body uses **full Markdown** with the project template
- The PR template from the project must be followed exactly

### Skills integration
- When the task involves deco.cx or VTEX, **read the appropriate skill** before executing
- Available skills: `deco-section`, `deco-loader`, `deco-island`, `deco-app`, `deco-vtex`, `vtex-io-component`, `vtex-io-node-graphql`, `vtex-checkout`, `vtex-checkout-config`
- Skills are located at `C:\Users\agencian1\.cursor\skills\{skill-name}\SKILL.md`
- Follow the skill instructions exactly — they contain project-specific conventions and patterns
