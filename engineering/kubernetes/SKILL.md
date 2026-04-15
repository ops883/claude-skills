---
name: "kubernetes"
description: "Kubernetes raw manifest authoring and cluster operations skill for Claude Code — covers Deployment, StatefulSet, DaemonSet, Job, and CronJob authoring with right-sized resource requests/limits, RBAC least-privilege patterns (Role/ClusterRole, RoleBinding, ServiceAccount), NetworkPolicy default-deny and allow-specific rules, HPA and VPA configuration, rolling/blue-green/canary deployment strategies, ConfigMap and Secret management, liveness/readiness/startup probe design, PodDisruptionBudgets, node affinity and taints/tolerations, pod security contexts (runAsNonRoot, readOnlyRootFilesystem, drop ALL capabilities), multi-environment management with Kustomize, and kubectl operational patterns. Use when: user is writing or reviewing Kubernetes YAML manifests, configuring cluster RBAC, setting up autoscaling, debugging pod failures, hardening workload security, or managing multi-environment overlays without Helm."
license: MIT
metadata:
  version: 1.0.0
  author: ops883
  category: engineering
  updated: 2026-04-14
---

# Kubernetes

> Right-sized resources. Least-privilege RBAC. No runAsRoot.

Opinionated workflow for authoring production-grade Kubernetes manifests directly — not Helm charts. Covers every layer from pod security to cluster networking. Each section is a concrete decision, not a reference dump.

For Helm chart packaging and templating, see **helm-chart-builder**.

---

## Slash Commands

| Command | What it does |
|---------|-------------|
| `/k8s:manifest` | Author or review a Kubernetes manifest — resources, probes, security context, labels |
| `/k8s:rbac` | Design RBAC for a workload — ServiceAccount, Role/ClusterRole, RoleBinding, least privilege |
| `/k8s:audit` | Audit existing manifests for security, reliability, and operational issues |

---

## When This Skill Activates

Recognize these patterns:

- "Write a Kubernetes Deployment for..."
- "Review my k8s manifests"
- "Set up RBAC for this service"
- "Configure HPA / autoscaling"
- "Add network policies to my namespace"
- "My pod keeps crashing / OOMKilled / CrashLoopBackOff"
- "Set up blue-green / canary deployment"
- "Multi-environment Kubernetes without Helm"
- Any file ending in `.yaml` containing `apiVersion:` and `kind:`

If the user has raw Kubernetes YAML or wants to deploy without Helm → this skill applies.

---

## Workflow

### `/k8s:manifest` — Manifest Authoring

#### Step 1: Choose the right workload kind

| Workload | Kind | When |
|----------|------|------|
| Stateless service | `Deployment` | Web APIs, workers, background processors |
| Stateful with stable identity | `StatefulSet` | Databases, message queues, distributed systems |
| Every node | `DaemonSet` | Log collectors, CNI agents, monitoring |
| One-off task | `Job` | DB migrations, batch imports |
| Scheduled task | `CronJob` | Reports, cleanups, scheduled syncs |

#### Step 2: Always set resources

Every container **must** have `resources.requests` and `resources.limits`. No exceptions.

```yaml
resources:
  requests:
    cpu: "100m"
    memory: "128Mi"
  limits:
    cpu: "500m"
    memory: "256Mi"
```

Size requests to typical load. Size limits to burst ceiling. Never set limits lower than requests.

#### Step 3: Add probes

| Probe | Purpose | When to add |
|-------|---------|-------------|
| `livenessProbe` | Restart container if stuck | Always — guards against deadlocks |
| `readinessProbe` | Remove from Service endpoints | Always — prevents premature traffic |
| `startupProbe` | Allow slow startup | Slow-starting apps (>30s) |

#### Step 4: Harden the security context

```yaml
securityContext:               # pod-level
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000
  seccompProfile:
    type: RuntimeDefault
containers:
  - securityContext:           # container-level
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop: ["ALL"]
```

Add `emptyDir` volumes for any paths requiring writes (`/tmp`, cache dirs).

#### Step 5: Apply standard labels

```yaml
labels:
  app.kubernetes.io/name: my-service
  app.kubernetes.io/instance: my-service-prod
  app.kubernetes.io/version: "1.4.2"
  app.kubernetes.io/component: api
  app.kubernetes.io/part-of: my-platform
  app.kubernetes.io/managed-by: kubectl
```

---

### `/k8s:rbac` — RBAC Design

**Principle:** one ServiceAccount per workload. Never use `default`. Never grant more than the workload needs.

#### Decision tree

```
Does the pod call the Kubernetes API?
├── No  → Create SA with automountServiceAccountToken: false
└── Yes → What scope?
          ├── Namespace only → Role + RoleBinding
          └── Cluster-wide  → ClusterRole + ClusterRoleBinding (justify explicitly)
```

#### Least-privilege checklist

- [ ] Specific `resources` (never `*`)
- [ ] Specific `verbs` (never `*`)
- [ ] Specific `resourceNames` where possible
- [ ] No `secrets` get/list unless required
- [ ] No `pods/exec` unless required
- [ ] Reviewed by `kubectl auth can-i --list --as=system:serviceaccount:NAMESPACE:SA`

---

### `/k8s:audit` — Manifest Audit

Run the linter first:

```bash
python3 scripts/k8s_manifest_linter.py manifests/ --recursive
python3 scripts/k8s_manifest_linter.py deployment.yaml --output json
```

#### Audit categories

**CRITICAL — fix before deploying to production**
- Missing `resources.requests` or `resources.limits`
- `hostNetwork: true` or `hostPID: true`
- `privileged: true` in securityContext
- Wildcard RBAC permissions (`verbs: ["*"]` or `resources: ["*"]`)
- Secrets stored in ConfigMaps or env vars as plaintext

