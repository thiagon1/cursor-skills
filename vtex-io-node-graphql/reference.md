# VTEX IO Node.js + GraphQL — API Reference

Detailed reference for client types, REST routes, event handling, path patterns, authentication, and HttpClient methods.

## Client types

| Type | Import | Use case |
|---|---|---|
| `ExternalClient` | `@vtex/api` | External REST APIs (GitHub, ViaCEP, etc.) |
| `JanusClient` | `@vtex/api` | VTEX Core Commerce APIs via Janus Router |
| `MasterData` | `@vtex/api` | VTEX Master Data CRUD operations |
| `AppClient` | `@vtex/api` | Communication with other IO services via HTTP |
| `AppGraphQLClient` | `@vtex/api` | Communication with other IO GraphQL services |
| `InfraClient` | `@vtex/api` | VTEX IO Infra services |

### ExternalClient

- `baseUrl` in `super()` must start with `http://`
- For HTTPS, set header `'x-vtex-use-https': 'true'`
- Use `metric` parameter for analytics tracking
- Use `private routes` map for cleaner code

```ts
import type { IOContext, InstanceOptions } from '@vtex/api'
import { ExternalClient } from '@vtex/api'

export default class MyApiClient extends ExternalClient {
  private routes = {
    data: (id: string) => `/api/data/${id}`,
    search: () => '/api/search',
  }

  constructor(context: IOContext, options?: InstanceOptions) {
    super('http://api.example.com', context, {
      ...options,
      retries: 2,
      headers: {
        Accept: 'application/json',
        'x-vtex-use-https': 'true',
        ...options?.headers,
      },
    })
  }

  public getData(id: string) {
    return this.http.get(this.routes.data(id), { metric: 'api-get-data' })
  }

  public searchData(query: string) {
    return this.http.get(this.routes.search(), {
      metric: 'api-search',
      params: { q: query },
    })
  }
}
```

### JanusClient (VTEX Core Commerce APIs)

Use for Checkout, Catalog, OMS, Pricing, and other VTEX internal APIs.

```ts
import type { InstanceOptions, IOContext } from '@vtex/api'
import { JanusClient } from '@vtex/api'

export default class CheckoutClient extends JanusClient {
  constructor(context: IOContext, options?: InstanceOptions) {
    super(context, {
      ...options,
      headers: {
        Accept: 'application/json',
        VtexIdclientAutCookie: context.storeUserAuthToken,
        'x-vtex-user-agent': context.userAgent,
        ...options?.headers,
      },
    })
  }

  public getOrderForm(orderFormId: string) {
    return this.http.get(`/api/checkout/pub/orderForm/${orderFormId}`, {
      metric: 'checkout-get-orderform',
    })
  }
}
```

Required policy in `manifest.json`:
```json
{
  "name": "outbound-access",
  "attrs": {
    "host": "{{account}}.vtexcommercestable.com.br",
    "path": "/api/checkout/pub/orderForm/*"
  }
}
```

### MasterData client

```ts
import type { IOContext, InstanceOptions } from '@vtex/api'
import { MasterData } from '@vtex/api'

export default class MDClient extends MasterData {
  constructor(ctx: IOContext, options?: InstanceOptions) {
    super(ctx, { ...options })
  }

  public searchDocs(email: string) {
    return this.searchDocuments({
      dataEntity: 'MY',
      fields: ['id', 'name', 'email'],
      where: `email='${email}'`,
      pagination: { page: 1, pageSize: 10 },
    })
  }

  public createDoc(data: Record<string, unknown>) {
    return this.createDocument({ dataEntity: 'MY', fields: data })
  }

  public scrollDocs(size: number, sort: string) {
    return this.scrollDocuments({
      dataEntity: 'MY',
      fields: ['id', 'name'],
      schema: 'v1',
      size,
      sort,
    }).then(({ data }) => data)
  }
}
```

Required policy:
```json
{ "name": "ADMIN_DS" }
```

## HttpClient methods

