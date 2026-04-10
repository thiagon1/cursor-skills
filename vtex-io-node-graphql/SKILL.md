---
name: vtex-io-node-graphql
description: Creates Node.js backend services and GraphQL APIs in VTEX IO, including resolvers, clients, schema types, and React component integration via react-apollo. Use when the user asks to create a Node.js API, GraphQL resolver, custom client, mutation, query, or integrate backend with a React component in VTEX IO.
---

# Node.js + GraphQL Backend for VTEX IO

Guide for creating backend services with Node.js builder (`node: 7.x`) and GraphQL builder (`graphql: 2.x`) in VTEX IO, and integrating with custom React components via `react-apollo`.

## Prerequisites

The `manifest.json` must include these builders and dependencies:
```json
"builders": {
  "node": "7.x",
  "graphql": "2.x",
  "react": "3.x"
},
"dependencies": {
  "vtex.render-runtime": "8.x"
}
```

For external API access, add policies to `manifest.json`:
```json
"policies": [
  {
    "name": "outbound-access",
    "attrs": {
      "host": "api.example.com",
      "path": "/api/*"
    }
  }
]
```

## File structure

```
node/
├── index.ts               ← Service entry-point (clients + resolvers)
├── service.json           ← Worker resources (memory, replicas, timeout)
├── package.json           ← Dependencies (@vtex/api)
├── tsconfig.json          ← TypeScript config
├── clients/
│   ├── index.ts           ← IOClients class (registers all clients)
│   └── myClient.ts        ← Custom client (ExternalClient or MasterData)
└── resolvers/
    ├── index.ts           ← Aggregates all Query/Mutation resolvers
    └── myFeature.ts       ← Feature-specific resolvers

graphql/
├── schema.graphql         ← Root schema (Query + Mutation + directives)
└── types/
    └── myFeature.graphql  ← Type definitions for the feature

react/
├── components/
│   └── MyComponent/
│       ├── index.js       ← Component using react-apollo hooks
│       └── graphql/
│           ├── myQuery.gql      ← Query file
│           └── myMutation.gql   ← Mutation file
└── typings/
    └── graphql.d.ts       ← Module declarations for .gql/.graphql
```

## Step-by-step workflow

### 1. Define GraphQL schema (`graphql/schema.graphql`)

Every query and mutation **must** have the `@auth` directive (required by graphql builder `2.x`).

```graphql
type Query {
  getMyData(id: String!): MyDataResponse
    @auth(scope: PUBLIC)
    @cacheControl(scope: PRIVATE, maxAge: 0)
}

type Mutation {
  createMyData(input: MyDataInput!): MyDataResult
    @auth(scope: PUBLIC)
    @cacheControl(scope: PUBLIC, maxAge: 0)
}
```

### 2. Define types (`graphql/types/myFeature.graphql`)

```graphql
type MyDataResponse {
  id: String
  name: String
  value: Int
}

type MyDataResult {
  success: Boolean!
  message: String!
  data: MyDataResponse
}

input MyDataInput {
  name: String!
  value: Int!
}
```

### 3. Create a custom client (`node/clients/myClient.ts`)

#### ExternalClient (for external REST APIs)

```ts
import type { InstanceOptions, IOContext } from '@vtex/api'
import { ExternalClient } from '@vtex/api'

export default class MyClient extends ExternalClient {
  constructor(context: IOContext, options?: InstanceOptions) {
    super(
      `https://api.example.com`,
      context,
      {
        ...options,
        headers: {
          Authorization: context.authToken,
        },
      }
    )
  }

  public async getData(id: string) {
    return this.http.get(`/data/${id}`)
  }

  public async createData(payload: Record<string, unknown>) {
    return this.http.post('/data', payload)
  }
}
```

#### MasterData client (for VTEX Master Data)

```ts
import type { IOContext, InstanceOptions } from '@vtex/api'
import { MasterData } from '@vtex/api'

export default class MyMDClient extends MasterData {
  constructor(ctx: IOContext, options?: InstanceOptions) {
    super(ctx, { ...options })
  }

