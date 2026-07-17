---
name: figma-assets
description: Extrai design e assets do Figma via MCP a partir de um link — contexto/specs (get_design_context, metadata, variables, screenshot) e download de SVG/imagens (download_assets). Use quando o usuário enviar um link do Figma e pedir para pegar o design, specs, tokens, exportar SVG, baixar imagens/ícones ou implementar uma tela a partir do Figma.
---

# Figma — pegar design e assets via MCP

Skill para trabalhar com links do Figma usando o **MCP do Figma** (server `user-Figma`). Dois fluxos:

- **Flow 1 — Design/specs:** obter código de referência, estrutura, tokens/variáveis e screenshot de um nó.
- **Flow 2 — Assets (SVG/imagens):** exportar/baixar SVG, PNG, JPG e as imagens originais de um nó.

## Pré-requisito

- Server MCP `user-Figma` com status **ready**. Se estiver "needsAuth", chamar `mcp_auth` desse server e autenticar.
- O usuário precisa fornecer um **link de nó específico** (com `node-id`). Sem `node-id`, pedir o link do nó selecionado.

## Passo 0 — Extrair `fileKey` e `nodeId` do link (SEMPRE primeiro)

A partir de `https://figma.com/design/:fileKey/:fileName?node-id=1-2`:

- `fileKey` = segmento após `/design/`.
- `nodeId` = valor de `node-id`, trocando `-` por `:` (ex.: `21016-6080` → `21016:6080`).

Variações:
- Branch: `https://figma.com/design/:fileKey/branch/:branchKey/:fileName` → usar `branchKey` como `fileKey`.
- Só funciona em URLs `/design/`. `/board/` (FigJam), `/slides/` e `/make/` têm outras ferramentas/regras.
- Se a URL **não** tiver `node-id`, pedir ao usuário o link do nó específico (não adivinhar `nodeId`).

**Exemplo (link deste projeto):**
`.../design/RNLC1stgG6AljmbLflHgO9/...?node-id=21016-6080`
→ `fileKey = RNLC1stgG6AljmbLflHgO9`, `nodeId = 21016:6080`.

---

# Flow 1 — Design / specs

Objetivo: entender e/ou implementar um nó (tela, componente) do Figma.

## 1.1 — Contexto principal (`get_design_context`)

Ferramenta primária para design-to-code. Retorna código de referência + screenshot + metadados e URLs dos assets referenciados.

```
server: user-Figma
toolName: get_design_context
arguments: {
  "fileKey": "<fileKey>",
  "nodeId": "<nodeId>",
  "clientLanguages": "javascript,css,typescript",
  "clientFrameworks": "react"   // ou "preact", "vue", "unknown"
}
```

- O código retornado é **referência**, não final — adaptar aos padrões do projeto (ex.: VTEX IO → CSS Handles + `vtex-io-component`; deco.cx → `deco-section`/`deco-island`).
- Por padrão inclui screenshot. Só usar `excludeScreenshot: true` para poupar contexto quando o usuário pedir.

## 1.2 — Estrutura do nó (`get_metadata`) — opcional

Use para ter um mapa (IDs, tipos, nomes, posições, tamanhos) e então chamar `get_design_context` em nós filhos específicos. Bom para telas grandes.

```
server: user-Figma
toolName: get_metadata
arguments: { "fileKey": "<fileKey>", "nodeId": "<nodeId>" }
```

- Sem `nodeId`: lista as páginas de topo do arquivo (útil quando não se sabe onde entrar).

## 1.3 — Tokens / variáveis (`get_variable_defs`)

Cores, tipografia, espaçamentos, etc. definidos como variáveis no nó.

```
server: user-Figma
toolName: get_variable_defs
arguments: { "fileKey": "<fileKey>", "nodeId": "<nodeId>" }
```

Ex. retorno: `{ "icon/default/secondary": "#949494", "spacing/md": 16 }` — mapear para tokens/tema do projeto.

## 1.4 — Screenshot de referência (`get_screenshot`)

Imagem do nó para comparar com a implementação.

