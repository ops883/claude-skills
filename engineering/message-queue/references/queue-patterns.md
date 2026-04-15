# Queue Patterns Reference

Complete code examples for message queue patterns across BullMQ, Kafka, RabbitMQ, and Redis Streams.

---

## Decision Matrix

| Use Case | Best Choice | Why |
|----------|-------------|-----|
| Background jobs (email, resize, export) | **BullMQ** | Built-in retry, DLQ, cron, priority — runs on Redis you likely already have |
| High-throughput event streaming | **Kafka** | Partitioned log, replay, consumer groups, compaction |
| Complex routing between services | **RabbitMQ** | Topic/header exchanges, flexible binding rules |
| Lightweight pub/sub on existing Redis | **Redis Streams** | No extra infra, consumer groups, persistent log |
| Scheduled/delayed jobs | **BullMQ** | Native cron + delayed job support |
| Exactly-once with transactions | **Kafka** | Transactional producer API |
| Fan-out broadcast to N services | **RabbitMQ fanout** or **Kafka** | Depends on throughput: RabbitMQ for low, Kafka for high |
| Per-entity ordering required | **Kafka** (partition key) or **RabbitMQ** (single queue) | Kafka: order per partition; RabbitMQ: order per queue |
| < 1000 jobs/day, simple ops team | **BullMQ** | Simplest to run; no Kafka/RabbitMQ to operate |

---

## BullMQ: Full Worker with DLQ and Exponential Backoff

```typescript
import { Queue, Worker, Job, FlowProducer } from "bullmq";
import IORedis from "ioredis";

const connection = new IORedis({ maxRetriesPerRequest: null });

// ── Queues ──────────────────────────────────────────────────────────────────
const emailQueue = new Queue("email-send", { connection });
const dlq        = new Queue("email-send-dlq", { connection });

// ── Add a job ───────────────────────────────────────────────────────────────
await emailQueue.add(
  "welcome",
  {
    id: crypto.randomUUID(),     // idempotency key
    to: "alice@example.com",
    subject: "Welcome to Acme",
  },
  {
    attempts: 5,
    backoff: { type: "exponential", delay: 2_000 },  // 2s 4s 8s 16s 32s
    removeOnComplete: { count: 1_000 },
    removeOnFail: false,
  }
);

// ── Worker ──────────────────────────────────────────────────────────────────
const worker = new Worker(
  "email-send",
  async (job: Job) => {
    // Idempotency: skip if already processed
    const stored = await connection.set(
      `idem:${job.data.id}`, "1", "NX", "EX", 86_400
    );
    if (!stored) {
      console.log(`[skip] duplicate job ${job.id}`);
      return;
    }
    await sendEmail(job.data);
  },
  {
    connection,
    concurrency: 10,
    limiter: { max: 100, duration: 60_000 },  // 100 emails/min
  }
);

// ── DLQ on final failure ────────────────────────────────────────────────────
worker.on("failed", async (job, err) => {
  if (!job) return;
  if (job.attemptsMade >= (job.opts.attempts ?? 1)) {
    await dlq.add("dead", {
      originalJobId: job.id,
      queue: "email-send",
      payload: job.data,
      error: err.message,
      stack: err.stack,
      failedAt: new Date().toISOString(),
    });
  }
});

// ── Job chaining (flow) ─────────────────────────────────────────────────────
const flow = new FlowProducer({ connection });
await flow.add({
  name: "generate-report",
  queueName: "reports",
  data: { reportId: "123" },
  children: [
    { name: "fetch-data",   queueName: "fetchers", data: { src: "db" } },
    { name: "fetch-assets", queueName: "fetchers", data: { src: "s3" } },
  ],
});

// ── Cron job ────────────────────────────────────────────────────────────────
await emailQueue.add(
  "daily-digest",
  {},
  {
    repeat: { cron: "0 8 * * *" },
    jobId: "daily-digest-cron",  // stable ID prevents duplicate cron registrations
  }
);

async function sendEmail(data: { to: string; subject: string }) {
  console.log(`Sending to ${data.to}: ${data.subject}`);
}
```

---

## Kafka: Consumer Group with Offset Management

