---
name: omie-commit
description: >-
  Branch and commit standard for the OMIE project (Next.js + Strapi). Use when
  creating a branch or writing a git commit in C:/projetos/omie: enforces
  feat/<descricao> branch naming and Conventional Commits with a rich,
  context-first body (what/why, problem, solution, rationale, edge cases, tests).
  Use whenever the user asks to commit, branch, or "seguir o padrão do omie".
---

# OMIE — padrão de branch e commit

Padrão de **branch** e **mensagem de commit** do projeto OMIE (`C:\projetos\omie`, Next.js `front/` + Strapi `cms/`). Use ao criar branch ou commitar neste repo.

## Quando usar

- "criar branch no omie", "commit no omie", "seguir o padrão do omie", "commitar isso"
- Sempre que estiver commitando dentro de `C:\projetos\omie`

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

## 4. Integração

- **`runrunit-pr-commit`**: ao iniciar/entregar uma task do omie, usar esta skill para nome de branch (`feat/<descricao>`) e mensagem de commit; o restante (PR, comentário na task, Cloudinary) segue a `runrunit-pr-commit`.
- Skills de implementação do omie: `component-creator`, `strapi-single-cpts`, `page-builder-section-mapper`, `section-performance-optimizer`, `frontend-performance`, `popup-form-template-creator`, `legacy-lp-*`.

## Regras

- Branch: `{tipo}/{descricao-kebab}`, nunca `task{id}`. Confirmar branch base.
- Commit: Conventional Commits com assunto em português + **corpo explicando o porquê** (contexto, problema, solução, casos de borda, testes).
- `[TASK-{id}]` no assunto é opcional (usar quando vier do Runrun.it).
- Commitar com `git.exe -F .git\COMMIT_MSG_TEMP`; deixar husky/lint-staged rodar; `--no-verify` só em falha espúria e com aviso.
