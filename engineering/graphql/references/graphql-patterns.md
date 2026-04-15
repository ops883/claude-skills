# GraphQL Patterns Reference

Concrete, production-tested patterns. Copy and adapt — do not start from scratch.

---

## DataLoader — Solving N+1

Without DataLoader, loading `posts` for 100 users fires 100 SQL queries. With DataLoader, it fires 1.

### Installation
```bash
npm install dataloader
```

### Pattern: Batch loader by foreign key

```javascript
// src/loaders/index.js
import DataLoader from 'dataloader';
import { db } from '../db';

// Batch function receives an array of keys, returns array of values IN SAME ORDER
async function batchPostsByUserId(userIds) {
  const posts = await db('posts')
    .whereIn('user_id', userIds)
    .select('*');

  // Group by user_id
  const byUserId = {};
  for (const post of posts) {
    if (!byUserId[post.user_id]) byUserId[post.user_id] = [];
    byUserId[post.user_id].push(post);
  }

  // Return in same order as input keys (DataLoader requirement)
  return userIds.map(id => byUserId[id] || []);
}

export function createLoaders() {
  return {
    postsByUserId: new DataLoader(batchPostsByUserId),
    // Add one DataLoader per relationship
    commentsByPostId: new DataLoader(batchCommentsByPostId),
    userById: new DataLoader(batchUsersById),
  };
}
```

### Pattern: Batch loader for single entities (by ID)

```javascript
async function batchUsersById(ids) {
  const users = await db('users').whereIn('id', ids).select('*');
  const byId = Object.fromEntries(users.map(u => [u.id, u]));
  // Return null for missing IDs (not undefined — DataLoader distinction)
  return ids.map(id => byId[id] ?? null);
}
```

### Wire into context (created fresh per request)

```javascript
// New DataLoader per request — never share across requests
const context = ({ req }) => ({
  user: req.user,
  loaders: createLoaders(),  // fresh per request
  dataSources: { ... },
});
```

---

## Apollo Server Setup with Context Injection

### Full production setup (Express + JWT auth)

```javascript
// src/server.js
import { ApolloServer } from '@apollo/server';
import { expressMiddleware } from '@apollo/server/express4';
import { ApolloServerPluginDrainHttpServer } from '@apollo/server/plugin/drainHttpServer';
import express from 'express';
import http from 'http';
import jwt from 'jsonwebtoken';
import { typeDefs } from './schema';
import { resolvers } from './resolvers';
import { createLoaders } from './loaders';
import { db } from './db';

const app = express();
const httpServer = http.createServer(app);

const server = new ApolloServer({
  typeDefs,
  resolvers,
  plugins: [ApolloServerPluginDrainHttpServer({ httpServer })],
  // Limit query depth and complexity to prevent abuse
  // Add graphql-depth-limit and graphql-validation-complexity for production
});

await server.start();

app.use(
  '/graphql',
  express.json(),
  expressMiddleware(server, {
    context: async ({ req }) => {
      // Decode JWT — do NOT throw here, let resolvers enforce auth
      let user = null;
      const authHeader = req.headers.authorization || '';
      const token = authHeader.replace(/^Bearer\s+/i, '');
      if (token) {
        try {
          user = jwt.verify(token, process.env.JWT_SECRET);
        } catch {
          // Invalid token — treat as unauthenticated
        }
      }

      return {
        user,                    // null if unauthenticated
        loaders: createLoaders(), // fresh DataLoaders per request
        db,                      // query builder
      };
    },
  })
);

await new Promise(resolve => httpServer.listen({ port: 4000 }, resolve));
console.log('GraphQL server running at http://localhost:4000/graphql');
```

### Auth enforcement pattern in resolvers