```typescript
import { Kafka, EachMessagePayload, KafkaMessage } from "kafkajs";

const kafka = new Kafka({
  clientId: "notification-service",
  brokers: ["kafka:9092"],
  retry: { retries: 5, initialRetryTime: 300 },
});

const consumer = kafka.consumer({
  groupId: "notification-service-v1",
  sessionTimeout: 30_000,
  heartbeatInterval: 3_000,
});
const producer = kafka.producer({ transactionalId: "notif-producer" });
const admin    = kafka.admin();

// ── Consumer group run ──────────────────────────────────────────────────────
await consumer.connect();
await consumer.subscribe({ topic: "user-events", fromBeginning: false });

await consumer.run({
  autoCommit: false,  // NEVER auto-commit — you decide when to advance

  eachMessage: async ({ topic, partition, message }: EachMessagePayload) => {
    const raw = message.value?.toString();
    if (!raw) {
      await commitOffset(consumer, topic, partition, message);
      return;
    }

    let event: any;
    try {
      event = JSON.parse(raw);
    } catch {
      // Poison message — route to DLQ topic, then commit
      await producer.send({
        topic: "user-events-dlq",
        messages: [{
          key: message.key,
          value: message.value,
          headers: {
            "x-error": "invalid-json",
            "x-source-topic": topic,
            "x-source-partition": String(partition),
            "x-source-offset": message.offset,
          },
        }],
      });
      await commitOffset(consumer, topic, partition, message);
      return;
    }

    // Idempotency using offset as dedup key
    const dedupKey = `idem:${topic}:${partition}:${message.offset}`;
    const isNew = await redis.set(dedupKey, "1", "NX", "EX", 86_400);
    if (isNew) {
      await processEvent(event);
    }

    await commitOffset(consumer, topic, partition, message);
  },
});

async function commitOffset(
  c: typeof consumer,
  topic: string,
  partition: number,
  msg: KafkaMessage
) {
  await c.commitOffsets([{
    topic,
    partition,
    offset: (Number(msg.offset) + 1).toString(),
  }]);
}

// ── Consumer lag monitoring ─────────────────────────────────────────────────
async function checkConsumerLag(groupId: string, topic: string) {
  await admin.connect();
  const [groupOffsets, topicOffsets] = await Promise.all([
    admin.fetchOffsets({ groupId, topics: [topic] }),
    admin.fetchTopicOffsets(topic),
  ]);

  for (const tEntry of groupOffsets) {
    for (const p of tEntry.partitions) {
      const latest = topicOffsets.find(o => o.partition === p.partition);
      if (!latest) continue;
      const lag = Number(latest.offset) - Number(p.offset);
      console.log(`Partition ${p.partition} lag: ${lag}`);
      if (lag > 50_000) {
        console.warn(`HIGH LAG on ${topic}:${p.partition} = ${lag}`);
      }
    }
  }
  await admin.disconnect();
}

async function processEvent(event: any) { /* ... */ }
```

---

## RabbitMQ: Topic Exchange with DLQ

```typescript
import amqp, { Channel, Connection, ConsumeMessage } from "amqplib";

const MAIN_EXCHANGE = "events";
const DLX           = "events-dlx";
const QUEUE         = "notification-queue";
const DLQ           = "notification-queue-dlq";

async function setupRabbitMQ(): Promise<{ ch: Channel; conn: Connection }> {
  const conn = await amqp.connect("amqp://localhost");
  const ch   = await conn.createChannel();

  // Dead-letter exchange (direct)
  await ch.assertExchange(DLX, "direct", { durable: true });
  await ch.assertQueue(DLQ, { durable: true });
  await ch.bindQueue(DLQ, DLX, QUEUE);

  // Topic exchange for main routing
  await ch.assertExchange(MAIN_EXCHANGE, "topic", { durable: true });

  // Main queue wired to DLX
  await ch.assertQueue(QUEUE, {
    durable: true,
    arguments: {
      "x-dead-letter-exchange":    DLX,
      "x-dead-letter-routing-key": QUEUE,
      "x-message-ttl":             3_600_000,  // 1h max age
    },
  });

  // Routing patterns
  await ch.bindQueue(QUEUE, MAIN_EXCHANGE, "user.#");         // all user events
  await ch.bindQueue(QUEUE, MAIN_EXCHANGE, "order.created");  // specific event

  // CRITICAL — limit in-flight messages to prevent OOM
  ch.prefetch(10);

  return { ch, conn };
}

async function startConsumer() {
  const { ch } = await setupRabbitMQ();

  ch.consume(QUEUE, async (msg: ConsumeMessage | null) => {
    if (!msg) return;

    try {
      const event = JSON.parse(msg.content.toString());
      await handleEvent(event);
      ch.ack(msg);
    } catch (err) {
      // First delivery: requeue once. Redelivery: nack → goes to DLQ via DLX
      if (!msg.fields.redelivered) {
        ch.nack(msg, false, true);   // requeue once
      } else {
        ch.nack(msg, false, false);  // DLX takes it
      }
    }
  });
}

// Exchange type cheat-sheet:
// direct  — exact routing key match     (task queues by type)
// fanout  — all bound queues            (broadcast)
// topic   — wildcard patterns           (multi-attribute routing)
//           *  matches one word
//           #  matches zero or more words
// headers — match on message headers    (complex routing without a key)

async function handleEvent(event: any) { /* ... */ }
```