| Method | Returns | Description |
|---|---|---|
| `get(url, config?)` | body | GET request, returns response body |
| `getRaw(url, config?)` | full response | GET with headers, status |
| `getWithBody(url, data?, config?)` | body | GET with request body |
| `getBuffer(url, config?)` | buffer + headers | GET as buffer |
| `getStream(url, config?)` | IncomingMessage | GET as readable stream |
| `post(url, data?, config?)` | body | POST request |
| `postRaw(url, data?, config?)` | full response | POST with headers, status |
| `put(url, data?, config?)` | body | PUT request |
| `putRaw(url, data?, config?)` | full response | PUT with headers, status |
| `patch(url, data?, config?)` | body | PATCH request |
| `head(url, config?)` | void | HEAD request |
| `delete(url, config?)` | void | DELETE request |

### RequestConfig options

| Option | Type | Description |
|---|---|---|
| `metric` | string | Name for analytics tracking |
| `headers` | object | Per-request headers |
| `params` | object | Query string parameters (`?key=value`) |
| `timeout` | number | Per-request timeout (ms) |
| `forceMaxAge` | number | Force cache max-age (seconds) |

## InstanceOptions

| Option | Description |
|---|---|
| `authType` | Authentication type |
| `timeout` | Request timeout (ms) |
| `memoryCache` | Memory cache layer |
| `diskCache` | Disk cache layer |
| `baseURL` | Base URL for requests |
| `retries` | Number of retries on failure |
| `exponentialTimeoutCoefficient` | Exponential timeout backoff factor |
| `initialBackoffDelay` | Initial backoff delay (ms) |
| `exponentialBackoffCoefficient` | Exponential backoff retry factor |
| `concurrency` | Max concurrent requests |
| `headers` | Default headers |
| `params` | Default query params |
| `verbose` | Verbose logging |

## Authentication

IO apps do NOT need appKey/appToken for VTEX Core Commerce APIs. Each app has a rotating token:

| Token | Access via | Use case |
|---|---|---|
| App token | `ctx.authToken` | Default app-level auth |
| Store user | `ctx.vtex.storeUserAuthToken` | Storefront user context |
| Admin user | `ctx.vtex.adminUserAuthToken` | Admin panel context |

Set the appropriate token in the `VtexIdclientAutCookie` header.

## REST routes

### Defining routes in `service.json`

```json
{
  "memory": 256,
  "ttl": 10,
  "timeout": 2,
  "minReplicas": 2,
  "maxReplicas": 4,
  "routes": {
    "myData": {
      "path": "/_v/my-app/data/:id",
      "public": true
    }
  }
}
```

### Path patterns

| Pattern | Cookies | Cache | Use case |
|---|---|---|---|
| `{path}` | Not guaranteed | Edge cached | Static data, public info |
| `/_v/segment/{path}` | `vtex_segment` | Segment-based | Promotions by currency/region |
| `/_v/private/{path}` | segment + session | No cache | User-specific data (orders) |

### Dynamic routes (wildcard)

For variable-length paths, use `*path`:
```json
"routes": {
  "productSearch": {
    "path": "/_v/api/search/*path",
    "public": true
  }
}
```

Access in handler:
```ts
const { path = '' } = ctx.vtex.route.params
const segments = path.split('/').filter((s: string) => s !== '')
```

### Middleware handler

```ts
export async function myHandler(ctx: Context, next: () => Promise<void>) {
  const { id } = ctx.vtex.route.params
  try {
    const data = await ctx.clients.myClient.getData(id)
    ctx.body = data
    ctx.status = 200
  } catch (error) {
    ctx.body = { error: 'Not found' }
    ctx.status = 404
  }
  await next()
}
```

### Registering routes in `node/index.ts`

```ts
import { method, Service } from '@vtex/api'
import { myHandler } from './middlewares/myHandler'

export default new Service({
  clients,
  routes: {
    myData: method({
      GET: [myHandler],
      POST: [validateMiddleware, createHandler],
    }),
  },
  graphql: { resolvers },
})
```