  public async search(email: string) {
    return this.searchDocuments({
      dataEntity: 'MY',
      fields: ['id', 'name', 'email'],
      where: `email='${email}'`,
      pagination: { page: 1, pageSize: 10 },
    })
  }

  public async create(data: Record<string, unknown>) {
    return this.createDocument({
      dataEntity: 'MY',
      fields: data,
    })
  }
}
```

#### VTEX internal API client

```ts
import type { InstanceOptions, IOContext } from '@vtex/api'
import { ExternalClient } from '@vtex/api'

export default class VtexApiClient extends ExternalClient {
  constructor(context: IOContext, options?: InstanceOptions) {
    super(
      `http://${context.account}.vtexcommercestable.com.br/api`,
      context,
      {
        ...options,
        headers: {
          VtexIdClientAutCookie:
            context.adminUserAuthToken ??
            context.storeUserAuthToken ??
            context.authToken,
        },
      }
    )
  }
}
```

### 4. Register clients (`node/clients/index.ts`)

```ts
import { IOClients } from '@vtex/api'
import MyClient from './myClient'

export class Clients extends IOClients {
  public get myClient() {
    return this.getOrSet('myClient', MyClient)
  }
}
```

### 5. Create resolvers (`node/resolvers/myFeature.ts`)

Resolver function names **must match** the schema field names exactly.

```ts
export const queries = {
  getMyData: async (
    _: unknown,
    { id }: { id: string },
    ctx: Context
  ) => {
    try {
      const data = await ctx.clients.myClient.getData(id)
      return data
    } catch (error) {
      console.error('Error fetching data:', error)
      return null
    }
  },
}

export const mutations = {
  createMyData: async (
    _: unknown,
    { input }: { input: { name: string; value: number } },
    ctx: Context
  ) => {
    try {
      const result = await ctx.clients.myClient.createData(input)
      return { success: true, message: 'Created', data: result }
    } catch (error) {
      console.error('Error creating data:', error)
      return { success: false, message: 'Failed to create' }
    }
  },
}
```

### 6. Aggregate resolvers (`node/resolvers/index.ts`)

```ts
import { queries as myQueries, mutations as myMutations } from './myFeature'

export const resolvers = {
  Query: {
    ...myQueries,
  },
  Mutation: {
    ...myMutations,
  },
}
```

### 7. Configure service entry-point (`node/index.ts`)

```ts
import type { ClientsConfig, ServiceContext } from '@vtex/api'
import { LRUCache, Service } from '@vtex/api'

import { Clients } from './clients'
import { resolvers } from './resolvers'

const TIMEOUT_MS = 800
const memoryCache = new LRUCache<string, any>({ max: 5000 })
metrics.trackCache('status', memoryCache)

const clients: ClientsConfig<Clients> = {
  implementation: Clients,
  options: {
    default: {
      retries: 2,
      timeout: TIMEOUT_MS,
    },
    status: {
      memoryCache,
    },
  },
}

declare global {
  type Context = ServiceContext<Clients>
}

export default new Service({
  clients,
  graphql: {
    resolvers,
  },
})
```

### 8. Configure service resources (`node/service.json`)

```json
{
  "memory": 256,
  "ttl": 10,
  "timeout": 2,
  "minReplicas": 2,
  "maxReplicas": 4,
  "workers": 1
}
```

### 9. Create `.gql` files in React (`react/components/MyComponent/graphql/`)

Query file:
```graphql
query GetMyData($id: String!) {
  getMyData(id: $id) {
    id
    name
    value
  }
}
```

Mutation file:
```graphql
mutation CreateMyData($input: MyDataInput!) {
  createMyData(input: $input) {
    success
    message
    data {
      id
      name
    }
  }
}
```

### 10. Consume in React component

```js
import React, { useState } from 'react'
import { useLazyQuery, useMutation } from 'react-apollo'

import GET_MY_DATA from './graphql/myQuery.gql'
import CREATE_MY_DATA from './graphql/myMutation.gql'

