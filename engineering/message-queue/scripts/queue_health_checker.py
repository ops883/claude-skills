#!/usr/bin/env python3
"""
queue_health_checker.py — Analyze queue configuration files for misconfigurations.

Usage:
  python queue_health_checker.py --config queue.json
  python queue_health_checker.py --config queue.json --output json
  python queue_health_checker.py --scaffold bullmq
  python queue_health_checker.py --scaffold kafka
  python queue_health_checker.py --scaffold rabbitmq
  python queue_health_checker.py --scaffold redis-streams
"""

import argparse
import json
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(str, Enum):
    WARNING = "WARNING"
    NOTE = "NOTE"
    OK = "OK"


@dataclass
class Finding:
    severity: Severity
    queue: str
    check: str
    message: str
    recommendation: str


@dataclass
class AnalysisResult:
    queue_type: str
    total_queues: int
    findings: list[Finding] = field(default_factory=list)

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == Severity.WARNING]

    @property
    def notes(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == Severity.NOTE]


# ---------------------------------------------------------------------------
# Scaffold templates
# ---------------------------------------------------------------------------

BULLMQ_SCAFFOLD = '''\
// BullMQ Worker with DLQ and exponential backoff
// Install: npm install bullmq ioredis

import { Queue, Worker, Job } from "bullmq";
import IORedis from "ioredis";

const connection = new IORedis({ maxRetriesPerRequest: null });

// Main queue
const mainQueue = new Queue("email-send", { connection });

// Dead letter queue
const dlq = new Queue("email-send-dlq", { connection });

// Worker with concurrency + rate limiting
const worker = new Worker(
  "email-send",
  async (job: Job) => {
    const { to, subject, body } = job.data;
    // Idempotency check
    const alreadyDone = await redis.set(
      `processed:${job.id}`,
      "1",
      "NX",
      "EX",
      86400
    );
    if (!alreadyDone) {
      console.log(`Duplicate job ${job.id} — skipping`);
      return;
    }
    await sendEmail({ to, subject, body });
  },
  {
    connection,
    concurrency: 10,
    limiter: { max: 100, duration: 60_000 }, // 100 emails/min
  }
);

// Add jobs with retry + backoff
await mainQueue.add(
  "welcome-email",
  { to: "user@example.com", subject: "Welcome", body: "..." },
  {
    attempts: 5,
    backoff: { type: "exponential", delay: 2000 }, // 2s, 4s, 8s, 16s, 32s
    removeOnComplete: { count: 1000 },
    removeOnFail: false, // keep for DLQ inspection
  }
);

// Move to DLQ after max retries
worker.on("failed", async (job, err) => {
  if (!job) return;
  if (job.attemptsMade >= (job.opts.attempts ?? 1)) {
    await dlq.add("failed-job", {
      originalJobId: job.id,
      originalQueue: "email-send",
      payload: job.data,
      error: err.message,
      failedAt: new Date().toISOString(),
    });
    console.error(`Job ${job.id} moved to DLQ: ${err.message}`);
  }
});

worker.on("error", (err) => console.error("Worker error:", err));
'''

KAFKA_SCAFFOLD = '''\
// Kafka Consumer with manual offset commit and consumer group
// Install: npm install kafkajs

import { Kafka, EachMessagePayload } from "kafkajs";

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

const producer = kafka.producer();

async function run() {
  await consumer.connect();
  await consumer.subscribe({ topic: "user-events", fromBeginning: false });

  await consumer.run({
    autoCommit: false, // manual commit — never lose a message
    eachMessage: async ({ topic, partition, message }: EachMessagePayload) => {
      const key = message.key?.toString();
      const value = message.value?.toString();

      if (!value) return;

      let parsed: any;
      try {
        parsed = JSON.parse(value);
      } catch (err) {
        // Poison message — send to DLQ topic
        await producer.send({
          topic: "user-events-dlq",
          messages: [{ key, value, headers: { error: "invalid-json" } }],
        });
        // Still commit to avoid reprocessing
        await consumer.commitOffsets([
          { topic, partition, offset: (Number(message.offset) + 1).toString() },
        ]);
        return;
      }

      // Idempotency: use message offset as dedup key
      const dedupKey = `processed:${topic}:${partition}:${message.offset}`;
      // (store dedupKey in Redis with NX + EX 86400)

      await processEvent(parsed);

      // Commit only after successful processing
      await consumer.commitOffsets([
        { topic, partition, offset: (Number(message.offset) + 1).toString() },
      ]);
    },
  });
}

async function processEvent(event: any) {
  console.log("Processing:", event.type);
  // your logic here
}

run().catch(console.error);
'''