```
server: user-Figma
toolName: get_screenshot
arguments: { "fileKey": "<fileKey>", "nodeId": "<nodeId>", "maxDimension": 1024 }
```

- Retorna URL curta + instruções `curl` (preferível; gasta menos contexto). Aumente `maxDimension` para inspecionar detalhes.

---

# Flow 2 — Assets (SVG / imagens)

Objetivo: exportar/baixar **SVG**, **PNG/JPG** ou as **imagens originais** de um nó (ícones, logos, fotos).

## 2.1 — Baixar assets (`download_assets`)

```
server: user-Figma
toolName: download_assets
arguments: {
  "fileKey": "<fileKey>",
  "nodeId": "<nodeId>",
  "defaultFormat": "svg"   // "svg" | "png" | "jpg" | "pdf" (opcional)
  // "defaultScale": 2      // 0.01–4, só p/ png/jpg quando pedir resolução específica
}
```

Retorna:
1. Um **render exportado** do nó (no formato pedido).
2. A lista de **imagens originais** (JPEG/PNG/GIF/WebP) usadas como fills no subtree (até 20). Cada uma traz o `format` real → salvar com a extensão correta.

Regras:
- **SVG** (ícones/vetores/logos): passar `defaultFormat: "svg"`.
- **Foto/bitmap** (banner, foto de produto): usar as **imagens originais** retornadas, ou `defaultFormat: "png"`/`"jpg"`.
- Só definir `defaultFormat`/`defaultScale` quando o usuário pedir formato/resolução específicos; sem isso, respeita as export settings do nó (senão PNG @1x).
- **URLs são temporárias** — baixar imediatamente.

## 2.2 — Salvar no projeto

1. Baixar cada asset a partir da URL retornada (via `curl`/download) para a pasta correta do projeto:
   - VTEX IO: `assets/` do app ou onde o time versiona ícones/imagens.
   - deco.cx: `static/` (ou pasta de assets do projeto).
2. Nomear de forma semântica (ex.: `icon-cart.svg`, `banner-pdp-mobile.png`).
3. Confirmar com o usuário **antes de criar arquivos** (regra geral de permissão).

## 2.3 — SVG inline (opcional)

Se o objetivo é usar o SVG **inline** no código (componente React/Preact), abrir o conteúdo do `.svg` baixado e colar como JSX, ou referenciar o arquivo. Otimizar (remover metadados do Figma) se necessário.

---

## Fluxo recomendado (design-to-code a partir de um link)

1. Passo 0: extrair `fileKey` + `nodeId`.
2. `get_design_context` para código + screenshot.
3. `get_variable_defs` se houver tokens a mapear.
4. `download_assets` (`svg`/`png`) para ícones e imagens do nó.
5. Salvar assets no projeto (com confirmação) e implementar adaptando aos padrões da stack (`vtex-io-component` / `vtex-css` / `deco-section`).
6. Comparar com `get_screenshot` para conferir fidelidade.

## Ferramentas MCP (server `user-Figma`)

| Ferramenta | Uso |
|---|---|
| `get_design_context` | Código de referência + screenshot + metadados (principal) |
| `get_metadata` | Estrutura (IDs/tipos/tamanhos) para navegar nós |
| `get_variable_defs` | Tokens/variáveis (cor, tipografia, espaçamento) |
| `get_screenshot` | Imagem do nó para referência/comparação |
| `download_assets` | Exportar SVG/PNG/JPG/PDF + imagens originais |
| `mcp_auth` | Autenticar o server Figma quando `needsAuth` |

## Regras

- **Sempre** extrair `fileKey`/`nodeId` do link antes de chamar qualquer ferramenta; nunca adivinhar `nodeId`.
- Código do `get_design_context` é referência — adaptar à stack (não colar cru).
- Baixar assets logo após receber as URLs (expiram).
- Pedir confirmação antes de criar/salvar arquivos no projeto.
- Só `/design/` nesta skill; FigJam (`/board/`), Slides (`/slides/`) e Make (`/make/`) não são cobertos aqui.
- Integra com: `vtex-io-component`, `vtex-css`, `deco-section`, `deco-island` para implementar o design extraído.