---

## Redis Streams: Consumer Group

```typescript
import IORedis from "ioredis";

const redis    = new IORedis();
const STREAM   = "user-events";
const GROUP    = "notification-service";
const CONSUMER = `worker-${process.pid}`;

async function setup() {
  try {
    // "$" = only new messages after group creation
    await redis.xgroup("CREATE", STREAM, GROUP, "$", "MKSTREAM");
  } catch (err: any) {
    if (!err.message.includes("BUSYGROUP")) throw err;
  }
}

async function consume() {
  while (true) {
    // ">" = new messages for this consumer group
    const result = await redis.xreadgroup(
      "GROUP", GROUP, CONSUMER,
      "COUNT", "10",
      "BLOCK", "2000",
      "STREAMS", STREAM, ">"
    ) as [string, [string, string[]][]][] | null;

    if (!result) continue;

    for (const [, messages] of result) {
      for (const [id, fields] of messages) {
        const data: Record<string, string> = {};
        for (let i = 0; i < fields.length; i += 2) {
          data[fields[i]] = fields[i + 1];
        }

        try {
          await processMessage(id, data);
          await redis.xack(STREAM, GROUP, id);  // advance consumer group cursor
        } catch (err) {
          console.error(`Failed to process ${id}:`, err);
          // Message stays in PEL (Pending Entry List) — reclaimed below
        }
      }
    }
  }
}

// Reclaim messages stuck in PEL (dead consumer recovery)
async function reclaimStuck(minIdleMs = 60_000) {
  // XAUTOCLAIM: atomically transfer idle PEL entries to this consumer
  const [, claimed] = await redis.xautoclaim(
    STREAM, GROUP, CONSUMER,
    String(minIdleMs), "0-0",
    "COUNT", "10"
  ) as [string, [string, string[]][]];

  console.log(`Reclaimed ${claimed.length} stuck messages`);
  return claimed;
}

async function processMessage(id: string, data: Record<string, string>) {
  console.log("Stream message:", id, data);
}

await setup();
await consume();
```

---

## Idempotency Key Pattern

The core contract: every message carries a stable `id`. Consumers check before processing.

```typescript
// Generating deterministic idempotency keys (for scheduled sends)
import { createHash } from "crypto";

function deterministicId(namespace: string, ...parts: string[]): string {
  return createHash("sha256")
    .update([namespace, ...parts].join(":"))
    .digest("hex")
    .slice(0, 32);
}

// Example: one welcome email per user, never duplicate
const msgId = deterministicId("welcome-email", userId);

// Redis dedup check (NX = only set if Not eXists)
async function processOnce(
  redis: IORedis,
  id: string,
  ttlSeconds: number,
  handler: () => Promise<void>
): Promise<"processed" | "duplicate"> {
  const acquired = await redis.set(`idem:${id}`, "1", "NX", "EX", ttlSeconds);
  if (!acquired) return "duplicate";
  await handler();
  return "processed";
}

// Usage
const result = await processOnce(redis, msg.id, 86_400, async () => {
  await sendWelcomeEmail(msg.payload);
});
if (result === "duplicate") logger.info({ id: msg.id }, "Skip duplicate");
```

---

## Exponential Backoff with Jitter

Prevents thundering herd when many consumers retry simultaneously.

**Formula:**
```
delay = min(cap, base * 2^attempt) + random(0, base * 2^attempt * jitter_factor)
```

```typescript
interface BackoffOptions {
  baseMs?: number;       // default 1000
  capMs?: number;        // default 60_000
  jitter?: number;       // fraction 0-1, default 0.3
}

function exponentialBackoff(
  attempt: number,
  { baseMs = 1_000, capMs = 60_000, jitter = 0.3 }: BackoffOptions = {}
): number {
  const exponential = Math.min(capMs, baseMs * Math.pow(2, attempt));
  const jitterMs    = Math.random() * exponential * jitter;
  return Math.floor(exponential + jitterMs);
}

// Example delays (approximate):
// attempt 0:  1000ms ± 300ms
// attempt 1:  2000ms ± 600ms
// attempt 2:  4000ms ± 1200ms
// attempt 3:  8000ms ± 2400ms
// attempt 4: 16000ms ± 4800ms
// attempt 5: 32000ms ± 9600ms

// In a retry loop
async function withRetry<T>(
  fn: () => Promise<T>,
  maxAttempts = 5
): Promise<T> {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (err) {
      if (attempt === maxAttempts - 1) throw err;
      const delay = exponentialBackoff(attempt);
      console.warn(`Attempt ${attempt + 1} failed. Retrying in ${delay}ms`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error("unreachable");
}
```