RABBITMQ_SCAFFOLD = '''\
// RabbitMQ Topic Exchange with DLQ and prefetch
// Install: npm install amqplib @types/amqplib

import amqp from "amqplib";

async function run() {
  const conn = await amqp.connect("amqp://localhost");
  const ch = await conn.createChannel();

  const EXCHANGE = "events";
  const MAIN_QUEUE = "notification-queue";
  const DLQ = "notification-queue-dlq";
  const DLX = "notification-dlx"; // dead letter exchange

  // Dead letter exchange (direct)
  await ch.assertExchange(DLX, "direct", { durable: true });
  await ch.assertQueue(DLQ, { durable: true });
  await ch.bindQueue(DLQ, DLX, MAIN_QUEUE);

  // Topic exchange
  await ch.assertExchange(EXCHANGE, "topic", { durable: true });

  // Main queue with DLX config
  await ch.assertQueue(MAIN_QUEUE, {
    durable: true,
    arguments: {
      "x-dead-letter-exchange": DLX,
      "x-dead-letter-routing-key": MAIN_QUEUE,
      "x-message-ttl": 3_600_000, // 1h max queue time
    },
  });

  // Bind: receive all user.* events
  await ch.bindQueue(MAIN_QUEUE, EXCHANGE, "user.#");

  // CRITICAL: set prefetch to prevent consumer OOM
  ch.prefetch(10);

  ch.consume(MAIN_QUEUE, async (msg) => {
    if (!msg) return;

    try {
      const event = JSON.parse(msg.content.toString());
      await handleEvent(event);
      ch.ack(msg);
    } catch (err) {
      // nack without requeue on poison message → goes to DLQ via DLX
      const requeue = (msg.fields.redelivered === false);
      ch.nack(msg, false, requeue);
    }
  });

  console.log("Consumer ready. Waiting for user.* events...");
}

async function handleEvent(event: any) {
  console.log("Handling:", event.type);
}

run().catch(console.error);
'''

REDIS_STREAMS_SCAFFOLD = '''\
// Redis Streams consumer group with manual ACK
// Install: npm install ioredis

import IORedis from "ioredis";

const redis = new IORedis();

const STREAM = "user-events";
const GROUP = "notification-service";
const CONSUMER = `consumer-${process.pid}`;

async function setup() {
  try {
    // Create consumer group (fromId "0" = read from beginning, "$" = new only)
    await redis.xgroup("CREATE", STREAM, GROUP, "$", "MKSTREAM");
  } catch (err: any) {
    if (!err.message.includes("BUSYGROUP")) throw err;
  }
}

async function consume() {
  while (true) {
    // ">" means: give me new messages not yet delivered to any consumer in group
    const results = await redis.xreadgroup(
      "GROUP", GROUP, CONSUMER,
      "COUNT", "10",
      "BLOCK", "2000",
      "STREAMS", STREAM, ">"
    ) as any;

    if (!results) continue; // timeout, try again

    for (const [, messages] of results) {
      for (const [id, fields] of messages) {
        const data: Record<string, string> = {};
        for (let i = 0; i < fields.length; i += 2) {
          data[fields[i]] = fields[i + 1];
        }

        try {
          await processMessage(id, data);
          // ACK after successful processing
          await redis.xack(STREAM, GROUP, id);
        } catch (err) {
          console.error(`Failed to process ${id}:`, err);
          // Message stays in PEL (Pending Entry List) for retry
        }
      }
    }
  }
}

// Reclaim stuck messages from dead consumers
async function reclaimPending(minIdleMs = 60_000) {
  const pending = await redis.xautoclaim(
    STREAM, GROUP, CONSUMER,
    minIdleMs.toString(), "0-0",
    "COUNT", "10"
  );
  // pending[1] contains reclaimed messages to reprocess
  return pending;
}

async function processMessage(id: string, data: Record<string, string>) {
  console.log("Processing stream message:", id, data);
}

await setup();
await consume();
'''

