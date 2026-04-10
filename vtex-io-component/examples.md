# Examples — VTEX IO Components from this project

## 1. Simple component with local CSS (`import styles`)

`HeaderDeliveryCep` uses `import styles from './styles.css'` for local scoping.

### Entry-point (`react/HeaderDeliveryCep.js`)

```js
import HeaderDeliveryCep from './components/HeaderDeliveryCep'
export default HeaderDeliveryCep
```

### Component (`react/components/HeaderDeliveryCep/index.js`)

```js
import React, { useCallback, useEffect, useRef, useState } from 'react'
import { canUseDOM } from 'vtex.render-runtime'
import styles from './styles.css'
import { schema } from './schema'

// JSX usage:
<div className={styles.triggerAnchor}>
  <button className={styles.trigger}>
    <span className={styles.triggerLabel}>{label}</span>
  </button>
</div>

// Schema binding:
HeaderDeliveryCep.schema = schema
HeaderDeliveryCep.defaultProps = {
  blockRole: 'trigger',
  modalTitle: schema.properties.modalTitle.default,
}
```

### Local CSS (`styles.css`)

```css
.trigger {
  display: flex;
  align-items: flex-start;
  gap: 4px;
  background: none;
  border: none;
  cursor: pointer;
  color: #fff;
}

.triggerLabel {
  font-size: 11px;
  font-weight: 400;
}

.triggerValue {
  font-size: 13px;
  font-weight: 600;
}
```

### interfaces.json

```json
{
  "n1-header-delivery-cep": {
    "component": "HeaderDeliveryCep"
  }
}
```

### Block JSONC usage

```jsonc
{
  "n1-header-delivery-cep#header-delivery-trigger": {
    "title": "CEP — trigger (next to search)",
    "props": {
      "blockRole": "trigger"
    }
  }
}
```

---

## 2. Component with useCssHandles (basic)

`DisclosureLayout` uses `useCssHandles` to expose customizable handles.

```js
import React from 'react'
import { useCssHandles } from 'vtex.css-handles'

const CSS_HANDLES = ['disclosureLayout']

const DisclosureLayout = ({ children, className = '' }) => {
  const handles = useCssHandles(CSS_HANDLES)

  return (
    <div className={`${handles.disclosureLayout} ${className}`.trim()}>
      {children}
    </div>
  )
}

export default DisclosureLayout
```

---

## 3. Component with multiple handles and states

`DisclosureTrigger` demonstrates handles for visual states.

```js
import React from 'react'
import { useCssHandles } from 'vtex.css-handles'

const CSS_HANDLES = [
  'disclosureTrigger',
  'disclosureTriggerButton',
  'disclosureTriggerText',
  'disclosureTriggerIcon',
  'disclosureTriggerExpanded',
  'disclosureTriggerCollapsed',
]

const DisclosureTrigger = ({ onClick, isExpanded = false, text = 'Show more' }) => {
  const handles = useCssHandles(CSS_HANDLES)

  const classes = [
    handles.disclosureTrigger,
    handles.disclosureTriggerButton,
    isExpanded ? handles.disclosureTriggerExpanded : handles.disclosureTriggerCollapsed,
  ].join(' ')

  return (
    <p className={classes} onClick={onClick} aria-expanded={isExpanded}>
      <span className={handles.disclosureTriggerText}>{text}</span>
      <span className={handles.disclosureTriggerIcon}>▼</span>
    </p>
  )
}

export default DisclosureTrigger
```

---

## 4. Component with migrationFrom and classes

`PriceRangeCustom` preserves handles from another VTEX app.

```js
import { useCssHandles } from 'vtex.css-handles'

const CSS_HANDLES = ['filterTemplateOverflow']

const PriceRangeCustom = ({ classes, ... }) => {
  const handles = useCssHandles(CSS_HANDLES, {
    migrationFrom: 'vtex.search-result@3.x',
    classes,
  })

  return <div className={handles.filterTemplateOverflow}>...</div>
}
```

---

## 5. Full VTEX schemas — Real project examples

### 5a. Schema with enum/enumNames — `HeaderDeliveryCep`

