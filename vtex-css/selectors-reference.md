# CSS Selectors — referência (VTEX IO)

Conteúdo alinhado à nota de release da VTEX sobre a deprecação de seletores CSS. Fonte: [bit.ly/io-css-selectors](https://bit.ly/io-css-selectors) (documentação "CSS Selectors deprecation") e políticas descritas no repositório store framework.

## Por que a VTEX restringe seletores

- Estilos baseados em **estrutura HTML** quebram quando a VTEX altera markup, ordem de nós ou atributos.
- **CSS Handles** são o contrato estável: permanecem válidos **durante a major version** do componente, segundo a documentação pública de Handles.

## Continua permitido (whitelist)

- Seletor de **classe**: `.foo`
- **Pseudo-classes** (lista da documentação): `:hover`, `:visited`, `:active`, `:disabled`, `:focus`, `:local`, `:not`, `:target`, `:first-child`, `:last-child`
- **Pseudo-elementos** (todos): `::before`, `::after`, `::placeholder`, etc.
- `:nth-child(even)` e `:nth-child(odd)` apenas
- Combinador **espaço** (descendente): `.foo .bar`
- Atributo **`[data-...]`** (qualquer atributo `data-*` conforme a nota; não use outros atributos no lugar de Handles sem revisar a política atual)
- **`:global(vtex-AppName-Version-ComponentName)`** — para selecionar elementos provenientes de **outro app** no padrão de identificação da VTEX (não use `:global` em classes genéricas que não sejam desse padrão)

## Depreciado / bloqueado em apps ainda não publicados (exemplos da documentação)

- Seletor de **tipo** (tag): `div`, `span`, `p`, `a`…
- Combinadores **>**, **+**, **~**
- `:nth-child` com **número** (diferente de `even`/`odd`)
- Seletores de atributo **exceto** `data-` — exemplos citados: `[class~="..."]` complexos, `[alt="..."]` como substituto de Handle
- Uso indevido de **`:global`** em classes que **não** sejam o padrão de outro app (Handles vtex-…)

## Lojas já em produção

- Temas **já publicados** podem, segundo a nota, continuar a **linkar e publicar** versões novas do tema **mesmo** com seletores fora da lista — isso evita trancar lojas legadas.
- Ainda assim, o risco de quebra de layout com mudanças de HTML continua; a **recomendação** é migrar tudo para Handles + whitelist.

## Ações práticas de migração

1. Listar regras em `*.css` do tema com `grep` por `> `, `~`, `+`, `div`, `span`, `nth-child(` com dígito, etc.
2. Para cada regra, identificar o **bloco** VTEX e o ponto a estilizar; mapear para **classe** exposta (Handle) ou ajuste no app que renderiza o componente.
3. Onde faltar Handle no componente nativo, considerar: **app próprio** que envolva o bloco com `useCssHandles` (theme ou custom app), respeitando a skill **vtex-io-component** para estrutura de arquivos e dependências.

## Links

- [CSS Selectors deprecation (VTEX) — link curto](https://bit.ly/io-css-selectors)
- [vtex-apps/css-handles — repositório](https://github.com/vtex-apps/css-handles)
