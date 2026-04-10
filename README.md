# Cursor Skills

Skills personalizadas para o Cursor AI, focadas em desenvolvimento VTEX e automações de workflow.

## Skills disponíveis

| Skill | Descrição |
|---|---|
| **vtex-checkout** | Customização do VTEX Checkout v6 — vtex.js, orderForm, eventos, proxy local para testes |
| **vtex-io-component** | Criação de componentes React para VTEX IO com CSS Handles, Site Editor e interfaces.json |
| **vtex-io-node-graphql** | Backend Node.js e GraphQL no VTEX IO — resolvers, clients, mutations e integração com React |
| **runrunit-pr-commit** | Automação: busca dados de tasks no Runrun.it, cria commits semânticos e abre PRs no GitHub |

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
- Para runrunit-pr-commit: MCP do Runrun.it configurado + GitHub CLI (`gh`)
