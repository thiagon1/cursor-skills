---
name: vtex-io-component
description: Creates custom React components for VTEX IO with CSS Handles, Site Editor schema, interfaces.json and block structure. Supports Figma URL input to extract layout via MCP before coding. Use when the user asks to create a VTEX IO React component, add CSS Handle, customize block styling, register component in interfaces.json, configure VTEX Site Editor schema (string, boolean, number, object, array, enum, image-uploader, datetime widget), or build a component from a Figma design.
---

# React Components for VTEX IO

Guide for creating custom React components in VTEX IO Store Theme projects (builder `react: 3.x`).

## Prerequisites

The `manifest.json` must contain:
```json
"dependencies": {
  "vtex.css-handles": "0.x",
  "vtex.render-runtime": "8.x"
}
```
And in `react/typings/`:
```ts
// vtex.css-handles.ts
declare module 'vtex.css-handles'
```

## File structure

```
react/
├── MyComponent.js                ← entry-point (import/export)
├── components/
│   └── MyComponent/
│       ├── index.js               ← main logic
│       ├── schema.js              ← VTEX schema (editable props in Site Editor)
│       ├── styles.css             ← local CSS (when using CSS Handles)
│       └── components/            ← internal subcomponents (optional)
store/
├── interfaces.json                ← maps block → React component
└── blocks/react-components/
    └── my-component/
        └── my-component.jsonc     ← block declaration
```

## Figma integration (optional)

When the user provides a **Figma URL**, extract the layout before coding the component.

### Parse the URL

From `https://figma.com/design/:fileKey/:fileName?node-id=1-2`:
- `fileKey` = `:fileKey`
- `nodeId` = `1:2` (replace `-` with `:`)

For branch URLs `https://figma.com/design/:fileKey/branch/:branchKey/:fileName`, use `branchKey` as `fileKey`.

### Step A — Get design context

```
server: user-Figma
toolName: get_design_context
arguments: {
  "fileKey": "<fileKey>",
  "nodeId": "<nodeId>",
  "clientLanguages": "javascript,css",
  "clientFrameworks": "react"
}
```

Returns: reference code (React + Tailwind), screenshot, and metadata.

**IMPORTANT:** The returned code is a REFERENCE, not final code. Adapt it to VTEX IO patterns:
- Replace Tailwind classes → CSS Handles (`useCssHandles`)
- Replace standard HTML → VTEX block structure
- Replace hardcoded values → `schema.js` editable props
- Replace image URLs → VTEX assets or props

### Step B — Get screenshot (if needed separately)

```
server: user-Figma
toolName: get_screenshot
arguments: { "fileKey": "<fileKey>", "nodeId": "<nodeId>" }
```

### Step C — Explore structure (large designs)

For complex designs, get the node tree first:

```
server: user-Figma
toolName: get_metadata
arguments: {
  "fileKey": "<fileKey>",
  "nodeId": "<nodeId>",
  "clientLanguages": "javascript,css",
  "clientFrameworks": "react"
}
```

Then call `get_design_context` on specific child nodes.

### Figma → VTEX IO mapping

| Figma concept | VTEX IO equivalent |
|---|---|
| Frame / Auto-layout | `flex-layout.row` / `flex-layout.col` with `blockClass` |
| Text layer | Prop in `schema.js` (editable in Site Editor) |
| Color / font | CSS Handle + theme style in `styles/css/` |
| Image | Prop `imageUrl` or VTEX `image#block` |
| Button | Prop + CSS Handle or VTEX `link.product` |
| Spacing / padding | CSS on the handle (e.g. `padding`, `gap`) |
| Component variant | `withModifiers` on the CSS Handle |
| Responsive breakpoint | Media queries in `styles.css` or VTEX responsive blocks |

### Workflow when Figma URL is provided

1. Call `get_design_context` with the URL
2. Analyze the screenshot and reference code
3. Map Figma layers → CSS Handles (name them semantically)
4. Map text content → `schema.js` props (Portuguese titles)
5. Create the component following the standard creation workflow below
6. Style the handles to match the Figma design

## Creation workflow

### 1. Register in interfaces.json

```json
{
  "n1-my-component": {
    "component": "MyComponent"
  }
}
```