```js
export const schema = {
  title: 'Header — CEP / entrega',
  description: 'Use "Gatilho" ao lado da busca e "Linha de endereço" abaixo do campo de busca.',
  type: 'object',
  properties: {
    blockRole: {
      title: 'Função do bloco',
      type: 'string',
      enum: ['trigger', 'deliveryLine'],
      enumNames: ['Gatilho (ícone + texto)', 'Linha "Entregar em…"'],
      default: 'trigger',
    },
    modalTitle: {
      title: 'Título do modal',
      type: 'string',
      default: 'Informe seu CEP',
    },
    placeholderCep: {
      title: 'Placeholder do CEP',
      type: 'string',
      default: '00000-000',
    },
  },
}
```

### 5b. Schema with array + boolean + number — `TopbarMenuLinks`

```js
const linkItemSchema = {
  type: 'object',
  properties: {
    SVGIcone: { title: 'SVG Ícone', type: 'string', default: '' },
    text: { title: 'Texto do link', type: 'string', default: '' },
    url: { title: 'URL de destino', type: 'string', default: '' },
    newTab: { title: 'Abrir em nova aba', type: 'boolean', default: false },
  },
}

export const schema = {
  title: 'Top bar — menu de links',
  description: 'Desktop: até 6 links. Mobile: até 3 textos em carrossel.',
  type: 'object',
  properties: {
    isVisible: { title: 'Exibir faixa', type: 'boolean', default: true },
    showSlides: { title: 'Exibir slides', type: 'boolean', default: false },
    timeInterval: {
      title: 'Tempo de intervalo entre slides',
      description: 'Recomendado entre 5 e 7 segundos.',
      type: 'number',
      default: 6,
    },
    links: {
      title: 'Links',
      type: 'array',
      maxItems: 6,
      items: linkItemSchema,
      default: [],
    },
  },
}
```

### 5c. Schema with image-uploader widget

```js
export const schema = {
  title: 'Banner — imagem responsiva',
  type: 'object',
  properties: {
    imageDesktop: {
      type: 'string',
      title: 'Imagem Desktop',
      default: '',
      description: 'Cole a URL da imagem',
    },
    imageMobile: {
      title: 'Imagem Mobile',
      type: 'string',
      default: '',
      widget: { "ui:widget": "image-uploader" },
    },
    alt: {
      title: 'Texto alternativo',
      type: 'string',
      default: '',
    },
  },
}
```

### 5d. Schema with datetime widget

```js
export const schema = {
  title: 'Componente de Promoção',
  type: 'object',
  properties: {
    startDate: {
      type: 'string',
      title: 'Data de Início',
      default: '',
      description: '{ano}/{mês}/{dia}',
    },
    endDate: {
      title: 'Data de Término',
      type: 'string',
      format: 'date-time',
      default: new Date().toISOString(),
      widget: { "ui:widget": "datetime" },
    },
    active: {
      title: 'Promoção ativa',
      type: 'boolean',
      default: true,
    },
  },
}
```

### 5e. Schema with nested object

```js
export const schema = {
  title: 'Card de Produto',
  type: 'object',
  properties: {
    image: {
      title: 'Imagem',
      type: 'object',
      properties: {
        src: { type: 'string', title: 'URL da Imagem', description: 'URL' },
        alt: { type: 'string', title: 'Texto Alternativo' },
        title: { type: 'string', title: 'Título da imagem' },
      },
    },
  },
}
```

### 5f. Schema with array + __editorItemTitle

```js
export const schema = {
  title: 'Galeria de Imagens',
  type: 'object',
  properties: {
    images: {
      type: 'array',
      title: 'Imagens',
      default: [{ src: '', alt: 'Texto alternativo', mobileSrc: '' }],
      items: {
        type: 'object',
        title: 'Imagem',
        properties: {
          __editorItemTitle: {
            title: 'Nome do item',
            type: 'string',
            default: 'Imagem',
          },
          src: {
            type: 'string',
            title: 'Imagem Desktop',
            description: 'URL da imagem [desktop]',
          },
          alt: { type: 'string', title: 'Texto Alternativo' },
          mobileSrc: {
            type: 'string',
            title: 'Imagem Mobile',
            description: 'URL da imagem [mobile]',
          },
        },
      },
    },
  },
}
```

### 5g. Schema with `dependencies` + `oneOf` — Conditional fields

