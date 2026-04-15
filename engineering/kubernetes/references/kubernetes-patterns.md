# Kubernetes Patterns Reference

Concrete YAML patterns for production workloads. Copy, adapt, deploy.

---

## 1. Resource Limits Template

Always set both requests and limits. Requests drive scheduling; limits prevent runaway containers.

```yaml
resources:
  requests:
    cpu: "100m"       # 0.1 vCPU — typical idle cost
    memory: "128Mi"   # baseline resident set size
  limits:
    cpu: "500m"       # 0.5 vCPU — burst ceiling
    memory: "256Mi"   # hard cap — exceeded = OOMKill
```

**Sizing rules:**
- Set requests at ~P50 observed usage, limits at ~P99
- CPU limits throttle (not kill); memory limits kill
- Never set limits < requests
- For JVM workloads: set `-Xmx` to 75% of `limits.memory` to leave headroom for the JVM itself

---

## 2. RBAC Least-Privilege Pattern

One ServiceAccount per workload. Namespace-scoped Role unless cluster-wide access is justified.

```yaml
# 1. ServiceAccount — one per workload, no auto-mount
apiVersion: v1
kind: ServiceAccount
metadata:
  name: my-service
  namespace: my-ns
automountServiceAccountToken: false   # opt-in per pod, not per SA
---
# 2. Role — only what the workload actually needs
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: my-service
  namespace: my-ns
rules:
  - apiGroups: [""]
    resources: ["configmaps"]
    resourceNames: ["my-service-config"]   # lock to specific resource name
    verbs: ["get", "watch"]
  - apiGroups: [""]
    resources: ["secrets"]
    resourceNames: ["my-service-secret"]
    verbs: ["get"]
---
# 3. RoleBinding — connect SA to Role
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: my-service
  namespace: my-ns
subjects:
  - kind: ServiceAccount
    name: my-service
    namespace: my-ns
roleRef:
  kind: Role
  name: my-service
  apiGroup: rbac.authorization.k8s.io
```

**Verification:**
```bash
kubectl auth can-i --list \
  --as=system:serviceaccount:my-ns:my-service \
  -n my-ns
```

---

## 3. NetworkPolicy: Default-Deny + Allow-Specific

Apply default-deny first, then explicitly allow required traffic. Works at the namespace or pod selector level.

```yaml
# Default-deny: block all ingress and egress in namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: my-ns
spec:
  podSelector: {}       # matches all pods in namespace
  policyTypes:
    - Ingress
    - Egress
---
# Allow: frontend can reach backend on port 8080
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-backend
  namespace: my-ns
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: backend
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app.kubernetes.io/name: frontend
      ports:
        - protocol: TCP
          port: 8080
---
# Allow: backend egress to external DB on port 5432
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-backend-db-egress
  namespace: my-ns
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: backend
  policyTypes:
    - Egress
  egress:
    - ports:
        - protocol: TCP
          port: 5432
    - ports:                # DNS — always allow or nothing resolves
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53
```

**Note:** Calico, Cilium, and Antrea enforce NetworkPolicy. Flannel does not — verify your CNI.

---

## 4. HPA with Custom Metrics

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-service-hpa
  namespace: my-ns
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-service
  minReplicas: 2
  maxReplicas: 20
  metrics:
    # Standard: scale on CPU utilization
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    # Custom: scale on request queue depth (requires custom metrics adapter)
    - type: Pods
      pods:
        metric:
          name: http_requests_per_second
        target:
          type: AverageValue
          averageValue: "1000"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300   # wait 5 min before scaling down
      policies:
        - type: Percent
          value: 10
          periodSeconds: 60             # remove at most 10% per minute
    scaleUp:
      stabilizationWindowSeconds: 0    # scale up immediately
      policies:
        - type: Pods
          value: 4
          periodSeconds: 60            # add at most 4 pods per minute
```

**Prerequisite:** `resources.requests.cpu` must be set or HPA cannot calculate utilization.

---

## 5. Deployment with Blue-Green Strategy

Blue-green via two Deployments + Service selector swap. No extra controllers needed.

```yaml
# Blue (current stable)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-service-blue
  namespace: my-ns