```javascript
import { AuthenticationError, ForbiddenError } from 'apollo-server-errors';

// Helper — call at top of any protected resolver
function requireAuth(ctx) {
  if (!ctx.user) throw new AuthenticationError('You must be logged in.');
  return ctx.user;
}

function requireRole(ctx, role) {
  const user = requireAuth(ctx);
  if (user.role !== role) throw new ForbiddenError(`Requires role: ${role}`);
  return user;
}

// Usage
const resolvers = {
  Query: {
    me: (_, __, ctx) => {
      const user = requireAuth(ctx);
      return ctx.loaders.userById.load(user.id);
    },
    adminStats: (_, __, ctx) => {
      requireRole(ctx, 'ADMIN');
      return ctx.db('stats').select('*');
    },
  },
};
```

---

## Cursor Pagination

Offset pagination breaks when items are inserted/deleted during browsing. Cursor-based pagination is stable and scales.

### Schema

```graphql
type UserConnection {
  edges: [UserEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type UserEdge {
  node: User!
  cursor: String!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}

type Query {
  """Paginated list of users."""
  users(first: Int, after: String, last: Int, before: String): UserConnection!
}
```

### Implementation

```javascript
// Encode/decode cursor (base64 of "typename:id" or "typename:createdAt:id")
const encodeCursor = (id) => Buffer.from(`user:${id}`).toString('base64');
const decodeCursor = (cursor) => {
  const decoded = Buffer.from(cursor, 'base64').toString('utf8');
  return decoded.split(':')[1]; // returns id
};

async function getUsers({ first = 10, after, last, before }, { db }) {
  let query = db('users').orderBy('created_at', 'asc').orderBy('id', 'asc');

  if (after) {
    const afterId = decodeCursor(after);
    query = query.where('id', '>', afterId);
  }
  if (before) {
    const beforeId = decodeCursor(before);
    query = query.where('id', '<', beforeId);
  }

  const limit = first ?? last ?? 10;
  const rows = await query.limit(limit + 1).select('*'); // fetch +1 to detect hasNextPage

  const hasNextPage = rows.length > limit;
  const hasPreviousPage = Boolean(after || before);
  const items = hasNextPage ? rows.slice(0, limit) : rows;

  const totalCount = await db('users').count('* as count').first();

  return {
    edges: items.map(row => ({
      node: row,
      cursor: encodeCursor(row.id),
    })),
    pageInfo: {
      hasNextPage,
      hasPreviousPage,
      startCursor: items.length ? encodeCursor(items[0].id) : null,
      endCursor: items.length ? encodeCursor(items[items.length - 1].id) : null,
    },
    totalCount: Number(totalCount.count),
  };
}
```

---

## Subscriptions with WebSocket

### Server setup (Apollo Server + graphql-ws)

```javascript
import { createServer } from 'http';
import { WebSocketServer } from 'ws';
import { useServer } from 'graphql-ws/lib/use/ws';
import { makeExecutableSchema } from '@graphql-tools/schema';
import { PubSub } from 'graphql-subscriptions';

export const pubsub = new PubSub();

const schema = makeExecutableSchema({ typeDefs, resolvers });
const httpServer = createServer(app);

// WebSocket server alongside HTTP
const wsServer = new WebSocketServer({ server: httpServer, path: '/graphql' });
const serverCleanup = useServer(
  {
    schema,
    context: async (ctx) => {
      // ctx.connectionParams contains auth token from client
      const token = ctx.connectionParams?.authToken;
      let user = null;
      if (token) {
        try { user = jwt.verify(token, process.env.JWT_SECRET); } catch {}
      }
      return { user, loaders: createLoaders() };
    },
  },
  wsServer
);
```

### Schema

```graphql
type Subscription {
  """Fires when a post is created by the specified author."""
  postCreated(authorId: ID!): Post!

  """Fires when a comment is added to the specified post."""
  commentAdded(postId: ID!): Comment!
}
```

### Resolvers with withFilter

```javascript
import { withFilter } from 'graphql-subscriptions';
import { pubsub } from '../server';

const resolvers = {
  Mutation: {
    createPost: async (_, { input }, { user, db }) => {
      requireAuth(ctx); // reuse auth helper
      const post = await db('posts').insert(input).returning('*');
      // Publish event — subscribers with matching authorId receive it
      await pubsub.publish('POST_CREATED', { postCreated: post[0] });
      return post[0];
    },
  },

  Subscription: {
    postCreated: {
      subscribe: withFilter(
        () => pubsub.asyncIterator('POST_CREATED'),
        // Filter function: return true to forward to this subscriber
        (payload, variables) => payload.postCreated.author_id === variables.authorId
      ),
    },
  },
};
```