```js
export const schema = {
  title: 'Vitrine de Produtos',
  type: 'object',
  properties: {
    category: {
      title: 'Categoria',
      type: 'string',
      default: '',
    },
    orderBy: {
      title: 'Ordenação',
      type: 'string',
      enum: ['', 'OrderByTopSaleDESC', 'OrderByPriceDESC', 'OrderByPriceASC'],
      enumNames: ['Relevância', 'Mais vendidos', 'Maior preço', 'Menor preço'],
      default: '',
    },
    showAdvanced: {
      title: 'Exibir opções avançadas',
      type: 'boolean',
      default: false,
    },
  },
  dependencies: {
    showAdvanced: {
      oneOf: [
        {
          properties: {
            showAdvanced: { enum: [false] },
          },
        },
        {
          properties: {
            showAdvanced: { enum: [true] },
            trackingId: {
              title: 'ID de rastreamento',
              type: 'string',
              default: '',
            },
            maxItems: {
              title: 'Máximo de itens',
              type: 'number',
              default: 10,
            },
            hideUnavailable: {
              title: 'Ocultar produtos indisponíveis',
              type: 'boolean',
              default: false,
            },
          },
        },
      ],
    },
  },
}
```

### 5h. `contentSchemas.json` with `$ref` and `definitions`

File: `store/contentSchemas.json` — used for complex apps with reusable sub-schemas.

```json
{
  "definitions": {
    "MyShelf": {
      "type": "object",
      "properties": {
        "title": {
          "title": "Título",
          "type": "string"
        },
        "strategy": {
          "title": "Estratégia",
          "$ref": "#/definitions/ShelfStrategy"
        },
        "maxItems": {
          "title": "Máximo de itens",
          "type": "number",
          "default": 10,
          "isLayout": true
        }
      }
    },
    "ShelfStrategy": {
      "enum": ["BOUGHT_TOGETHER", "SIMILAR", "VIEWED_TOGETHER"],
      "enumNames": ["Comprados juntos", "Similares", "Vistos juntos"],
      "default": "BOUGHT_TOGETHER"
    }
  }
}
```

### 5i. Schema with `oneOf` on enum selection — Different fields per mode

```js
export const schema = {
  title: 'Componente Display',
  type: 'object',
  properties: {
    displayMode: {
      title: 'Modo de exibição',
      type: 'string',
      enum: ['carousel', 'grid'],
      enumNames: ['Carrossel', 'Grade'],
      default: 'carousel',
    },
  },
  dependencies: {
    displayMode: {
      oneOf: [
        {
          properties: {
            displayMode: { enum: ['carousel'] },
            autoplay: {
              title: 'Reprodução automática',
              type: 'boolean',
              default: false,
            },
            interval: {
              title: 'Intervalo entre slides (seg)',
              type: 'number',
              default: 5,
            },
            arrows: {
              title: 'Exibir setas',
              type: 'boolean',
              default: true,
            },
          },
        },
        {
          properties: {
            displayMode: { enum: ['grid'] },
            columns: {
              title: 'Colunas por linha',
              type: 'number',
              default: 3,
            },
            gap: {
              title: 'Espaçamento',
              type: 'string',
              enum: ['none', 'small', 'medium', 'large'],
              enumNames: ['Nenhum', 'Pequeno', 'Médio', 'Grande'],
              default: 'medium',
            },
          },
        },
      ],
    },
  },
}
```

---

## 6. Subcomponent folder structure

Example from `ButtonAddToCart` with `components/` subfolder:

```
react/
├── ButtonAddToCart.js           ← entry-point
└── components/
    └── ButtonAddToCart/
        ├── index.js             ← main component
        └── components/
            ├── AddToCartButton.js  ← uses useCssHandles
            └── Modal.js            ← uses separate useCssHandles
```

Each subcomponent declares its own `CSS_HANDLES`:

```js
// AddToCartButton.js
const CSS_HANDLES = ['addToCartButton', 'addToCartButtonIcon']
const handles = useCssHandles(CSS_HANDLES, {
  migrationFrom: ['vtex.add-to-cart-button@0.x'],
})

// Modal.js
const CSS_HANDLES = ['buttonCancel', 'buttonContinue']
const handles = useCssHandles(CSS_HANDLES)
```
