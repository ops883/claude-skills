---
name: "message-queue"
description: "Expert guidance on message queue design patterns covering Redis pub/sub vs streams, BullMQ job queues with worker concurrency and cron jobs, RabbitMQ exchange routing (direct/fanout/topic/headers), Kafka topics and partition key strategies with consumer group management, dead letter queues with exponential backoff and poison message detection, idempotent consumer patterns with deduplication keys, backpressure mechanisms, and retry strategies for building resilient at-least-once delivery pipelines."
license: MIT
metadata:
  version: 1.0.0
  author: ops883
  category: engineering
  updated: 2026-04-14
---

# Message Queue Design

> At-least-once delivery. Idempotent consumers. No lost jobs.

Design, configure, and operate message queues across Redis Streams, BullMQ, RabbitMQ, and Kafka — with dead letter queues, backpressure, and retry strategies baked in.

## Slash Commands

| Command | Description |
|---------|-------------|
| `/queue:design` | Choose the right queue technology, design message schemas, and configure delivery semantics |
| `/queue:dlq` | Configure dead letter queues, exponential backoff, poison message handling, and replay |
| `/queue:monitor` | Set up queue depth alerts, consumer lag tracking, stall detection, and throughput metrics |

---

## When This Skill Activates

- Designing a new job queue, event pipeline, or notification system
- Choosing between Redis, BullMQ, RabbitMQ, or Kafka
- Debugging silent job failures, duplicate processing, or consumer lag
- Configuring dead letter queues and retry policies
- Setting up Kafka consumer groups or RabbitMQ exchanges
- Dealing with backpressure, rate limiting, or message ordering requirements

---

## `/queue:design` — Choosing the Right Queue

### Technology Decision Matrix

| Requirement | Redis Streams | BullMQ | RabbitMQ | Kafka |
|-------------|--------------|--------|----------|-------|
| Simple pub/sub fanout | ✓ | — | ✓ (fanout exchange) | ✓ |
| Job queue with retries | partial | **best fit** | ✓ | overkill |
| Complex routing rules | — | — | **best fit** | — |
| High-throughput event log | ✓ | — | — | **best fit** |
| Replay/rewind messages | ✓ (consumer groups) | — | — | **best fit** |
| Scheduled/cron jobs | — | **best fit** | — | — |
| Multi-tenant job isolation | — | ✓ (named queues) | ✓ (vhosts) | ✓ (topics) |
| Ordering guarantees | per-stream | per-queue | per-queue | per-partition |
| Horizontal scale | moderate | moderate | moderate | **best fit** |

**Decision rules:**
- Web app background jobs (email, resize, export) → **BullMQ**
- Service-to-service events, routing by type → **RabbitMQ**
- High-volume event streaming, analytics, audit logs → **Kafka**
- Lightweight pub/sub in an existing Redis stack → **Redis Streams**

### Message Schema Design

Every message needs three envelope fields regardless of broker:

```typescript
interface Message<T> {
  id: string;           // idempotency key — UUID v4 or deterministic hash
  type: string;         // e.g. "email.welcome", "image.resize"
  timestamp: string;    // ISO 8601
  payload: T;
  metadata?: {
    correlationId?: string;   // trace across services
    causationId?: string;     // id of the message that caused this one
    retryCount?: number;
    source?: string;
  };
}
```

### Idempotency Keys

Consumers **must** handle duplicate delivery. Use the message `id` as a deduplication key:

```typescript
async function processMessage(msg: Message<EmailPayload>) {
  // Check dedup store first (Redis SET NX with TTL, or DB unique constraint)
  const alreadyProcessed = await redis.set(
    `processed:${msg.id}`,
    '1',
    'NX',
    'EX',
    86400  // 24h TTL
  );
  if (!alreadyProcessed) {
    logger.info({ msgId: msg.id }, 'Duplicate message — skipping');
    return;
  }
  await doActualWork(msg.payload);
}
```

### At-Least-Once vs Exactly-Once

| Semantic | How to achieve | Trade-off |
|----------|---------------|-----------|
| At-least-once | Ack after processing | Duplicates possible — requires idempotent consumers |
| Exactly-once | Transactional outbox pattern | Higher complexity, slower writes |
| At-most-once | Ack before processing | Risk of lost messages on crash |

**Default recommendation:** at-least-once + idempotent consumers. Exactly-once is rarely worth the complexity unless financial transactions are involved.

---

## BullMQ Patterns

### Worker Concurrency