### Client (Apollo Client)

```javascript
import { split, HttpLink } from '@apollo/client';
import { GraphQLWsLink } from '@apollo/client/link/subscriptions';
import { createClient } from 'graphql-ws';
import { getMainDefinition } from '@apollo/client/utilities';

const wsLink = new GraphQLWsLink(
  createClient({
    url: 'ws://localhost:4000/graphql',
    connectionParams: { authToken: getAuthToken() },
  })
);

const httpLink = new HttpLink({ uri: 'http://localhost:4000/graphql' });

// Route subscriptions to WS, everything else to HTTP
const splitLink = split(
  ({ query }) => {
    const def = getMainDefinition(query);
    return def.kind === 'OperationDefinition' && def.operation === 'subscription';
  },
  wsLink,
  httpLink
);
```

---

## Persisted Queries

Persisted queries reduce request size and prevent arbitrary query execution in production.

### Apollo Server — automatic persisted queries (APQ)

```javascript
import { ApolloServer } from '@apollo/server';
import { ApolloServerPluginCacheControl } from '@apollo/server/plugin/cacheControl';
import responseCachePlugin from '@apollo/server-plugin-response-cache';
import { InMemoryLRUCache } from '@apollo/utils.keyvaluecache';

const server = new ApolloServer({
  typeDefs,
  resolvers,
  cache: new InMemoryLRUCache({ maxSize: 30_000_000 }), // 30MB
  plugins: [
    ApolloServerPluginCacheControl({ defaultMaxAge: 0 }),
    responseCachePlugin(),
  ],
});
```

### Client — send hash first, full query on cache miss

```javascript
import { ApolloClient, InMemoryCache } from '@apollo/client';
import { createPersistedQueryLink } from '@apollo/client/link/persisted-queries';
import { sha256 } from 'crypto-hash';

const persistedQueriesLink = createPersistedQueryLink({ sha256 });

const client = new ApolloClient({
  link: persistedQueriesLink.concat(httpLink),
  cache: new InMemoryCache(),
});
```

### Locked persisted queries (production hardening)

Register a fixed query manifest at deploy time. Reject all unregistered queries.

```javascript
// Build step: extract queries from client code into a manifest
// npx apollo client:extract --output=./operations.json

// Server: load manifest and reject unknown queries
import manifest from './operations.json';
const allowedQueries = new Set(Object.keys(manifest));

const server = new ApolloServer({
  typeDefs,
  resolvers,
  plugins: [{
    requestDidStart() {
      return {
        didResolveOperation({ request }) {
          const hash = request.extensions?.persistedQuery?.sha256Hash;
          if (hash && !allowedQueries.has(hash)) {
            throw new ForbiddenError('Unknown operation');
          }
        },
      };
    },
  }],
});
```

---

## Hasura Permission Rules

Hasura uses row-level and column-level permissions per role.

### Pattern: users can only read their own data

```json
{
  "role": "user",
  "permission": {
    "columns": ["id", "name", "email", "created_at"],
    "filter": {
      "id": { "_eq": "X-Hasura-User-Id" }
    }
  }
}
```

### Pattern: admins can read all, users read own

```json
{
  "role": "admin",
  "permission": {
    "columns": "*",
    "filter": {}
  }
}
```

```json
{
  "role": "user",
  "permission": {
    "columns": ["id", "title", "body", "created_at"],
    "filter": {
      "author_id": { "_eq": "X-Hasura-User-Id" }
    }
  }
}
```

### Pattern: insert with preset (inject user ID from JWT)

```json
{
  "role": "user",
  "permission": {
    "columns": ["title", "body"],
    "set": {
      "author_id": "X-Hasura-User-Id"
    },
    "check": {}
  }
}
```

### JWT config for Hasura