For blocks with children:
```json
{
  "n1-my-component": {
    "component": "MyComponent",
    "composition": "children",
    "allowed": "*"
  }
}
```

### 2. Create entry-point (`react/MyComponent.js`)

```js
import MyComponent from './components/MyComponent'
export default MyComponent
```

### 3. Create component with CSS Handles

```js
import React from 'react'
import { useCssHandles } from 'vtex.css-handles'

const CSS_HANDLES = [
  'container',
  'title',
  'description',
  'actionButton',
]

function MyComponent({ heading, subtitle }) {
  const { handles, withModifiers } = useCssHandles(CSS_HANDLES)

  return (
    <div className={handles.container}>
      <h2 className={handles.title}>{heading}</h2>
      <p className={handles.description}>{subtitle}</p>
      <button className={withModifiers('actionButton', ['primary'])}>
        Action
      </button>
    </div>
  )
}

export default MyComponent
```

### 4. VTEX Schema (`schema.js`)

Title and description **always in Portuguese** (store editor language).
Uses JSON Schema format — see [reference.md](reference.md) for all schema types.

```js
export const schema = {
  title: 'Meu Componente',
  description: 'Descrição do componente em português',
  type: 'object',
  properties: {
    heading: { title: 'Título', type: 'string', default: 'Olá mundo' },
    isVisible: { title: 'Exibir', type: 'boolean', default: true },
    image: {
      title: 'Imagem', type: 'string', default: '',
      widget: { "ui:widget": "image-uploader" },
    },
    color: {
      title: 'Cor', type: 'string', default: 'red',
      enum: ['red', 'blue', 'black'],
      enumNames: ['Vermelho', 'Azul', 'Preto'],
    },
    links: {
      title: 'Links', type: 'array', maxItems: 6, default: [],
      items: {
        type: 'object', title: 'Link',
        properties: {
          __editorItemTitle: { title: 'Nome do item', type: 'string', default: 'Link' },
          text: { title: 'Texto', type: 'string', default: '' },
          url: { title: 'URL', type: 'string', default: '' },
        },
      },
    },
  },
}
```

Available types: `string`, `boolean`, `number`, `object`, `array`.
Widgets: `image-uploader`, `datetime`, `textarea`, `color`.
Dropdown: use `enum` + `enumNames` for labeled selects.
Arrays: use `items` with sub-properties; add `__editorItemTitle` for editable names.
Conditional fields: use `dependencies` + `oneOf` to show/hide props based on a toggle or selection.
Reusable schemas: use `store/contentSchemas.json` with `definitions` and `$ref` for complex apps.

Bind to the component:
```js
import { schema } from './schema'
MyComponent.schema = schema
MyComponent.defaultProps = {
  heading: schema.properties.heading.default,
  isVisible: schema.properties.isVisible.default,
}
```

#### Array props (lists of items)

When a component accepts a **repeatable list** of items (links, banners, slides, etc.), use `type: 'array'` with `items` defining the shape of each entry. **NEVER** use flat "slot" props like `item1Text`, `item2Text` — always use a proper JSON Schema array.

The VTEX Site Editor renders arrays as an "add item" UI, where each item expands into its own form.

```js
const linkItemSchema = {
  type: 'object',
  properties: {
    text: {
      title: 'Texto do link',
      type: 'string',
      default: '',
    },
    url: {
      title: 'URL de destino',
      type: 'string',
      default: '',
    },
    newTab: {
      title: 'Abrir em nova aba',
      type: 'boolean',
      default: false,
    },
  },
}

export const schema = {
  title: 'Meu Componente com Lista',
  type: 'object',
  properties: {
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

Key rules for arrays:
- **`items`** defines the schema each array entry must follow (like JSON Schema spec)
- **`maxItems`** limits how many entries the editor allows (optional but recommended)
- **`minItems`** sets a minimum (optional)
- **`default`** should be `[]` (empty array)
- In the component, always guard with `Array.isArray(prop)` before mapping
- **NEVER** create flat numbered props (`item1`, `item2`, etc.) — use arrays instead

### 5. Declare JSONC block

```jsonc
// store/blocks/react-components/my-component/my-component.jsonc
{
  "n1-my-component#default": {
    "title": "My Component",
    "props": {
      "heading": "Welcome"
    }
  }
}
```

## CSS Handles — Rules

### Naming conventions

- Names in **camelCase**: `containerWrapper`, `priceLabel`, `actionButton`
- Semantic: describe **what** the element is, not **how** it looks
- Prefix with context when needed: `modalOverlay`, `modalTitle`, `modalClose`

### useCssHandles — basic usage

```js
import { useCssHandles } from 'vtex.css-handles'