```typescript
import { Worker } from 'bullmq';

const worker = new Worker('image-processing', async (job) => {
  await resizeImage(job.data);
}, {
  connection: redisConnection,
  concurrency: 5,          // 5 jobs in parallel per worker process
  limiter: {
    max: 100,              // rate limit: max 100 jobs
    duration: 60_000,      // per 60 seconds
  },
});
```

**Concurrency guide:**
- CPU-bound work (image processing, PDF generation): `concurrency = CPU cores`
- I/O-bound work (email sending, API calls): `concurrency = 10–50`
- Never set > 50 without profiling — thread pool exhaustion causes cascading failures

### Priority Queues

```typescript
// Add with priority (lower number = higher priority)
await queue.add('send-email', payload, { priority: 1 });   // urgent
await queue.add('send-email', payload, { priority: 10 });  // normal
await queue.add('send-email', payload, { priority: 100 }); // bulk
```

### Job Chaining

```typescript
const flow = await flowProducer.add({
  name: 'generate-report',
  queueName: 'reports',
  data: { reportId },
  children: [
    { name: 'fetch-data',   queueName: 'data-fetch',   data: { reportId } },
    { name: 'fetch-assets', queueName: 'asset-fetch',  data: { reportId } },
  ],
});
// generate-report waits until all children complete
```

### Cron Jobs

```typescript
await queue.add('daily-digest', {}, {
  repeat: { cron: '0 8 * * *' },  // every day at 08:00
  jobId: 'daily-digest-cron',      // stable ID prevents duplicate schedules
});
```

---

## Kafka Patterns

### Partition Key Strategy

Messages with the same key always go to the same partition — this is the **only** ordering guarantee Kafka provides.

```typescript
// Good: user events ordered per user
producer.send({
  topic: 'user-events',
  messages: [{ key: userId, value: JSON.stringify(event) }],
});

// Bad: null key → round-robin → no ordering
producer.send({
  topic: 'user-events',
  messages: [{ value: JSON.stringify(event) }],  // WARNING
});
```

**Key strategy guide:**
- User events → `userId`
- Order events → `orderId`
- Inventory updates → `productId`
- Audit logs (no ordering needed) → null or random

### Consumer Group Rebalancing

```typescript
const consumer = kafka.consumer({
  groupId: 'notification-service',
  sessionTimeout: 30_000,       // detect dead consumers in 30s
  heartbeatInterval: 3_000,
  maxBytesPerPartition: 1_048_576,  // 1MB per partition per fetch
});

consumer.on(consumer.events.REBALANCING, (e) => {
  logger.warn('Rebalancing started — pausing processing');
});
```

### Offset Management

```typescript
// Manual commit — commit only after successful processing
await consumer.run({
  eachMessage: async ({ topic, partition, message, heartbeat }) => {
    await processMessage(message);
    await consumer.commitOffsets([{
      topic, partition,
      offset: (Number(message.offset) + 1).toString(),
    }]);
  },
  autoCommit: false,  // critical: disable auto-commit
});
```

### Log Compaction

Use compacted topics for "latest state per key" (e.g., user profiles):

```
# Topic config
cleanup.policy=compact
min.cleanable.dirty.ratio=0.1
segment.ms=3600000
```

---

## RabbitMQ Patterns

### Exchange Types

| Exchange | Routes to | Use case |
|----------|-----------|----------|
| `direct` | Queues with exact binding key match | Task distribution by type |
| `fanout` | All bound queues | Broadcast events |
| `topic` | Queues matching wildcard pattern | Multi-attribute routing |
| `headers` | Queues matching header attributes | Complex routing without key |

### Topic Exchange Example

```typescript
// Producer
channel.publish('events', 'user.payment.completed', Buffer.from(msg));

// Consumer binding patterns:
channel.bindQueue('billing-queue',  'events', 'user.payment.*');
channel.bindQueue('audit-queue',    'events', 'user.#');       // all user events
channel.bindQueue('payment-queue',  'events', '*.payment.*');  // any payment
```

### Prefetch Count

```typescript
// Critical: set prefetch to limit messages in-flight per consumer
channel.prefetch(10);  // max 10 unacked messages per consumer

// prefetch: 0 = unlimited — NEVER do this in production
// Causes consumer OOM when queue has backlog
```

---

## `/queue:dlq` — Dead Letter Queue Patterns

### DLQ Architecture

```
Main Queue → Worker → [fail] → Retry Queue (backoff) → [max retries] → DLQ
```

### Exponential Backoff with Jitter (BullMQ)

```typescript
await queue.add('send-email', payload, {
  attempts: 5,
  backoff: {
    type: 'exponential',
    delay: 2000,  // base delay ms: 2s, 4s, 8s, 16s, 32s
  },
});
```