---

## Poison Message Detection

A poison message crashes every consumer that touches it, creating an infinite retry loop.

```typescript
interface PoisonDetector {
  maxFailuresBeforeQuarantine: number;
  failureCounts: Map<string, number>;
}

function createPoisonDetector(max = 3): PoisonDetector {
  return { maxFailuresBeforeQuarantine: max, failureCounts: new Map() };
}

async function handleWithPoisonDetection(
  detector: PoisonDetector,
  messageId: string,
  dlq: Queue,
  originalQueue: string,
  payload: unknown,
  handler: () => Promise<void>
): Promise<void> {
  try {
    await handler();
    detector.failureCounts.delete(messageId);  // reset on success
  } catch (err: any) {
    const count = (detector.failureCounts.get(messageId) ?? 0) + 1;
    detector.failureCounts.set(messageId, count);

    const isPoison = count >= detector.maxFailuresBeforeQuarantine;
    const isSchemaError = err instanceof SyntaxError
      || err.message?.includes("validation")
      || err.message?.includes("schema");

    if (isPoison || isSchemaError) {
      console.error(`Quarantining poison message ${messageId}`);
      await dlq.add("poison", {
        messageId,
        originalQueue,
        payload,
        error: err.message,
        failureCount: count,
        quarantinedAt: new Date().toISOString(),
      });
      detector.failureCounts.delete(messageId);
    } else {
      throw err;  // let normal retry logic handle it
    }
  }
}
```

**Signs of a poison message:**
- Job fails on every worker, every time
- Error is consistent (schema mismatch, null pointer on specific field)
- Job ID appears repeatedly in DLQ within a short window

**Replay after fix:**
```typescript
async function replayFromDlq(dlq: Queue, target: Queue, jobId: string) {
  const dead = await dlq.getJob(jobId);
  if (!dead) throw new Error(`Job ${jobId} not found in DLQ`);

  await target.add(dead.name, dead.data, {
    attempts: 3,
    backoff: { type: "exponential", delay: 2_000 },
    jobId: `replay-${dead.id}-${Date.now()}`,
  });

  await dead.remove();
  console.log(`Replayed ${jobId} to ${target.name}`);
}
```

---

## Prometheus Queue Metrics

```typescript
import { Gauge, Counter, Histogram, register } from "prom-client";
import { Queue } from "bullmq";

// ── Gauges ──────────────────────────────────────────────────────────────────
const queueDepth = new Gauge({
  name: "queue_depth",
  help: "Number of jobs waiting to be processed",
  labelNames: ["queue_name", "status"],
});

const consumerLag = new Gauge({
  name: "kafka_consumer_lag",
  help: "Messages behind the latest offset",
  labelNames: ["topic", "partition", "group_id"],
});

const redisMemoryUsage = new Gauge({
  name: "redis_memory_used_bytes",
  help: "Redis used memory in bytes",
  labelNames: ["instance"],
});

// ── Counters ────────────────────────────────────────────────────────────────
const jobsProcessed = new Counter({
  name: "queue_jobs_total",
  help: "Total jobs processed",
  labelNames: ["queue_name", "result"],  // result: success | failed | duplicate
});

const dlqJobsTotal = new Counter({
  name: "queue_dlq_jobs_total",
  help: "Jobs routed to DLQ",
  labelNames: ["queue_name", "reason"],
});

// ── Histograms ──────────────────────────────────────────────────────────────
const jobDuration = new Histogram({
  name: "queue_job_duration_seconds",
  help: "Job processing time",
  labelNames: ["queue_name"],
  buckets: [0.01, 0.1, 0.5, 1, 5, 30, 60],
});

// ── Collector ───────────────────────────────────────────────────────────────
async function collectBullMQMetrics(queues: Queue[]) {
  for (const q of queues) {
    const counts = await q.getJobCounts(
      "waiting", "active", "completed", "failed", "delayed"
    );

    for (const [status, count] of Object.entries(counts)) {
      queueDepth.set({ queue_name: q.name, status }, count);
    }
  }
}

// Expose /metrics endpoint (Express example)
// app.get("/metrics", async (req, res) => {
//   await collectBullMQMetrics(queues);
//   res.set("Content-Type", register.contentType);
//   res.end(await register.metrics());
// });
```

**Grafana alert rules (PromQL):**
```promql
# Queue depth critical
queue_depth{status="waiting"} > 10000

# DLQ growth rate
rate(queue_dlq_jobs_total[5m]) > 0.1

# Consumer lag critical
kafka_consumer_lag > 100000

# High failure rate
rate(queue_jobs_total{result="failed"}[5m])
  / rate(queue_jobs_total[5m]) > 0.05
```
