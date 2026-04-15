---
name: "graphql"
description: "GraphQL API design and implementation skill for schema-first development, SDL patterns, resolver chaining, DataLoader N+1 prevention, Apollo Server/Client setup, Hasura permissions, WebSocket subscriptions, persisted queries, cursor pagination, and authentication via context injection. Use when: user wants to design or audit a GraphQL schema, fix N+1 query problems, set up Apollo Server or Hasura, implement subscriptions, add pagination, or follow GraphQL production best practices."
license: MIT
metadata:
  version: 1.0.0
  author: ops883
  category: engineering
  updated: 2026-04-14
---

# GraphQL

> Schema-first. No N+1. No resolver spaghetti.

Opinionated GraphQL workflow covering everything from SDL design to production query optimization. Built around concrete patterns that work — DataLoader, cursor pagination, context injection, persisted queries.

Not a GraphQL tutorial. A set of decisions about how to build APIs that don't melt under load.

---

## Slash Commands

| Command | What it does |
|---------|-------------|
| `/graphql:schema` | Design or review a GraphQL schema using SDL best practices |
| `/graphql:resolvers` | Build resolver chains with DataLoader and proper context injection |
| `/graphql:audit` | Audit a schema for N+1 risks, missing pagination, and type design issues |

---

## When This Skill Activates

Recognize these patterns from the user:

- "Design a GraphQL schema for..."
- "Fix my N+1 queries"
- "Set up Apollo Server"
- "Add subscriptions to my GraphQL API"
- "Implement cursor pagination"
- "Hasura permissions for..."
- "GraphQL authentication / context"
- "Persisted queries"
- Any request involving: SDL, resolvers, DataLoader, Apollo, Hasura, GraphQL schema, query performance

---

## Workflow

### `/graphql:schema` — Schema-First Design

1. **Define types in SDL before writing any resolver**

   ```graphql
   """A platform user account."""
   type User {
     id: ID!
     email: String!
     name: String!
     role: UserRole!
     posts(first: Int, after: String): PostConnection!
     createdAt: DateTime!
   }

   enum UserRole { ADMIN MEMBER VIEWER }

   type PostConnection {
     edges: [PostEdge!]!
     pageInfo: PageInfo!
     totalCount: Int!
   }

   type PostEdge {
     node: Post!
     cursor: String!
   }

   type PageInfo {
     hasNextPage: Boolean!
     hasPreviousPage: Boolean!
     startCursor: String
     endCursor: String
   }
   ```

2. **SDL checklist**

   ```
   TYPES
   ├── Every type has id: ID! (except connection/edge/pageInfo types)
   ├── Non-null by default — nullable only when null is meaningful
   ├── Lists return connections, not bare arrays (for anything paginated)
   ├── Enums for finite value sets — never raw strings
   └── Add description strings on all types, fields, queries, mutations

   QUERIES
   ├── List queries always have pagination args (first/after or last/before)
   ├── Single-item queries return nullable (user returns User, not User!)
   ├── Filter args typed as input types, not flat scalars
   └── No overfetching — don't return related data unless user asks

   MUTATIONS
   ├── Input types for all mutations: createUser(input: CreateUserInput!)
   ├── Return the mutated object plus a clientMutationId if needed
   ├── Use verb-noun naming: createPost, updateUser, deleteComment
   └── Error handling via union types or errors field on payload

   SUBSCRIPTIONS
   ├── Add filter args (userId, topicId) — never broadcast everything
   ├── Return same type as the underlying query
   └── Document event triggers in description
   ```

3. **Run schema analyzer**
   ```bash
   python3 scripts/graphql_schema_analyzer.py schema.graphql
   ```

4. **Iterate on warnings before writing resolvers**

---

### `/graphql:resolvers` — Resolver Implementation

1. **Context setup (do once, use everywhere)**

   See `references/graphql-patterns.md` → Apollo Server Context section.

2. **Resolver chain pattern**

   ```javascript
   // Resolvers are just functions — keep them thin
   const resolvers = {
     Query: {
       user: (_, { id }, { dataSources }) =>
         dataSources.userService.getById(id),

       users: (_, { first = 10, after }, { dataSources }) =>
         dataSources.userService.getPaginated({ first, after }),
     },

     User: {
       // DataLoader prevents N+1 — one SQL per batch, not per user
       posts: ({ id }, { first, after }, { loaders }) =>
         loaders.postsByUserId.load({ userId: id, first, after }),
     },

     Mutation: {
       createUser: async (_, { input }, { dataSources, user }) => {
         if (!user) throw new AuthenticationError('Not authenticated');
         return dataSources.userService.create(input);
       },
     },

     Subscription: {
       postCreated: {
         subscribe: withFilter(
           (_, __, { pubsub }) => pubsub.asyncIterator('POST_CREATED'),
           (payload, { userId }) => payload.postCreated.authorId === userId
         ),
       },
     },
   };
   ```