## Event handling

Events are workspace and account-bound. They enable async workflows.

### Declare events in `service.json`

```json
{
  "events": {
    "orderCreated": {
      "sender": "vtex.orders-broadcast",
      "keys": ["order-created"]
    }
  }
}
```

### Create event handler

```ts
// node/events/orderCreated.ts
export async function handleOrderCreated(ctx: Context) {
  const { body } = ctx
  console.log('Order event received:', body)
  // Process the event...
}
```

### Register in `node/index.ts`

```ts
import { handleOrderCreated } from './events/orderCreated'

export default new Service({
  clients: {
    implementation: Clients,
    options: {
      default: { retries: 2, timeout: 10000 },
      events: {
        exponentialTimeoutCoefficient: 2,
        exponentialBackoffCoefficient: 2,
        initialBackoffDelay: 50,
        retries: 1,
        timeout: 3000,
        concurrency: 10,
      },
    },
  },
  events: {
    orderCreated: handleOrderCreated,
  },
  graphql: { resolvers },
})
```

### Event client options

| Option | Type | Description |
|---|---|---|
| `exponentialTimeoutCoefficient` | int | Timeout increase factor per retry |
| `exponentialBackoffCoefficient` | int | Backoff increase factor per retry |
| `initialBackoffDelay` | int (ms) | Wait before next retry |
| `retries` | int | Max retry attempts |
| `timeout` | int (ms) | Timeout per attempt |
| `concurrency` | int | Simultaneous event processes |

## Node builder 7.x notes

- Uses Node.js 20 engine and TypeScript 5.x
- Ensure `typescript: "5.x"` in `node/package.json` devDependencies
- `global.metrics` → use `(global as any).metrics` due to `@types/node` 20.x breaking change
- `tsconfig.json` target is overridden to `es2019` by the builder

## service.json full reference

```json
{
  "memory": 256,
  "ttl": 10,
  "timeout": 2,
  "minReplicas": 2,
  "maxReplicas": 4,
  "workers": 1,
  "routes": {},
  "events": {}
}
```

| Field | Type | Description |
|---|---|---|
| `memory` | int | Memory allocation in MB (auto-adjusted if exceeded) |
| `ttl` | int | Time-to-live for the service (seconds) |
| `timeout` | int | Max request duration (seconds) |
| `minReplicas` | int | Minimum running replicas |
| `maxReplicas` | int | Maximum replicas under load |
| `workers` | int | Number of worker processes |
| `routes` | object | REST route definitions |
| `events` | object | Event listener definitions |

## Documentation links

- [Using Node Clients](https://developers.vtex.com/docs/guides/using-node-clients)
- [Developing Clients](https://developers.vtex.com/docs/guides/vtex-io-documentation-how-to-create-and-use-clients)
- [Connecting to VTEX Core Commerce APIs](https://developers.vtex.com/docs/guides/how-to-connect-with-vtex-core-commerce-apis-using-vtex-io)
- [Service path patterns](https://developers.vtex.com/docs/guides/service-path-patterns)
- [Dynamic routes](https://developers.vtex.com/docs/guides/configuring-dynamic-routes-in-vtex-io-services)
- [Service configuration apps](https://developers.vtex.com/docs/guides/vtex-io-documentation-developing-service-configuration-apps)
- [Node builder 7.x migration](https://developers.vtex.com/docs/guides/node-builder-7x-migration-guide)
- [Getting started (boilerplate)](https://developers.vtex.com/docs/guides/services-1-getting-started-with-the-boilerplate)
- [Handling events](https://developers.vtex.com/docs/guides/services-2-handling-and-receiving-events)
- [GraphQL with Master Data](https://developers.vtex.com/docs/guides/services-6-graphql-retrieving-data-from-master-data)
- [GraphiQL IDE](https://developers.vtex.com/docs/guides/services-7-using-graphiql)
- [Calling Commerce APIs](https://developers.vtex.com/docs/guides/calling-commerce-apis-1-getting-the-service-app-boilerplate)