Manual backoff with jitter (prevents thundering herd):

```typescript
function backoffWithJitter(attempt: number, baseMs = 1000): number {
  const exponential = baseMs * Math.pow(2, attempt);
  const jitter = Math.random() * exponential * 0.3;  // ±30% jitter
  return Math.min(exponential + jitter, 60_000);     // cap at 60s
}
// attempt 0: ~1000ms, attempt 1: ~2000ms, attempt 2: ~4000ms...
```

### Poison Message Detection

A poison message causes every consumer to crash before it can be acked:

```typescript
worker.on('failed', async (job, err) => {
  const isPoisonMessage = (
    job.attemptsMade >= job.opts.attempts &&
    err.message.includes('SyntaxError')  // schema violation
  );

  if (isPoisonMessage) {
    await dlqQueue.add('poison', {
      originalJobId: job.id,
      originalQueue: job.queueName,
      payload: job.data,
      error: err.message,
      detectedAt: new Date().toISOString(),
    });
    logger.error({ jobId: job.id }, 'Poison message quarantined to DLQ');
  }
});
```

### DLQ Inspection and Replay

```typescript
// Inspect DLQ
const failedJobs = await dlqQueue.getFailed(0, 100);
for (const job of failedJobs) {
  console.log({ id: job.id, error: job.failedReason, data: job.data });
}

// Replay a specific job after fixing the bug
const job = await dlqQueue.getJob(jobId);
await originalQueue.add(job.name, job.data, {
  attempts: 3,
  jobId: `replay-${job.id}-${Date.now()}`,
});
await job.remove();
```

---

## `/queue:monitor` — Queue Health & Metrics

### Key Metrics to Track

| Metric | Warning threshold | Critical threshold |
|--------|------------------|-------------------|
| Queue depth | > 1000 jobs | > 10000 jobs |
| Job stall time | > 5 min | > 30 min |
| Failed job rate | > 1% | > 5% |
| Consumer lag (Kafka) | > 10k messages | > 100k messages |
| Redis memory usage | > 70% maxmemory | > 90% maxmemory |
| Processing throughput | < 50% baseline | < 20% baseline |

### BullMQ Queue Depth Alert

```typescript
async function checkQueueHealth(queue: Queue) {
  const counts = await queue.getJobCounts();
  const depth = counts.waiting + counts.delayed;

  if (depth > 10_000) {
    alert.fire(`Queue ${queue.name} depth critical: ${depth} jobs`);
  }

  const stallRate = counts.failed / (counts.completed + 1);
  if (stallRate > 0.05) {
    alert.fire(`Queue ${queue.name} fail rate: ${(stallRate * 100).toFixed(1)}%`);
  }
}
```

### Kafka Consumer Lag (kafkajs)

```typescript
const admin = kafka.admin();
const offsets = await admin.fetchOffsets({
  groupId: 'notification-service',
  topics: ['user-events'],
});

for (const topic of offsets) {
  for (const partition of topic.partitions) {
    const topicOffsets = await admin.fetchTopicOffsets(topic.topic);
    const latest = topicOffsets.find(o => o.partition === partition.partition);
    const lag = Number(latest.offset) - Number(partition.offset);

    if (lag > 50_000) {
      alert.fire(`Consumer lag on ${topic.topic}:${partition.partition} = ${lag}`);
    }
  }
}
```

### Redis Memory Pressure

```bash
redis-cli INFO memory | grep used_memory_human
redis-cli INFO memory | grep mem_fragmentation_ratio
# fragmentation > 1.5 = memory fragmentation issue
# used_memory > 80% maxmemory = eviction risk
```

---

## Python Tools

| Script | Purpose |
|--------|---------|
| `scripts/queue_health_checker.py` | Analyze a queue config JSON for misconfigurations; scaffold worker snippets |

**Usage:**

```bash
# Analyze a config file
python queue_health_checker.py --config queue.json

# JSON output for CI pipelines
python queue_health_checker.py --config queue.json --output json

# Scaffold a BullMQ TypeScript worker
python queue_health_checker.py --scaffold bullmq

# Scaffold a Kafka consumer
python queue_health_checker.py --scaffold kafka
```

---

## Cross-References

- `references/queue-patterns.md` — Complete code examples: BullMQ DLQ worker, Kafka consumer groups, RabbitMQ topic exchange, Redis Streams consumer group, idempotency key pattern, Prometheus metrics
- `engineering/observability/` — Prometheus, Grafana, alerting setup
- `engineering/redis/` — Redis configuration, clustering, persistence