spec:
  replicas: 3
  selector:
    matchLabels:
      app.kubernetes.io/name: my-service
      version: blue
  template:
    metadata:
      labels:
        app.kubernetes.io/name: my-service
        version: blue
    spec:
      containers:
        - name: my-service
          image: my-registry/my-service:1.4.2
          # ... resources, probes, securityContext
---
# Green (new version — deploy, verify, then flip Service)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-service-green
  namespace: my-ns
spec:
  replicas: 3
  selector:
    matchLabels:
      app.kubernetes.io/name: my-service
      version: green
  template:
    metadata:
      labels:
        app.kubernetes.io/name: my-service
        version: green
    spec:
      containers:
        - name: my-service
          image: my-registry/my-service:1.5.0
          # ... resources, probes, securityContext
---
# Service — points at blue initially
apiVersion: v1
kind: Service
metadata:
  name: my-service
  namespace: my-ns
spec:
  selector:
    app.kubernetes.io/name: my-service
    version: blue                  # change to 'green' to flip traffic
  ports:
    - port: 80
      targetPort: 8080
```

**Cutover:**
```bash
kubectl patch svc my-service -n my-ns \
  -p '{"spec":{"selector":{"version":"green"}}}'
# Verify, then delete blue
kubectl delete deployment my-service-blue -n my-ns
```

---

## 6. Liveness and Readiness Probe Patterns

```yaml
containers:
  - name: my-service
    # HTTP probe — most common for web services
    livenessProbe:
      httpGet:
        path: /healthz
        port: 8080
      initialDelaySeconds: 10    # wait before first probe
      periodSeconds: 10          # probe every 10s
      timeoutSeconds: 3          # fail if no response in 3s
      failureThreshold: 3        # restart after 3 consecutive failures

    readinessProbe:
      httpGet:
        path: /ready              # separate endpoint — checks DB connections etc.
        port: 8080
      initialDelaySeconds: 5
      periodSeconds: 5
      timeoutSeconds: 2
      failureThreshold: 2         # remove from Service after 2 failures
      successThreshold: 2         # require 2 successes before re-adding

    # startupProbe — for slow-starting apps (prevents liveness killing them)
    startupProbe:
      httpGet:
        path: /healthz
        port: 8080
      failureThreshold: 30        # allow up to 300s (30 * 10s) to start
      periodSeconds: 10

    # TCP probe — for non-HTTP services
    # livenessProbe:
    #   tcpSocket:
    #     port: 5432
    #   initialDelaySeconds: 15
    #   periodSeconds: 20

    # Exec probe — last resort, avoid if possible (forks a process)
    # livenessProbe:
    #   exec:
    #     command: ["pg_isready", "-U", "postgres"]
    #   initialDelaySeconds: 30
    #   periodSeconds: 10
```

**Pattern:** liveness probes should check "is the process fundamentally broken?" (not dependencies). Readiness probes check "is the process ready to serve traffic?" (including dependency health).

---

## 7. PodDisruptionBudget

Ensure Kubernetes never takes down too many pods at once during voluntary disruptions (node drains, cluster upgrades).

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: my-service-pdb
  namespace: my-ns
spec:
  # Option A: minimum available (prefer for critical services)
  minAvailable: 2                # at least 2 pods must remain available
  # Option B: maximum unavailable (prefer when expressing tolerance)
  # maxUnavailable: 1

  selector:
    matchLabels:
      app.kubernetes.io/name: my-service
```

**Rules:**
- `minAvailable` + `maxUnavailable` are mutually exclusive — pick one
- For a 3-replica Deployment: `minAvailable: 2` or `maxUnavailable: 1` are equivalent
- PDB does NOT prevent involuntary disruptions (node failure, OOMKill)

---

## 8. Secret Management with External Secrets Operator

Never store real secrets in manifests or ConfigMaps. Use External Secrets Operator to sync from your secrets backend.

