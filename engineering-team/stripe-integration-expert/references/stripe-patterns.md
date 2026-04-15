# Stripe Integration Patterns

Reference material for testing, feature gating, customer portal, and billing utilities.

---

## Testing with Stripe CLI

```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Login
stripe login

# Forward webhooks to local dev
stripe listen --forward-to localhost:3000/api/webhooks/stripe

# Trigger specific events for testing
stripe trigger checkout.session.completed
stripe trigger customer.subscription.updated
stripe trigger invoice.payment_failed

# Test with specific customer
stripe trigger customer.subscription.updated \
  --override subscription:customer=cus_xxx

# View recent events
stripe events list --limit 10

# Test cards
# Success:              4242 4242 4242 4242
# Requires 3DS auth:   4000 0025 0000 3155
# Decline:             4000 0000 0000 9995
# Insufficient funds:  4000 0000 0000 0069
# Expired card:        4000 0000 0000 0069
```

---

## Customer Portal

```typescript
// app/api/billing/portal/route.ts
import { NextResponse } from "next/server"
import { stripe } from "@/lib/stripe"
import { getAuthUser } from "@/lib/auth"

export async function POST() {
  const user = await getAuthUser()
  if (!user?.stripeCustomerId) {
    return NextResponse.json({ error: "No billing account" }, { status: 400 })
  }

  const portalSession = await stripe.billingPortal.sessions.create({
    customer: user.stripeCustomerId,
    return_url: `${process.env.NEXT_PUBLIC_APP_URL}/settings/billing`,
  })

  return NextResponse.json({ url: portalSession.url })
}
```

**Note:** Customer portal features (cancel, plan change, payment method update) must be enabled in Stripe Dashboard → Billing → Customer portal settings.

---

## Feature Gating Helper

```typescript
// lib/subscription.ts
export function isSubscriptionActive(user: {
  subscriptionStatus: string | null
  stripeCurrentPeriodEnd: Date | null
}): boolean {
  if (!user.subscriptionStatus) return false
  if (["active", "trialing"].includes(user.subscriptionStatus)) return true
  // Grace period: past_due but not yet expired
  if (user.subscriptionStatus === "past_due" && user.stripeCurrentPeriodEnd) {
    return user.stripeCurrentPeriodEnd > new Date()
  }
  return false
}

// Middleware usage
export async function requireActiveSubscription() {
  const user = await getAuthUser()
  if (!isSubscriptionActive(user)) {
    redirect("/billing?reason=subscription_required")
  }
}
```

---

## Subscription Status Reference

| Status | Meaning | isActive? |
|--------|---------|-----------|
| `active` | Paid and current | ✅ |
| `trialing` | In free trial | ✅ |
| `past_due` | Payment failed, retrying | ✅ (grace period) |
| `canceled` | Cancelled by user or Stripe | ❌ |
| `unpaid` | All retries exhausted | ❌ |
| `incomplete` | Initial payment pending | ❌ |
| `paused` | Paused via billing thresholds | ❌ |

---

## Idempotency Keys

Always pass idempotency keys for mutations to prevent double-charges on retry:

```typescript
// Safe to retry — same key = same result
await stripe.paymentIntents.create(
  { amount: 2000, currency: "usd", customer: customerId },
  { idempotencyKey: `pi-${orderId}` }
)
```

Use a deterministic key derived from your business entity ID, not a random UUID.

---

## Metadata Strategy

Always attach `userId` (and other relevant IDs) to Stripe objects at creation time:

```typescript
const session = await stripe.checkout.sessions.create({
  // ...
  metadata: {
    userId: user.id,
    planId: selectedPlan,
  },
})
```

You cannot link a Stripe subscription back to your user without metadata — add it to customers, subscriptions, and checkout sessions.