**WARNING — fix before merge**
- `image:latest` or mutable tag
- Missing `livenessProbe` or `readinessProbe`
- Missing `securityContext.runAsNonRoot`
- No `podAntiAffinity` with `replicas > 1`

**NOTE — address in next sprint**
- `replicas: 1` on critical Deployments
- Missing namespace declaration
- No PodDisruptionBudget on HA workloads
- Missing `imagePullPolicy` with mutable tags

---

## Deployment Strategies

### Rolling update (default)

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxUnavailable: 0        # zero downtime — never take a pod down before new one is ready
    maxSurge: 1              # one extra pod at a time
```

### Blue-green (manual via label swap)

1. Deploy `v2` Deployment with label `version: green`
2. Verify green pods are healthy
3. Patch Service selector: `kubectl patch svc my-svc -p '{"spec":{"selector":{"version":"green"}}}'`
4. Delete blue Deployment after traffic confirmed

### Canary (weight-based)

Run two Deployments sharing the same Service selector except for a `track` label. Control traffic split by replica ratio (e.g., 9 stable + 1 canary = 10% canary traffic). Promote by scaling up canary and scaling down stable.

---

## Autoscaling

### HPA (CPU/memory or custom metrics)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-service
  minReplicas: 2
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

**Rule:** set `requests.cpu` on all containers before enabling HPA — HPA calculates utilization relative to requests.

### VPA (right-sizing)

Use VPA in `Off` mode first to get recommendations without disruption:

```yaml
updatePolicy:
  updateMode: "Off"   # Recommendation only — apply manually
```

Promote to `Auto` only after validating recommendations in staging. Never run HPA and VPA (on CPU/memory) simultaneously.

---

## ConfigMap and Secret Management

**ConfigMap:** non-sensitive configuration only. Mount as files for complex config, env vars for simple key=value.

**Secret:** never commit to git. Use one of:
1. **External Secrets Operator** (recommended) — syncs from AWS Secrets Manager / Vault / GCP Secret Manager
2. **Sealed Secrets** — encrypt with cluster public key, safe to commit
3. **SOPS + Kustomize secret generator** — file-level encryption

```yaml
# Always set imagePullSecrets at the SA level, not per-pod
serviceAccountName: my-service
automountServiceAccountToken: false
```

---

## Multi-Environment with Kustomize

```
k8s/
├── base/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── kustomization.yaml
└── overlays/
    ├── staging/
    │   ├── kustomization.yaml    # patches: replicas=1, image tag
    │   └── patch-replicas.yaml
    └── production/
        ├── kustomization.yaml    # patches: replicas=3, HPA, PDB
        └── patch-resources.yaml
```

```bash
kubectl apply -k k8s/overlays/production/
kubectl diff -k k8s/overlays/production/     # dry-run diff before apply
```

---

## kubectl Patterns

```bash
# Get pod logs for crashed container (previous instance)
kubectl logs pod/my-pod -c my-container --previous

# Exec into a running pod (use ephemeral debug containers for read-only root fs)
kubectl debug -it my-pod --image=busybox --target=my-container

# Check what a ServiceAccount can do
kubectl auth can-i --list --as=system:serviceaccount:my-ns:my-sa -n my-ns

# Force rollout (triggers new pods without image change)
kubectl rollout restart deployment/my-service

# Watch rollout progress
kubectl rollout status deployment/my-service --timeout=120s

# Get resource usage (requires metrics-server)
kubectl top pods -n my-ns --sort-by=memory

# Dry-run apply with diff
kubectl diff -f manifests/
kubectl apply -f manifests/ --dry-run=server

# Label-based filtering
kubectl get pods -l app.kubernetes.io/name=my-service,app.kubernetes.io/version=1.4.2
```

---

## Python Tools

### `scripts/k8s_manifest_linter.py`

Static analysis for Kubernetes YAML manifests — no cluster connection required.

**Usage:**
```bash
# Lint a single file
python3 scripts/k8s_manifest_linter.py deployment.yaml

# Lint all manifests in a directory
python3 scripts/k8s_manifest_linter.py k8s/ --recursive

# JSON output (for CI integration)
python3 scripts/k8s_manifest_linter.py k8s/ --recursive --output json
```

**Checks:** missing resources, `image:latest`, missing probes, hostNetwork/hostPID, privileged containers, missing runAsNonRoot, single-replica deployments, missing podAntiAffinity, missing namespace.

**Exit codes:** `0` = clean or warnings only. `1` = CRITICAL findings present.

---

## Proactive Triggers

Flag these without being asked:

- **No resource limits** → Add them. OOMKilled is almost always a missing limit problem.
- **`image:latest`** → Pin to a digest or semver tag. Mutable tags break reproducibility.
- **No readinessProbe** → Add one. Services route traffic to pods before app is ready without it.
- **`runAsRoot` / no `runAsNonRoot`** → Set it. Container breakout is far more impactful as root.
- **`replicas: 1` on critical path** → Warn. Single pod = single point of failure on node drain.
- **No NetworkPolicy** → Add default-deny. Open egress is the most common lateral movement path.
- **RBAC with wildcards** → Replace with specific verbs and resources.

---

## Cross-References

- **helm-chart-builder** — for packaging these manifests into distributable Helm charts with values templating
- **ci-cd-pipeline-builder** — for automating `kubectl apply` in deployment pipelines
- **docker-development** — for building the container images referenced in these manifests
- **terraform-patterns** — for provisioning the clusters these manifests run on
- **observability-designer** — for adding metrics, tracing, and alerting to deployed workloads