function MyComponent() {
  const [fetchData, { data, loading, error }] = useLazyQuery(GET_MY_DATA, {
    fetchPolicy: 'network-only',
  })

  const [createData, { loading: creating }] = useMutation(CREATE_MY_DATA)

  const handleFetch = () => {
    fetchData({ variables: { id: '123' } })
  }

  const handleCreate = async () => {
    const result = await createData({
      variables: { input: { name: 'Test', value: 42 } },
    })
    console.log(result.data.createMyData)
  }

  return (...)
}
```

## Using VTEX federated GraphQL (`@context` provider)

To query data from other VTEX apps (catalog, checkout, etc.), use the `@context` directive:

```graphql
query GetProduct($id: ID!) {
  product(identifier: { field: id, value: $id })
    @context(provider: "vtex.search-graphql") {
    productId
    productName
    items {
      itemId
      name
    }
  }
}
```

Common providers: `vtex.search-graphql`, `vtex.store-graphql`, `vtex.checkout-graphql`, `vtex.apps-graphql`.

## GraphQL directives reference

| Directive | Purpose | Example |
|---|---|---|
| `@auth(scope: PUBLIC)` | Public access (no auth required) | Storefront queries |
| `@auth(scope: PRIVATE)` | Requires admin auth token | Admin-only operations |
| `@cacheControl(scope: PRIVATE, maxAge: 0)` | No cache, per-user data | Order data, user info |
| `@cacheControl(scope: PUBLIC, maxAge: 300)` | Shared cache for 5 min | Category lists, settings |

## TypeScript typing for `.gql` imports

Ensure `react/typings/graphql.d.ts` exists:

```ts
declare module '*.graphql' {
  import { DocumentNode } from 'graphql'
  const value: DocumentNode
  export default value
}

declare module '*.gql' {
  import type { DocumentNode } from 'graphql'
  const query: DocumentNode
  export default query
}
```

## react-apollo hooks reference

| Hook | When to use |
|---|---|
| `useQuery(QUERY, { variables })` | Auto-fetch on mount |
| `useLazyQuery(QUERY, { fetchPolicy })` | Fetch on demand (user action) |
| `useMutation(MUTATION)` | Create, update, delete operations |

`fetchPolicy` options: `cache-first` (default), `network-only` (skip cache), `cache-and-network`, `no-cache`.

## REST routes and middlewares

The Node builder supports REST routes via `service.json` routes + middleware handlers. Define route path in `service.json`, create middleware in `node/middlewares/`, and register with `method()` in `node/index.ts`. See [reference.md](reference.md) for path patterns, middleware examples, and event handling.

### Quick example

```ts
// service.json → "routes": { "myRoute": { "path": "/_v/my-app/data/:id", "public": true } }
// node/middlewares/myHandler.ts
export async function myHandler(ctx: Context, next: () => Promise<void>) {
  const { id } = ctx.vtex.route.params
  ctx.body = await ctx.clients.myClient.getData(id)
  ctx.status = 200
  await next()
}
// node/index.ts → routes: { myRoute: method({ GET: [myHandler] }) }
```

## Event handling

Listen to events from other apps via `service.json` events + handler functions. See [reference.md](reference.md) for full event setup.

## Checklist

- [ ] `graphql/schema.graphql` with `@auth` on every field
- [ ] Types in `graphql/types/` matching resolver return shapes
- [ ] Client in `node/clients/` registered in `Clients` class
- [ ] Resolver function names match schema field names exactly
- [ ] Resolvers aggregated in `node/resolvers/index.ts`
- [ ] Service exported in `node/index.ts` with `graphql: { resolvers }`
- [ ] `service.json` with appropriate memory/timeout
- [ ] `.gql` files in React matching the schema
- [ ] `graphql.d.ts` typing in `react/typings/`
- [ ] Outbound access policies in `manifest.json` for external APIs
- [ ] REST routes declared in `service.json` with correct path pattern
- [ ] Event handlers registered for async workflows

## Additional resources

- [reference.md](reference.md) — Client types, HttpClient methods, REST routes, path patterns, event handling, authentication, service.json reference
- [examples.md](examples.md) — Real project examples (OMS, Newsletter, federated GraphQL)