const CSS_HANDLES = ['container', 'title'] as const

function Component({ classes }) {
  const { handles, withModifiers } = useCssHandles(CSS_HANDLES, { classes })
  return <div className={handles.container}>...</div>
}
```

The generated class follows the format: `vtex-{appVendor}-{appName}-{major}-x-{handleName}`

### withModifiers — states and variants

Useful for visual states (active/inactive, variants, colors):

```js
<div className={withModifiers('item', [isActive && 'active', color])}>
```

Generates classes like: `item item--active item--blue`

### migrationFrom — migration between apps

When a component migrates from one app to another, preserve legacy handles:

```js
const handles = useCssHandles(CSS_HANDLES, {
  migrationFrom: 'vtex.search-result@3.x',
  classes,
})
```

### createCssHandlesContext — components with subcomponents

When multiple components of the same block need to share handles, avoid prop drilling:

```js
// cssHandlesContext.js
import { createCssHandlesContext } from 'vtex.css-handles'
import { CSS_HANDLES } from './PublicComponent'

export const { CssHandlesProvider, useContextCssHandles } =
  createCssHandlesContext(CSS_HANDLES)
```

Root component:
```js
export const CSS_HANDLES = ['root', ...SubComponent.cssHandles]

function PublicComponent({ classes }) {
  const { handles } = useCssHandles(CSS_HANDLES, { classes })
  return (
    <CssHandlesProvider handles={handles}>
      <SubComponent />
    </CssHandlesProvider>
  )
}
```

Subcomponent:
```js
import { useContextCssHandles } from './cssHandlesContext'

const CSS_HANDLES = ['nested']

function SubComponent() {
  const { handles } = useContextCssHandles()
  return <div className={handles.nested}>...</div>
}

SubComponent.cssHandles = CSS_HANDLES
```

## Alternative approach: local CSS (`import styles`)

For components that **do not** need to expose handles for external customization:

```js
import styles from './styles.css'

function Component() {
  return <div className={styles.container}>...</div>
}
```

The `styles.css` file declares empty classes that the bundler transforms into scoped classes:
```css
.container {}
.title {}
```

**When to use each approach:**

| Scenario | Approach |
|---|---|
| Component that other apps will customize | `useCssHandles` |
| Isolated component, self-contained styling | `import styles from './styles.css'` |
| Migration between apps | `useCssHandles` with `migrationFrom` |
| Block with deeply nested subcomponents | `createCssHandlesContext` |

## Theme styling

Component styles live in `styles/scss/` or `styles/css/`:

```scss
// styles/scss/react-components/my-component/vtex.flex-layout.scss
.flexRow--my-component-container :global(.lojamm-store-theme-0-x-title) {
  font-size: 20px;
  font-weight: 700;
}
```

The selector follows: `.{vtexParentBlock}--{blockClass} :global(.{fullHandleName})`

## SSR and canUseDOM

For code that accesses `window`, `document` or `localStorage`:

```js
import { canUseDOM } from 'vtex.render-runtime'

useEffect(() => {
  if (!canUseDOM) return
  // safe client-side code
}, [])
```

## Checklist

- [ ] Entry-point at `react/ComponentName.js`
- [ ] Component at `react/components/ComponentName/index.js`
- [ ] Registered in `store/interfaces.json`
- [ ] Block declared in `store/blocks/react-components/`
- [ ] CSS Handles declared as `const` with camelCase names
- [ ] Schema with title/description in Portuguese
- [ ] Repeatable items use `type: 'array'` with `items` — **never** flat slot props
- [ ] `canUseDOM` before accessing browser APIs
- [ ] defaultProps derived from schema

## Additional resources

- For the full CSS Handles API, see [reference.md](reference.md)
- For real project examples, see [examples.md](examples.md)
