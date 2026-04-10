# API Reference — vtex.css-handles

## useCssHandles(handles, options?)

Main hook. Creates unique CSS handles per app.

### Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `handles` | `string[]` | Yes | List of handle names |
| `options` | `CssHandlesOptions` | No | Extra configurations |

### CssHandlesOptions

| Key | Type | Default | Description |
|---|---|---|---|
| `migrationFrom` | `string \| string[]` | — | Legacy app IDs to generate additional handles |
| `classes` | `CustomCSSClasses` | `undefined` | Overrides handle definitions (received via props) |

### Return: CssHandlesBag

| Key | Type | Description |
|---|---|---|
| `handles` | `Record<string, string>` | Map of handle → generated CSS class |
| `withModifiers` | `(handle: string, modifiers: string \| string[]) => string` | Appends modifier suffixes to the handle |

### Generated class

Format: `vtex-{vendor}-{appName}-{major}-x-{handleName}`

Example: for app `lojamm.store-theme@10.x`, handle `container`:
```
lojamm-store-theme-10-x-container
```

---

## withModifiers(handle, modifiers)

Returned by `useCssHandles`. Generates classes with `--{modifier}` suffix.

```js
withModifiers('slide', ['active', 'first'])
// → "slide slide--active slide--first"
```

Falsy values are automatically ignored:
```js
withModifiers('item', [isSelected && 'selected', color])
// if isSelected=false, color='blue' → "item item--blue"
```

---

## useCustomClasses(classesFn, deps)

Hook for parent components that want to override children's handles.

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `classesFn` | `() => Record<string, CustomClassValue>` | Function returning a map of custom handles |
| `deps` | `any[]` | Dependencies (like `useEffect`) |

### CustomClassValue

Each value can be:
- `string` — replaces the class
- `CustomClassItem` — fine-grained control
- `Array<string | CustomClassItem>` — multiple classes

### CustomClassItem

| Key | Type | Default | Description |
|---|---|---|---|
| `name` | `string` | key name | Handle name |
| `withModifiers` | `boolean` | `true` | Whether `withModifiers` is allowed |

### Example

```js
import { useCustomClasses } from 'vtex.css-handles'

function Parent() {
  const classes = useCustomClasses(() => ({
    container: 'custom-wrapper parentContainer',
    title: ['bold', { name: 'parentTitle', applyModifiers: true }],
  }))

  return <Child classes={classes} />
}
```

---

## createCssHandlesContext(handles)

Creates a Provider and context hook to share handles across a deep component tree.

### Parameter

| Parameter | Type | Description |
|---|---|---|
| `handles` | `string[]` | Full list of handles (root + subcomponents) |

### Return

| Key | Type | Description |
|---|---|---|
| `CssHandlesProvider` | `React.Component` | Provider that receives `handles` and `withModifiers` |
| `useContextCssHandles` | `() => CssHandlesBag` | Hook to consume handles from context |

### Usage pattern