```json
{
  "type": "HS256",
  "key": "your-secret-key",
  "claims_namespace": "https://hasura.io/jwt/claims",
  "claims_format": "json"
}
```

JWT payload must include:

```json
{
  "https://hasura.io/jwt/claims": {
    "x-hasura-allowed-roles": ["user", "admin"],
    "x-hasura-default-role": "user",
    "x-hasura-user-id": "123"
  }
}
```

---

## Error Handling Conventions

### Union return types (preferred for mutations)

```graphql
type CreateUserSuccess {
  user: User!
}

type ValidationError {
  field: String!
  message: String!
}

type AuthError {
  message: String!
}

union CreateUserResult = CreateUserSuccess | ValidationError | AuthError

type Mutation {
  createUser(input: CreateUserInput!): CreateUserResult!
}
```

```javascript
// Resolver returns the correct union member
createUser: async (_, { input }, ctx) => {
  if (!ctx.user) return { __typename: 'AuthError', message: 'Not authenticated' };
  if (!input.email.includes('@')) {
    return { __typename: 'ValidationError', field: 'email', message: 'Invalid email' };
  }
  const user = await ctx.db('users').insert(input).returning('*');
  return { __typename: 'CreateUserSuccess', user: user[0] };
},
```

### Client query

```graphql
mutation CreateUser($input: CreateUserInput!) {
  createUser(input: $input) {
    ... on CreateUserSuccess { user { id name } }
    ... on ValidationError { field message }
    ... on AuthError { message }
  }
}
```

---

## Schema Stitching vs Federation

| | Stitching | Federation |
|---|---|---|
| **Use when** | Small team, 2-3 services, full control | Multiple teams, independent deploy cadences |
| **Complexity** | Low | High (router, subgraph protocol) |
| **Runtime** | Gateway merges at query time | Router distributes queries |
| **Tooling** | `@graphql-tools/stitch` | Apollo Federation, Cosmo, Hive |
| **Type ownership** | Gateway defines all types | Each subgraph owns its types |

### Minimal federation setup

```javascript
// Subgraph (user service)
import { buildSubgraphSchema } from '@apollo/subgraph';
import gql from 'graphql-tag';

const typeDefs = gql`
  extend schema @link(url: "https://specs.apollo.dev/federation/v2.0", import: ["@key"])

  type User @key(fields: "id") {
    id: ID!
    name: String!
    email: String!
  }

  type Query {
    user(id: ID!): User
  }
`;

const resolvers = {
  User: {
    // Reference resolver — called by router when another subgraph references User
    __resolveReference: ({ id }, { loaders }) => loaders.userById.load(id),
  },
};

export const schema = buildSubgraphSchema({ typeDefs, resolvers });
```

---

## Rate Limiting Resolvers

Use field-level complexity scoring to prevent expensive queries.

```javascript
import { createComplexityLimitRule } from 'graphql-validation-complexity';

const complexityLimitRule = createComplexityLimitRule(1000, {
  // Override complexity for specific fields
  scalarCost: 1,
  objectCost: 2,
  listFactor: 10,
  introspectionListFactor: 2,
  onCost: (cost) => {
    if (cost > 500) {
      console.warn(`High-complexity query: ${cost}`);
    }
  },
});

const server = new ApolloServer({
  typeDefs,
  resolvers,
  validationRules: [complexityLimitRule],
});
```

### Depth limiting

```javascript
import depthLimit from 'graphql-depth-limit';

const server = new ApolloServer({
  typeDefs,
  resolvers,
  validationRules: [depthLimit(7)], // reject queries deeper than 7 levels
});
```

### Per-resolver rate limiting (Redis-backed)

```javascript
import { RateLimiterRedis } from 'rate-limiter-flexible';

const rateLimiter = new RateLimiterRedis({
  storeClient: redisClient,
  points: 100,     // requests
  duration: 60,    // per 60 seconds
});

// In context or as a directive
async function checkRateLimit(userId) {
  try {
    await rateLimiter.consume(userId);
  } catch {
    throw new ApolloError('Too many requests', 'RATE_LIMITED');
  }
}
```
