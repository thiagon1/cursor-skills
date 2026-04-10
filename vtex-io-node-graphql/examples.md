# Examples — Node.js + GraphQL from this project

## 1. Full flow: OMS Order (Query)

End-to-end flow from GraphQL schema to React component.

### GraphQL schema (`graphql/schema.graphql`)

```graphql
type Query {
  getOrder(orderId: String): GetOrderResponse
    @auth(scope: PUBLIC)
    @cacheControl(scope: PRIVATE, maxAge: 0)
}
```

### Types (`graphql/types/getOrder.graphql`)

```graphql
type OrderItems {
  id: String
  productId: String
  quantity: Int
  name: String
  price: Int
}

type DataGetOrderResponse {
  items: [OrderItems]
  value: Int
  orderFormId: String
}

type GetOrderResponse {
  status: Int
  data: DataGetOrderResponse
}
```

### Client (`node/clients/omsClient.ts`)

```ts
import type { InstanceOptions, IOContext } from '@vtex/api'
import { ExternalClient } from '@vtex/api'

export default class OMS extends ExternalClient {
  constructor(context: IOContext, options?: InstanceOptions) {
    super(
      `http://${context.account}.vtexcommercestable.com.br/api/oms/pvt/orders`,
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

  public async getOrder(orderId: string) {
    return this.http.getRaw(`/${orderId}`)
  }
}
```

### Resolver (`node/resolvers/oms/index.ts`)

```ts
export const queries = {
  getOrder: async (
    _: unknown,
    { orderId }: any,
    ctx: Context
  ): Promise<any> => {
    try {
      const data = await ctx.clients.omsClient.getOrder(orderId)
      return data
    } catch (error) {
      return null
    }
  },
}
```

### React `.gql` file (`react/components/.../getOrder.gql`)

```graphql
query GetOrder($orderId: String) {
  getOrder(orderId: $orderId) {
    status
    data {
      items { id productId quantity name price }
      value
      orderFormId
    }
  }
}
```

### React consumption with `useLazyQuery`

```js
import { useLazyQuery } from 'react-apollo'
import GET_ORDER from './graphql/getOrder.gql'

const [fetchOrder, { data, loading }] = useLazyQuery(GET_ORDER, {
  fetchPolicy: 'network-only',
})

// Trigger on user action:
fetchOrder({ variables: { orderId: '1234567890-01' } })
```

---

## 2. Full flow: Newsletter (Query + Mutation)

### Schema (`graphql/schema.graphql`)

```graphql
type Query {
  checkBlackFridayNewsletterEmail(email: String!): EmailCheckResponse
    @auth(scope: PUBLIC)
    @cacheControl(scope: PUBLIC, maxAge: 300)
}

type Mutation {
  subscribeBlackFridayNewsletter(input: BlackFridayNewsletterInput!): NewsletterResponse
    @auth(scope: PUBLIC)
    @cacheControl(scope: PUBLIC, maxAge: 0)
}
```

### Types (`graphql/types/blackFridayNewsletter.graphql`)

```graphql
type BlackFridaySubscription {
  name: String
  email: String
}

type NewsletterResponse {
  success: Boolean!
  message: String!
  data: BlackFridaySubscription
}

type EmailCheckResponse {
  success: Boolean!
  emailExists: Boolean!
}

input BlackFridayNewsletterInput {
  name: String!
  email: String!
}
```

### MasterData client (`node/clients/md.ts`)

```ts
import type { IOContext, InstanceOptions } from '@vtex/api'
import { MasterData } from '@vtex/api'

export interface BlackFridaySubscription {
  name?: string
  email?: string
}

export default class MD extends MasterData {
  constructor(ctx: IOContext, options?: InstanceOptions) {
    super(ctx, { ...options })
  }

  public async checkBlackFridayEmail(email: string) {
    const result = await this.searchDocuments<BlackFridaySubscription>({
      dataEntity: 'BF',
      fields: ['name', 'email'],
      where: `email='${email}'`,
      pagination: { page: 1, pageSize: 1 },
    })
    return result.length > 0 ? result[0] : null
  }

  public async createBlackFridaySubscription(email: string, data: Record<string, unknown>) {
    await this.createDocument({
      dataEntity: 'BF',
      fields: { email, ...data },
    })
    return { email, ...data }
  }
}
```

### Clients registry (`node/clients/index.ts`)

```ts
import { IOClients } from '@vtex/api'
import OMS from './omsClient'
import MD from './md'

