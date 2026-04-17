# Cursor Skills

Skills personalizadas para o Cursor AI, focadas em desenvolvimento VTEX, deco.cx e automações de workflow.

## Skills disponíveis

### VTEX

| Skill | Descrição |
|---|---|
| **vtex-checkout** | Customização do VTEX Checkout v6 — vtex.js, orderForm, eventos, proxy local para testes |
| **vtex-io-component** | Criação de componentes React para VTEX IO com CSS Handles, Site Editor e interfaces.json |
| **vtex-io-node-graphql** | Backend Node.js e GraphQL no VTEX IO — resolvers, clients, mutations e integração com React |
| **vtex-checkout-config** | Configuração da API de Checkout VTEX — orderForm config, seller window, limpar mensagens |

### Analytics / Tracking

| Skill | Descrição |
|---|---|
| **gtm-tags** | Google Tag Manager — auditar, validar, debugar e implementar tags, triggers, dataLayer e eventos GA4 (ecommerce e customizados) |

### deco.cx

| Skill | Descrição |
|---|---|
| **deco-section** | Criação de Sections — componentes Preact com Props tipadas que geram formulários no Admin |
| **deco-loader** | Loaders e Inline Loaders — data fetching server-side com Props configuráveis |
| **deco-island** | Islands — componentes interativos com hidratação client-side, signals e invoke API |
| **deco-app** | Criação de Apps customizadas — mod.ts, actions, workflows, loaders e state compartilhado |
| **deco-vtex** | Integração deco.cx + VTEX — PLP, PDP, carrinho, busca e operações via invoke |

### Automações

| Skill | Descrição |
|---|---|
| **runrunit-pr-commit** | Ciclo completo de tasks no Runrun.it — inicia tarefa (branch, análise, plano), executa com outras skills, commit, PR e comentário de entrega |

## Como usar

### Em um projeto existente

Copie as skills desejadas para `.cursor/skills/` no seu projeto:

```bash
# Copiar uma skill específica
cp -r vtex-checkout /seu-projeto/.cursor/skills/

# Copiar todas
cp -r */ /seu-projeto/.cursor/skills/
```

### Estrutura de cada skill

```
skill-name/
├── SKILL.md          ← arquivo principal (obrigatório)
├── reference.md      ← referência detalhada da API (opcional)
└── examples.md       ← exemplos de uso (opcional)
```

O Cursor detecta automaticamente qualquer pasta com `SKILL.md` dentro de `.cursor/skills/`.

## Requisitos

- [Cursor IDE](https://cursor.com/) com suporte a Agent Skills
- Para skills VTEX: acesso ao ambiente VTEX da loja
- Para skills deco.cx: [Deno](https://deno.land/) instalado + projeto deco.cx
- Para runrunit-pr-commit: MCP do Runrun.it configurado + GitHub CLI (`gh`)
