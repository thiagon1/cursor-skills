---
name: vtex-css
description: VTEX IO storefront CSS — CSS Handles, compliant selectors (bit.ly/io-css-selectors), vtex.css-handles API, and team pattern for legacy selectors in app-scoped theme CSS when CLI skips validation (e.g. vtex.login, vtex.my-account). Use when customizing store theme, compliant selectors, CSS Handles, or vendor-specific CSS overrides.
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

## Padrão do time — seletores fora da whitelist (workaround)

O **VTEX IO CLI** valida a whitelist de seletores no `vtex link`. Em builds reais, o output pode exibir que a validação de CSS **foi ignorada** para certas dependências por causa da **major version** do app, por exemplo:

```text
CSS validation was skipped for the following apps because of their current major version:

- vtex.login@2.x
- vtex.my-account@1.x
```

**Convenção deste time:** concentre **todos** os seletores que **não** seriam aceitos na validação padrão (ex.: `>`, `+`, seletor de tag, `nth-child(3)`, atributo que não seja `data-`, etc.) **apenas** nos arquivos CSS do tema cujo **escopo** corresponde a esses apps de vendor — a estrutura usual do Store Theme é **uma pasta por app** embaixo de `styles/css/`, por exemplo:

- `styles/css/vtex.login/**/*.css` — customizações de **Login** (apenas seletores “legados” / não conformes aqui)
- `styles/css/vtex.my-account/**/*.css` — customizações de **Minha conta** (idem)

Mantenha o restante do tema (home, PLP, PDP, shelf, header genérico, etc.) com **seletores conformes e Handles** sempre que possível.

**Regras para esse CSS “legado”:**

- Tratar como **dívida técnica**: comentar brevemente no arquivo **por que** o seletor não pôde ser expresso só com Handles + whitelist (ex.: “sem handle no bloco X nesta major”).
- Após **upgrade** de `vtex.login` / `vtex.my-account` (ou se a validação deixar de ser ignorada), revisar o arquivo: o `vtex link` pode voltar a bloquear regras antigas — refatorar para Handles/whitelist nessa oportunidade.
- Não espalhar seletores não conformes em arquivos de outros fornecedores “só porque funciona hoje” — a mensagem de “validation skipped” é **por app/major**; o time padronizou o escape hatch nesses **dois** escopos conhecidos; amplie a lista só se o CLI documentar o mesmo para outro `vendor@major`.

Mais detalhe e cuidados: [selectors-reference.md](selectors-reference.md) (seção *Validação ignorada por major version e escopos no tema*).

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
2. **Usar o tema** para estilizar `.handle` e `.handle--modificador` com seletores **da whitelist** na maior parte do projeto.
3. **Só** quando não houver alternativa (ex.: tela de login / minha conta com markup sem Handle suficiente e major com validação relaxada), colocar seletores não conformes **somente** nos arquivos sob `styles/css/vtex.login/` e `styles/css/vtex.my-account/` (ou o par documentado no manifest/time).
4. **Nunca** contar com ordem de `div` ou `nth-child(5)` no DOM da loja — mesmo no CSS legado, minimizar a superfície (menos regras possível).
5. Antes do **link**, observar a saída do CLI: se a lista de “validation skipped” mudar, revisar esses arquivos.
6. Para integração de layout Figma, blocos, schema: use a skill **vtex-io-component**.

---

## Checklist rápido

- [ ] Handles declarados e aplicados com `useCssHandles` (ou contexto) no componente certo
- [ ] Estilos do tema usam **classes** (e whitelist) — exceto o mínimo necessário nos escopos `vtex.login` / `vtex.my-account` (conforme padrão do time)
- [ ] Seletores não conformes **restrictos** a `styles/css/vtex.login/**` e `styles/css/vtex.my-account/**` (não misturar com `vtex.store-components` etc. sem alinhamento)
- [ ] `manifest.json` inclui `vtex.css-handles` se o app expõe componentes com handles
- [ ] `vtex link` conferido: mensagem de “CSS validation was skipped” alinhada com os arquivos onde há CSS legado

---

## Erros comuns

| Problema | Causa provável | Ação |
|---|---|---|
| Link falha com erro de seletor CSS | Seletor fora da whitelist | Reescrever usando classes + handles |
| Tema "não pega" estilo | Seletor mirando outro bloco/versão | Conferir nome do handle e app no inspector |
| Classe duplicada / conflito | Dois apps, mesmo identificador de handle | Handles são únicos por app; use namespaces claros e `:global(vtex-...)` só conforme regra VTEX |
| Modificador não aplica | `withModifiers` incorreto ou CSS sem `handle--x` | Alinhar nome do modificador e regra no `.css` |

Se precisar de blocos, Site Editor, `interfaces.json` e padrão de arquivos: use **vtex-io-component** em conjunto com esta skill.
