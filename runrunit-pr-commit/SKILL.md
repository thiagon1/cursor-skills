---
name: runrunit-pr-commit
description: Fetches Runrun.it task data via MCP, creates semantic git commits, opens GitHub PRs using the project template, and posts a summary comment on the task. Use when the user provides a Runrun.it task link and wants to commit, open a PR, or document the task.
---

# Runrun.it → Commit + PR + Comment

Workflow that fetches task data from Runrun.it, creates semantic commits, opens a GitHub PR with the project template, and optionally comments on the task with the PR link.

## Input

| Campo | Obrigatório | Descrição |
|-------|-------------|-----------|
| **Link da task** | Sim | URL da tarefa (ex.: `https://runrun.it/en-US/tasks/13631`) ou ID numérico |
| **URLs antes/depois** | Não | Para evidências visuais no PR e na task |
| **Branch destino** | Não | Padrão: `development` |

## Step 1 — Fetch task data from Runrun.it

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

## Step 2 — Determine change type

Map the task info to one of the PR change types:

| Tag / Keyword in title | Type |
|---|---|
| `bug`, `fix`, `correção` | 🐛 Correção de bug |
| `feature`, `novo`, `criar`, `adicionar` | ✨ Novo recurso |
| `refactor`, `refatoração`, `melhoria` | ♻️ Refatoração |
| `doc`, `documentação` | 📖 Documentação |
| `layout`, `css`, `estilo`, `visual`, `ajust` | 🎨 Alteração de layout |

If ambiguous, ask the user or default to 🎨 Alteração de layout.

## Step 3 — Create semantic commits

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

## Step 4 — Open GitHub PR

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

## Step 5 — Update task on Runrun.it

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

Comment format (plain text, NO Markdown):

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

## Step 6 (optional) — Move task stage

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

| Request | Steps to execute |
|---|---|
| "Pega dados da task" | Step 1 only |
| "Faz commit" | Steps 1 → 3 |
| "Abre PR" | Steps 1 → 4 |
| "Abre PR e comenta na task" | Steps 1 → 5 |
| "Faz tudo" | Steps 1 → 6 |
| "Só comenta na task" | Steps 1, 5 |

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

- Runrun.it comments are **plain text only** — no Markdown
- PR body uses **full Markdown** with the project template
- Always include `TASK-{id}` reference in commits and PR
- Check `git status` before committing — never commit unrelated files
- Never force push or amend unless explicitly asked
- The PR template from the project must be followed exactly
- **Git commit workaround:** ALWAYS use `& "C:\Program Files\Git\bin\git.exe" commit -F .git/COMMIT_MSG_TEMP` instead of `git commit -m "..."` to avoid the Cursor `--trailer` injection issue on git < 2.32. Write the message to `.git/COMMIT_MSG_TEMP` first using the Write tool, including `Made-with: Cursor` as the last line.