SCAFFOLDS: dict[str, str] = {
    "bullmq": BULLMQ_SCAFFOLD,
    "kafka": KAFKA_SCAFFOLD,
    "rabbitmq": RABBITMQ_SCAFFOLD,
    "redis-streams": REDIS_STREAMS_SCAFFOLD,
}


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

EMAIL_QUEUE_KEYWORDS = ("email", "notification", "notify", "sms", "push", "alert")


def check_common(queue: dict[str, Any]) -> list[Finding]:
    findings = []
    name = queue.get("name", "<unnamed>")

    # max_retries: 0 = silent failures
    if queue.get("max_retries") == 0:
        findings.append(Finding(
            severity=Severity.WARNING,
            queue=name,
            check="max_retries",
            message="max_retries is 0 — failed jobs will be silently dropped.",
            recommendation="Set max_retries to at least 3. Add a DLQ to capture persistent failures.",
        ))

    # No DLQ
    if not queue.get("dlq", False):
        findings.append(Finding(
            severity=Severity.WARNING,
            queue=name,
            check="dlq",
            message="DLQ is disabled — failed jobs have nowhere to go after max retries.",
            recommendation="Enable dlq:true and configure a dead letter queue for inspection and replay.",
        ))

    # High concurrency
    concurrency = queue.get("concurrency")
    if isinstance(concurrency, int) and concurrency > 50:
        findings.append(Finding(
            severity=Severity.WARNING,
            queue=name,
            check="concurrency",
            message=f"concurrency={concurrency} is very high and risks thread/connection pool exhaustion.",
            recommendation="For I/O-bound work keep concurrency <= 50. Profile before going higher.",
        ))

    # Email/notification queue without rate limit
    if any(kw in name.lower() for kw in EMAIL_QUEUE_KEYWORDS):
        if not queue.get("rate_limit"):
            findings.append(Finding(
                severity=Severity.NOTE,
                queue=name,
                check="rate_limit",
                message="Email/notification queue has no rate_limit configured.",
                recommendation="Add rate_limit to avoid spam classification or provider throttling (e.g. 100/min).",
            ))

    # High retries without jitter noted
    max_retries = queue.get("max_retries")
    if isinstance(max_retries, int) and max_retries > 10:
        if not queue.get("backoff_jitter", False):
            findings.append(Finding(
                severity=Severity.NOTE,
                queue=name,
                check="backoff_jitter",
                message=f"max_retries={max_retries} without jitter can cause thundering herd on retry storms.",
                recommendation="Add backoff_jitter:true or implement exponential backoff with ±30% jitter.",
            ))

    return findings


def check_kafka(queue: dict[str, Any]) -> list[Finding]:
    findings = []
    name = queue.get("name", "<unnamed>")

    if not queue.get("partition_key_strategy"):
        findings.append(Finding(
            severity=Severity.WARNING,
            queue=name,
            check="partition_key_strategy",
            message="No partition_key_strategy set — all messages will land on partition 0.",
            recommendation=(
                "Set partition_key_strategy to 'userId', 'orderId', or another high-cardinality key "
                "to distribute load and preserve per-entity ordering."
            ),
        ))

    return findings


def check_rabbitmq(queue: dict[str, Any]) -> list[Finding]:
    findings = []
    name = queue.get("name", "<unnamed>")

    prefetch = queue.get("prefetch")
    if prefetch == 0:
        findings.append(Finding(
            severity=Severity.WARNING,
            queue=name,
            check="prefetch",
            message="prefetch=0 means unlimited in-flight messages — consumers will OOM under backlog.",
            recommendation="Set prefetch to 10–50. This is the single most important RabbitMQ performance setting.",
        ))

    return findings


