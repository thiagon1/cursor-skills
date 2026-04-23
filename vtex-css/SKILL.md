---
name: vtex-css
description: VTEX IO storefront CSS — use CSS Handles and compliant selectors only, avoid structure-based selectors, and use vtex.css-handles (useCssHandles, withModifiers, useCustomClasses, createCssHandlesContext) in React components. Use when customizing store theme CSS, adding handles, Site Editor blocks, vtex.io styles, or when the user mentions CSS Handles, deprecated selectors, or bit.ly/io-css-selectors.
---

# VTEX IO — CSS Handles & seletores permitidos

Guia prático para customização de CSS em **Store Theme** e apps `store`: personalize via **CSS Handles** e arquivos `.css` do tema, nunca ancorando no HTML de forma frágil.

## Referências oficiais

- **Deprecação de seletores CSS (whitelist):** [CSS Selectors deprecation](https://bit.ly/io-css-selectors) (nota de release da VTEX)
- **Biblioteca e API de handles:** [vtex-apps/css-handles no GitHub](https://github.com/vtex-apps/css-handles) — gera e expõe classes de customização; documenta `useCssHandles`, `useCustomClasses`, `createCssHandlesContext`
- **Detalhes e lista completa (allow/deny):** [selectors-reference.md](selectors-reference.md)
- **Componentes React com handles** (registro, schema, blocks): skill `vtex-io-component`

---

## Regras gerais

1. **Customização pública = CSS Handles** — classes expostas pelo componente (ex. `.container`, com prefixo de app na loja) são o contrato de estilo. Quem consome o tema (loja) usa esses handles no CSS do **theme** ou de **customização**.
2. **Não use seletores baseados em estrutura HTML** (`div > span`, `section:nth-child(3)`) em projetos ainda **não publicados**: o **VTEX IO CLI** bloqueia seletores fora da whitelist no **link** (desde a política de deprecação).
3. **Lojas já publicadas** ainda podem publicar com seletores antigos, mas o layout fica frágil a qualquer alteração de markup — a VTEX **recomenda** migrar tudo para Handles e seletores permitidos.
4. **Dependency no app** que define componentes: em `manifest.json`, declare `"vtex.css-handles": "0.x"` (e tipagem `declare module 'vtex.css-handles'` se aplicável). Ver `vtex-io-component`.

---

## O que a VTEX **permite** (whitelist resumida)

| Permitido | Exemplo |
|---|---|
| Seletor de **classe** | `.minhaClasse` |
| Pseudo-classe | `:hover`, `:visited`, `:active`, `:disabled`, `:focus`, `:local`, `:not`, `:target`, `:first-child`, `:last-child` |
| Todos os **pseudo-elementos** | `::before`, `::after`, `::placeholder` |
| `nth-child` | apenas `(even)` e `(odd)` |
| Combinador **espaço** (descendente) | `.foo .bar` |
| Atributo `data-` | `[data-foo="bar"]` |
| `:global(vtex-...)` | Apenas para selecionar nós de **outro app** no formato de Handle de app (ex. componentes `vtex-*` versionados) |

## O que a VTEX **não** quer (e bloqueia em apps novos no link)

| Proibido / depreciado | Exemplo |
|---|---|
| Seletor de **tipo** (tag) | `div`, `span`, `a` |
| Combinadores **filho/irmão** | `>`, `+`, `~` |
| `nth-child` com **número** | `li:nth-child(2)` |
| Seletor de atributo **que não seja** `[data-...]` | `[class~="x"]`, `[alt="x"]` |
| `:global` com classes que **não** sejam handles de outro app | workaround frágil |

Texto longo e casos de borda: [selectors-reference.md](selectors-reference.md).

---

## Onde fica o CSS do tema

- Arquivos no app de **store theme** (ex. `styles/css/vtex.*/*.css` ou pastas usadas no seu projeto) — use classes que correspondam a **CSS Handles** renderizados na página, não invente cadeias `html body div#...`.
- Nomes reais de classe na loja: prefixados pelo identificador do app/versão (Handles expostos); inspecione no browser para confirmar se necessário, mas **escreva o CSS** como `.nomeDoHandle` / modificadores (abaixo) conforme a documentação do bloco.

---

## API `vtex.css-handles` (React)

Fonte: [README do repositório vtex-apps/css-handles](https://github.com/vtex-apps/css-handles).

### `useCssHandles`

- Recebe um array **const** de identificadores de handle (strings).
- Retorna `handles` (mapeia nome de handle → classe string) e `withModifiers` (gera sufixos `--modificador` nos handles).
- Opções: `classes` (override vindo de props — veja `useCustomClasses`); `migrationFrom` (IDs de app ao migrar bloco de um app para outro).

Padrão mínimo:

```tsx
import { useCssHandles } from 'vtex.css-handles'

const CSS_HANDLES = ['container', 'title', 'item'] as const

function MyComponent({ classes }) {
  const { handles, withModifiers } = useCssHandles(CSS_HANDLES, { classes })

  return (
    <div className={handles.container}>
      <h1 className={handles.title}>Title</h1>
      <ul>
        {items.map((x) => (
          <li
            key={x.id}
            className={withModifiers('item', x.modifierClass)}
          >
            {x.label}
          </li>
        ))}
      </ul>
    </div>
  )
}
```

**Vários nós com handles no mesmo bloco:** o hook deve ser chamado no **componente raiz (entry do block)** e receber **todos** os handles dos filhos, OU use `createCssHandlesContext` para compartilhar contexto (evita prop drill de `classes`).

### `withModifiers('handle', modifier)`

- Primeiro argumento: nome lógico do handle.
- Segundo: string ou array de strings; gera classes do tipo `handle--modifier`.

### `useCustomClasses`

- Permite que o **componente pai** mapeie nomes/aliases de classes para o filho, injetando via prop `classes` no filho que usa `useCssHandles`. Use quando o bloco precisa "absorver" a API de handles de componentes aninhados.

### `createCssHandlesContext`

- Cria `CssHandlesProvider` + `useContextCssHandles` para prover `handles` e `withModifiers` a descendentes sem passar `classes` por cada nível. O provider envolve a árvore; componentes aninhados usam `useContextCssHandles` e exportam `Component.cssHandles` para o pai mergear a lista de handles do bloco.

---

## Fluxo de trabalho recomendado

1. **Definir handles** (nomes semânticos, poucos, estáveis) no(s) componente(s) do app.
2. **Usar o tema** para estilizar `.handle` e `.handle--modificador` com seletores **da whitelist** apenas.
3. **Nunca** contar com ordem de `div` ou `nth-child(5)` no DOM da loja.
4. Antes do **link** em projeto novo, rode linter/build — se o CLI apontar seletor inválido, refatore para classes/handles.
5. Para integração de layout Figma, blocos, schema: use a skill **vtex-io-component**.

---

## Checklist rápido

- [ ] Handles declarados e aplicados com `useCssHandles` (ou contexto) no componente certo
- [ ] Estilos do tema usam **classes** (e whitelist), não `tag > tag`
- [ ] `manifest.json` inclui `vtex.css-handles` se o app expõe componentes com handles
- [ ] Loja nova: zero seletores bloqueados no CSS do link

---

## Erros comuns

| Problema | Causa provável | Ação |
|---|---|---|
| Link falha com erro de seletor CSS | Seletor fora da whitelist | Reescrever usando classes + handles |
| Tema "não pega" estilo | Seletor mirando outro bloco/versão | Conferir nome do handle e app no inspector |
| Classe duplicada / conflito | Dois apps, mesmo identificador de handle | Handles são únicos por app; use namespaces claros e `:global(vtex-...)` só conforme regra VTEX |
| Modificador não aplica | `withModifiers` incorreto ou CSS sem `handle--x` | Alinhar nome do modificador e regra no `.css` |

Se precisar de blocos, Site Editor, `interfaces.json` e padrão de arquivos: use **vtex-io-component** em conjunto com esta skill.