```yaml
# ExternalSecret — declares "fetch this secret from AWS Secrets Manager"
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: my-service-db-creds
  namespace: my-ns
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager      # ClusterSecretStore configured by platform team
    kind: ClusterSecretStore
  target:
    name: my-service-db-creds      # name of the Kubernetes Secret to create
    creationPolicy: Owner
  data:
    - secretKey: DB_PASSWORD       # key in the Kubernetes Secret
      remoteRef:
        key: prod/my-service/db    # path in AWS Secrets Manager
        property: password         # field within the JSON secret
    - secretKey: DB_USER
      remoteRef:
        key: prod/my-service/db
        property: username
```

Reference the synced Secret in your Deployment:

```yaml
envFrom:
  - secretRef:
      name: my-service-db-creds
```

**Alternatives:**
- **Sealed Secrets** — encrypt with cluster public key, commit to git: `kubeseal < secret.yaml > sealed-secret.yaml`
- **SOPS + Kustomize** — file-level encryption with age/PGP keys, decrypted at apply time

---

## 9. Multi-Environment with Kustomize

```
k8s/
├── base/
│   ├── kustomization.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   └── serviceaccount.yaml
└── overlays/
    ├── staging/
    │   ├── kustomization.yaml
    │   └── patch-deployment.yaml
    └── production/
        ├── kustomization.yaml
        ├── patch-deployment.yaml
        └── hpa.yaml
```

**base/kustomization.yaml:**
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - deployment.yaml
  - service.yaml
  - serviceaccount.yaml
commonLabels:
  app.kubernetes.io/managed-by: kustomize
```

**overlays/production/kustomization.yaml:**
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../base
  - hpa.yaml                       # production-only resources
patches:
  - path: patch-deployment.yaml
images:
  - name: my-registry/my-service
    newTag: "1.5.0"                # override image tag per environment
```

**overlays/production/patch-deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-service
spec:
  replicas: 3
  template:
    spec:
      containers:
        - name: my-service
          resources:
            requests:
              cpu: "200m"
              memory: "256Mi"
            limits:
              cpu: "1000m"
              memory: "512Mi"
```

**Apply:**
```bash
# Dry-run diff before applying
kubectl diff -k k8s/overlays/production/

# Apply
kubectl apply -k k8s/overlays/production/

# Build rendered manifests (for review or piping to kubectl)
kubectl kustomize k8s/overlays/production/
```

---

## 10. Full Deployment Template (production-hardened)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-service
  namespace: my-ns
  labels:
    app.kubernetes.io/name: my-service
    app.kubernetes.io/version: "1.5.0"
    app.kubernetes.io/component: api
    app.kubernetes.io/managed-by: kubectl
spec:
  replicas: 3
  selector:
    matchLabels:
      app.kubernetes.io/name: my-service
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0
      maxSurge: 1
  template:
    metadata:
      labels:
        app.kubernetes.io/name: my-service
        app.kubernetes.io/version: "1.5.0"
    spec:
      serviceAccountName: my-service
      automountServiceAccountToken: false
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
        seccompProfile:
          type: RuntimeDefault
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              podAffinityTerm:
                topologyKey: kubernetes.io/hostname
                labelSelector:
                  matchLabels:
                    app.kubernetes.io/name: my-service
      containers:
        - name: my-service
          image: my-registry/my-service:1.5.0
          imagePullPolicy: IfNotPresent
          ports:
            - name: http
              containerPort: 8080
              protocol: TCP
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop: ["ALL"]
          resources:
            requests:
              cpu: "200m"
              memory: "256Mi"
            limits:
              cpu: "1000m"
              memory: "512Mi"
          livenessProbe:
            httpGet:
              path: /healthz
              port: http
            initialDelaySeconds: 10
            periodSeconds: 10
            timeoutSeconds: 3
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /ready
              port: http
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 2
            failureThreshold: 2
          volumeMounts:
            - name: tmp
              mountPath: /tmp
      volumes:
        - name: tmp
          emptyDir: {}
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: topology.kubernetes.io/zone
          whenUnsatisfiable: ScheduleAnyway
          labelSelector:
            matchLabels:
              app.kubernetes.io/name: my-service
```