def analyze(config: dict[str, Any]) -> AnalysisResult:
    queue_type = config.get("type", "unknown").lower()
    queues = config.get("queues", [])

    result = AnalysisResult(queue_type=queue_type, total_queues=len(queues))

    for queue in queues:
        result.findings.extend(check_common(queue))

        if queue_type == "kafka":
            result.findings.extend(check_kafka(queue))
        elif queue_type == "rabbitmq":
            result.findings.extend(check_rabbitmq(queue))

    # If no findings at all, add an OK summary
    if not result.findings:
        result.findings.append(Finding(
            severity=Severity.OK,
            queue="all",
            check="overall",
            message="No issues detected.",
            recommendation="Keep monitoring queue depth, consumer lag, and DLQ growth.",
        ))

    return result


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------

def format_human(result: AnalysisResult) -> str:
    lines = []
    lines.append(f"Queue Health Report")
    lines.append(f"  Type    : {result.queue_type}")
    lines.append(f"  Queues  : {result.total_queues}")
    lines.append(f"  Warnings: {len(result.warnings)}")
    lines.append(f"  Notes   : {len(result.notes)}")
    lines.append("")

    for finding in result.findings:
        prefix = {
            Severity.WARNING: "[WARNING]",
            Severity.NOTE: "[NOTE]   ",
            Severity.OK: "[OK]     ",
        }[finding.severity]

        lines.append(f"{prefix} {finding.queue} / {finding.check}")
        lines.append(f"         {finding.message}")
        lines.append(f"         => {finding.recommendation}")
        lines.append("")

    if result.warnings:
        lines.append(f"Result: {len(result.warnings)} WARNING(s) found — fix before production.")
    elif result.notes:
        lines.append(f"Result: {len(result.notes)} NOTE(s) — review recommended.")
    else:
        lines.append("Result: All checks passed.")

    return "\n".join(lines)


def format_json(result: AnalysisResult) -> str:
    output = {
        "queue_type": result.queue_type,
        "total_queues": result.total_queues,
        "summary": {
            "warnings": len(result.warnings),
            "notes": len(result.notes),
        },
        "findings": [
            {
                "severity": f.severity.value,
                "queue": f.queue,
                "check": f.check,
                "message": f.message,
                "recommendation": f.recommendation,
            }
            for f in result.findings
        ],
    }
    return json.dumps(output, indent=2)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Analyze queue config files for misconfigurations, or scaffold worker templates.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python queue_health_checker.py --config queue.json
  python queue_health_checker.py --config queue.json --output json
  python queue_health_checker.py --scaffold bullmq
  python queue_health_checker.py --scaffold kafka
  python queue_health_checker.py --scaffold rabbitmq
  python queue_health_checker.py --scaffold redis-streams

Config JSON format:
  {
    "type": "bullmq",
    "queues": [
      {"name": "email-send", "concurrency": 5, "max_retries": 3, "dlq": true, "rate_limit": null},
      {"name": "image-process", "concurrency": 1, "max_retries": 0, "dlq": false}
    ]
  }

Supported types: bullmq, kafka, rabbitmq, redis-streams
""",
    )
    parser.add_argument(
        "--config", "-c",
        metavar="FILE",
        help="Path to queue config JSON file to analyze.",
    )
    parser.add_argument(
        "--output", "-o",
        choices=["human", "json"],
        default="human",
        help="Output format (default: human).",
    )
    parser.add_argument(
        "--scaffold", "-s",
        choices=list(SCAFFOLDS.keys()),
        metavar="TYPE",
        help=f"Print a scaffold worker snippet. Choices: {', '.join(SCAFFOLDS)}",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    # Scaffold mode
    if args.scaffold:
        print(SCAFFOLDS[args.scaffold])
        return 0

    # Config analysis mode
    if not args.config:
        parser.print_help()
        return 1

    try:
        with open(args.config, "r", encoding="utf-8") as fh:
            config = json.load(fh)
    except FileNotFoundError:
        print(f"Error: File not found: {args.config}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"Error: Invalid JSON in {args.config}: {exc}", file=sys.stderr)
        return 2

    if not isinstance(config.get("queues"), list):
        print("Error: Config must have a 'queues' array.", file=sys.stderr)
        return 2

    result = analyze(config)

    if args.output == "json":
        print(format_json(result))
    else:
        print(format_human(result))

    # Exit code: 1 if warnings found (useful in CI)
    return 1 if result.warnings else 0


if __name__ == "__main__":
    sys.exit(main())