export class Clients extends IOClients {
  public get omsClient() {
    return this.getOrSet('omsClient', OMS)
  }
  public get md() {
    return this.getOrSet('md', MD)
  }
}
```

### Resolver (`node/resolvers/blackFridayNewsletter.ts`)

```ts
export const queries = {
  checkBlackFridayNewsletterEmail: async (
    _: any,
    { email }: { email: string },
    ctx: Context
  ) => {
    try {
      const existing = await ctx.clients.md.checkBlackFridayEmail(email)
      return { success: true, emailExists: !!existing }
    } catch (error) {
      return { success: false, emailExists: false }
    }
  },
}

export const mutations = {
  subscribeBlackFridayNewsletter: async (
    _: any,
    { input }: { input: { name: string; email: string } },
    ctx: Context
  ) => {
    try {
      const existing = await ctx.clients.md.checkBlackFridayEmail(input.email)
      if (existing) {
        return { success: false, message: 'Email already registered', data: existing }
      }
      const newSub = await ctx.clients.md.createBlackFridaySubscription(
        input.email,
        { name: input.name }
      )
      return { success: true, message: 'Subscribed successfully', data: newSub }
    } catch (error) {
      return { success: false, message: 'Error creating subscription' }
    }
  },
}
```

### Resolvers aggregation (`node/resolvers/index.ts`)

```ts
import { queries as omsQueries } from './oms'
import { queries as bfQueries, mutations as bfMutations } from './blackFridayNewsletter'

export const resolvers = {
  Query: {
    ...omsQueries,
    ...bfQueries,
  },
  Mutation: {
    ...bfMutations,
  },
}
```

### React `.gql` files

```graphql
# react/components/BlackFridayNewsletter/graphql/checkEmail.gql
query CheckBlackFridayNewsletterEmail($email: String!) {
  checkBlackFridayNewsletterEmail(email: $email) {
    success
    emailExists
  }
}
```

```graphql
# react/components/BlackFridayNewsletter/graphql/subscribeNewsletter.gql
mutation SubscribeBlackFridayNewsletter($input: BlackFridayNewsletterInput!) {
  subscribeBlackFridayNewsletter(input: $input) {
    success
    message
    data { name email }
  }
}
```

### React component consuming both

```js
import { useLazyQuery, useMutation } from 'react-apollo'
import CHECK_EMAIL from './graphql/checkEmail.gql'
import SUBSCRIBE_NEWSLETTER from './graphql/subscribeNewsletter.gql'

const [checkEmail, { data: emailCheckData }] = useLazyQuery(CHECK_EMAIL, {
  fetchPolicy: 'network-only',
})

const [subscribeNewsletter, { loading: subscribing }] = useMutation(SUBSCRIBE_NEWSLETTER)

// Check email:
checkEmail({ variables: { email: 'user@example.com' } })

// Subscribe:
const result = await subscribeNewsletter({
  variables: { input: { name: 'John', email: 'john@example.com' } },
})
```

---

## 3. Federated GraphQL (using VTEX providers)

### Product query with `@context` provider

```graphql
# react/components/ProductModuleShelf/graphql/get_product.gql
query GET_PRODUCT_MODULE($id: ID!) {
  product(identifier: { field: id, value: $id })
    @context(provider: "vtex.search-graphql") {
    productId
    productName
    items {
      itemId
      name
      images { imageUrl }
    }
  }
}
```

### App settings query

```graphql
# react/graphql/queries/appSettings.gql
query AppSettings($version: String) {
  publicSettingsForApp(app: "lojamm.store-theme", version: $version)
    @context(provider: "vtex.apps-graphql") {
    message
  }
}
```

These queries do **not** require a Node.js resolver — they use the VTEX federated GraphQL layer directly from the React component.

---

## 4. Node.js project configuration

### `node/package.json`

```json
{
  "dependencies": {
    "co-body": "^6.0.0",
    "ramda": "^0.25.0"
  },
  "devDependencies": {
    "@vtex/api": "^7.0.0",
    "@vtex/tsconfig": "^0.5.6",
    "typescript": "5.5.3"
  },
  "scripts": {
    "lint": "tsc --noEmit --pretty"
  }
}
```

### `node/tsconfig.json`

```json
{
  "extends": "@vtex/tsconfig",
  "compilerOptions": {
    "noEmitOnError": false,
    "lib": ["dom"],
    "module": "esnext",
    "moduleResolution": "node",
    "target": "es2019"
  },
  "include": ["./typings/*.d.ts", "./**/*.tsx", "./**/*.ts"]
}
```

### `node/service.json`

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