1. Root component calls `useCssHandles` with **all** handles (its own + children's)
2. Wraps children with `<CssHandlesProvider>`
3. Children use `useContextCssHandles()` instead of `useCssHandles`

Advantage: no `classes` prop drilling across multiple levels.

---

## applyModifiers (legacy)

Standalone utility function imported separately. Equivalent to `withModifiers` but as a standalone function.

```js
import { useCssHandles, applyModifiers } from 'vtex.css-handles'

// usage:
<div className={applyModifiers(handles.slide, ['active'])} />
```

Prefer `withModifiers` from the `useCssHandles` return in new code.

---

## manifest.json dependency

```json
{
  "dependencies": {
    "vtex.css-handles": "0.x"
  }
}
```

Version `0.x` is the most commonly used in store-themes. Version `1.x` exists but contains the same APIs.

## TypeScript typing

```ts
// react/typings/vtex.css-handles.ts
declare module 'vtex.css-handles'
```

---

# VTEX Site Editor Schema Reference

Schema defines what props are editable in VTEX Site Editor. Uses JSON Schema format. The root `schema` must be `type: 'object'` with `properties`.

Ref: [Site Editor schema examples](https://developers.vtex.com/docs/guides/vtex-io-documentation-site-editor-schema-examples)

## Property types

### string — Text input

```js
heading: {
  title: 'Título',
  type: 'string',
  default: 'Olá mundo',
  description: 'Texto exibido no topo',
}
```

### string — Image URL (paste link)

```js
imageDesktop: {
  type: 'string',
  title: 'Imagem Desktop',
  default: '',
  description: 'Cole a URL da imagem',
}
```

### string — Image upload (file picker)

```js
imageMobile: {
  title: 'Imagem Mobile',
  type: 'string',
  default: '',
  widget: {
    "ui:widget": "image-uploader"
  }
}
```

### string — Date (text format)

```js
initialDate: {
  type: 'string',
  title: 'Data Inicial',
  default: '',
  description: '{ano}/{mês}/{dia}',
}
```

### string — DateTime picker (widget)

```js
finalDate: {
  title: 'Data Final',
  type: 'string',
  format: 'date-time',
  default: new Date().toISOString(),
  widget: {
    "ui:widget": "datetime"
  }
}
```

### boolean — Toggle

```js
isVisible: {
  title: 'Exibir componente',
  type: 'boolean',
  default: true,
}
```

### number — Numeric input

```js
timeInterval: {
  title: 'Intervalo entre slides (segundos)',
  description: 'Recomendado entre 5 e 7 segundos',
  type: 'number',
  default: 6,
}
```

### enum — Dropdown (select from values)

```js
color: {
  type: 'string',
  title: 'Cor',
  default: 'red',
  enum: ['red', 'blue', 'black'],
}
```

### enum + enumNames — Dropdown with labels

```js
color: {
  type: 'string',
  title: 'Cor',
  default: '#0ff102',
  enum: ['#0ff102', '#1038c9', '#000000'],
  enumNames: ['Verde', 'Azul', 'Preto'],
}
```

### object — Nested group

```js
image: {
  title: 'Imagem',
  type: 'object',
  properties: {
    src: { type: 'string', title: 'URL da Imagem' },
    alt: { type: 'string', title: 'Texto Alternativo' },
    title: { type: 'string', title: 'Título' },
  }
}
```

### array — Repeatable list

```js
links: {
  title: 'Links',
  type: 'array',
  maxItems: 6,
  default: [],
  items: {
    type: 'object',
    title: 'Link',
    properties: {
      text: { type: 'string', title: 'Texto do link', default: '' },
      url: { type: 'string', title: 'URL de destino', default: '' },
      newTab: { type: 'boolean', title: 'Abrir em nova aba', default: false },
    }
  }
}
```

### array with __editorItemTitle — Editable item names in Site Editor

```js
items: {
  type: 'object',
  title: 'Item',
  properties: {
    __editorItemTitle: {
      title: 'Nome do item',
      type: 'string',
      default: 'Item',
    },
    // ... other props
  }
}
```

---

## Advanced schema: `dependencies` + `oneOf` (conditional fields)

Use `dependencies` with `oneOf` to show/hide fields in Site Editor based on a toggle or selection. When a user enables a boolean or selects a value, additional fields appear.

### How it works

1. Define the **trigger property** in `properties` (e.g. a boolean toggle)
2. Add `dependencies` at the same level as `properties`
3. Inside the dependency, use `oneOf` with an array of sub-schemas — each entry matches a possible value of the trigger

### Pattern: Boolean toggle reveals extra fields

```js
{
  type: 'object',
  properties: {
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
            maxResults: {
              title: 'Máximo de resultados',
              type: 'number',
              default: 10,
            },
          },
        },
      ],
    },
  },
}
```

When `showAdvanced` = `false`: only the toggle is visible.
When `showAdvanced` = `true`: `trackingId` and `maxResults` fields appear.

### Pattern: Enum selection reveals different fields

```js
{
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
              title: 'Intervalo (segundos)',
              type: 'number',
              default: 5,
            },
          },
        },
        {
          properties: {
            displayMode: { enum: ['grid'] },
            columns: {
              title: 'Colunas',
              type: 'number',
              default: 3,
            },
          },
        },
      ],
    },
  },
}
```

When `displayMode` = `carousel`: shows `autoplay` + `interval`.
When `displayMode` = `grid`: shows `columns`.

### Real-world example: vtex-apps/shelf

Ref: [shelf contentSchemas.json](https://github.com/vtex-apps/shelf/blob/master/store/contentSchemas.json)

```json
{
  "type": "object",
  "dependencies": {
    "advancedProperties": {
      "oneOf": [
        {
          "properties": {
            "advancedProperties": { "enum": [true] },
            "trackingId": {
              "title": "admin/editor.shelf.advanced-properties.tracking-id.title",
              "type": "string"
            }
          }
        }
      ]
    }
  },
  "properties": {
    "advancedProperties": {
      "title": "admin/editor.shelf.advanced-properties.title",
      "type": "boolean",
      "default": false
    }
  }
}
```

---

## `contentSchemas.json` and `$ref` / `definitions`

For complex apps, VTEX supports an **external schema file** at `store/contentSchemas.json`. This separates schema definitions from component code and enables reuse via `$ref`.

### File location

```
store/
└── contentSchemas.json
```

### Structure

```json
{
  "definitions": {
    "MyComponent": {
      "type": "object",
      "properties": {
        "title": { "title": "Título", "type": "string" },
        "strategy": { "$ref": "#/definitions/StrategyEnum" }
      }
    },
    "StrategyEnum": {
      "enum": ["OPTION_A", "OPTION_B"],
      "enumNames": ["Opção A", "Opção B"],
      "default": "OPTION_A"
    }
  }
}
```

### `$ref` — Referencing definitions

Use `$ref` to point to reusable sub-schemas:

| Syntax | Meaning |
|---|---|
| `"$ref": "#/definitions/MyDef"` | Reference a definition in the same file |
| `"$ref": "app:vtex.native-types#/definitions/text"` | Reference a definition from another VTEX app |

### When to use `contentSchemas.json` vs inline `schema`

| Scenario | Use |
|---|---|
| Simple component with few props | Inline `schema` on component |
| Shared sub-schemas across components | `contentSchemas.json` with `definitions` |
| Apps with many blocks needing structured config | `contentSchemas.json` |
| Props that reference VTEX native types | `$ref` to `app:vtex.native-types#/...` |

### `isLayout` flag

Properties can include `"isLayout": true` or `"isLayout": false` to tell Site Editor whether a prop affects layout (visual structure) or content. Layout props are grouped separately in the editor.

```js
maxItems: {
  title: 'Máximo de itens',
  type: 'number',
  default: 10,
  isLayout: true,
}
```

---

## Widget reference

| Widget | Renders | Use with |
|---|---|---|
| `"ui:widget": "image-uploader"` | File picker for images | `type: 'string'` |
| `"ui:widget": "datetime"` | Date-time picker | `type: 'string', format: 'date-time'` |
| `"ui:widget": "textarea"` | Multi-line text area | `type: 'string'` |
| `"ui:widget": "color"` | Color picker | `type: 'string'` |

## Schema structure rules

1. Root must be `type: 'object'` with `title` and `properties`
2. `title` and `description` in **Portuguese** (Site Editor language)
3. Always set `default` values for every property
4. Use `maxItems` on arrays to limit list size in the editor
5. Bind to component: `MyComponent.schema = schema`
6. Set defaultProps from schema defaults: `MyComponent.defaultProps = { ... }`
7. Sub-schemas (objects nested in arrays) use `items.properties`
8. For item renaming in lists, add `__editorItemTitle` to item properties
9. Use `dependencies` + `oneOf` for conditional fields that appear/hide based on a toggle or selection
10. Use `contentSchemas.json` with `definitions` and `$ref` for reusable sub-schemas across blocks
11. Use `isLayout` to flag properties that affect visual structure vs content