3. **DataLoader pattern (mandatory for any list resolver)**

   Every field that loads a related entity must use DataLoader. No exceptions.
   See `references/graphql-patterns.md` → DataLoader section.

4. **Error handling**

   ```javascript
   // Use typed errors, not raw Error
   import { ApolloError, AuthenticationError, ForbiddenError, UserInputError } from 'apollo-server-express';

   // In resolvers:
   if (!ctx.user) throw new AuthenticationError('Login required');
   if (!canAccess(ctx.user, resource)) throw new ForbiddenError('Access denied');
   if (!isValid(input)) throw new UserInputError('Invalid input', { field: 'email' });
   ```

---

### `/graphql:audit` — Schema Audit

1. **Run the analyzer**
   ```bash
   python3 scripts/graphql_schema_analyzer.py schema.graphql
   python3 scripts/graphql_schema_analyzer.py schema.graphql --output json
   ```

2. **Interpret findings**

   | Severity | Meaning | Action |
   |----------|---------|--------|
   | CRITICAL | Breaking design flaw | Fix before shipping |
   | WARNING | Performance or correctness risk | Fix before production |
   | NOTE | Best practice deviation | Fix when possible |

3. **Common issues to look for manually**

   | Pattern | Risk | Fix |
   |---------|------|-----|
   | `friends: [User]` | N+1 on every query | Add DataLoader for friends |
   | `users: [User!]!` with no pagination args | Full table scan | Add cursor pagination |
   | Resolver calls DB directly | No batching | Move to DataLoader/DataSource |
   | Token checked in each resolver | Auth scattered | Centralize in context |
   | Mutations accept flat args | Hard to extend | Wrap in input types |
   | Subscription without filter | Broadcasts everything | Add withFilter() |

---

## Python Tools

### `scripts/graphql_schema_analyzer.py`

Static analysis of `.graphql` SDL files.

**Checks:**
- Missing `id: ID!` on object types (WARNING)
- Nullable list items `[Type]` vs `[Type!]!` (NOTE)
- Types with >15 fields — consider splitting (NOTE)
- Fields named `*old*`, `*legacy*`, `*deprecated*` without `@deprecated` (WARNING)
- Queries returning lists without pagination args (WARNING)
- Mutations without input types (WARNING)
- Missing description strings on types/queries (NOTE)
- Subscriptions without filter args (NOTE)
- N+1 risk: list field nested in list-returning context (WARNING)

**Usage:**
```bash
# Text report (exit code 1 if WARNING/CRITICAL)
python3 scripts/graphql_schema_analyzer.py schema.graphql

# JSON output (for CI)
python3 scripts/graphql_schema_analyzer.py schema.graphql --output json

# Show suggested fixes as inline comments
python3 scripts/graphql_schema_analyzer.py schema.graphql --fix
```

---

## Proactive Triggers

Flag these without being asked:

- **Resolver fetches related data in a loop** → DataLoader required. Explain the N+1 problem and provide the DataLoader implementation.
- **List query with no `first`/`after` args** → Will full-scan the table. Add cursor pagination.
- **Auth logic in each resolver** → Centralize in context. Show Apollo Server context pattern.
- **Mutation takes flat args** → Wrap in input type for forward compatibility.
- **Subscription with no filter** → Every client receives every event. Add `withFilter()`.
- **No `@deprecated` on legacy fields** → Clients can't introspect deprecation. Add it.
- **Schema uses offset pagination** → Doesn't scale past ~10k rows. Switch to cursor-based.

---

## Cross-References

- **api-design-reviewer** — REST and GraphQL API review. Complementary — graphql covers implementation, api-design-reviewer covers design decisions and API contracts.
- **database-designer** — Schema design. Complementary — GraphQL types often mirror DB schema; use both for data-layer/API-layer consistency.
- **ci-cd-pipeline-builder** — Pipeline construction. Use persisted queries and schema validation as a CI gate.
- **senior-security** — Application security. GraphQL has specific attack vectors (introspection abuse, query depth/complexity attacks); use senior-security for threat modeling.
