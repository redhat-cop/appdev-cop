# Ansible Collection: identity.platform

Enterprise identity-platform orchestration layer. Deploys Red Hat Build of Keycloak on OpenShift (or bare-metal), configures realms / clients / users through `redhat.rhbk`, and wires OpenShift OAuth to trust Keycloak as an OIDC identity provider — all driven by a single variable structure.

---

## Directory Tree

```
identity/platform/
├── galaxy.yml
├── README.md
├── inventory/
│   └── hosts.yml
├── playbooks/
│   ├── full-platform.yml          # Deploy everything end-to-end
│   ├── openshift-only.yml         # Deploy Keycloak infra on OpenShift only
│   ├── keycloak-only.yml          # Configure realms/clients/users only
│   └── integration.yml            # Wire OpenShift OAuth ↔ Keycloak
├── roles/
│   ├── auth/                      # Authentication context (OCP + Keycloak)
│   │   ├── defaults/main.yml
│   │   ├── meta/main.yml
│   │   └── tasks/
│   │       ├── main.yml
│   │       ├── openshift.yml      # Test OCP API connectivity
│   │       └── keycloak.yml       # Test Keycloak OIDC endpoint
│   │
│   ├── openshift_install/         # Deploy Keycloak on OpenShift (kubernetes.core)
│   │   ├── defaults/main.yml
│   │   ├── meta/main.yml
│   │   ├── handlers/main.yml
│   │   └── tasks/
│   │       ├── main.yml
│   │       ├── postgres.yml       # PostgreSQL PVC + Deployment + Service
│   │       ├── secrets.yml        # Admin + DB secrets
│   │       ├── deployment.yml     # Keycloak Deployment with probes
│   │       ├── service.yml        # Keycloak Service
│   │       ├── route.yml          # TLS Route + URL discovery
│   │       └── wait.yml           # Readiness gate
│   │
│   ├── openshift_rbac/            # Namespaces, ServiceAccounts, RoleBindings
│   │   ├── defaults/main.yml
│   │   ├── meta/main.yml
│   │   └── tasks/
│   │       ├── main.yml
│   │       ├── namespaces.yml
│   │       ├── service_accounts.yml
│   │       ├── rolebindings.yml
│   │       └── cluster_rolebindings.yml
│   │
│   ├── keycloak_install/          # Platform-aware install (openshift | baremetal)
│   │   ├── defaults/main.yml
│   │   ├── meta/main.yml
│   │   ├── templates/
│   │   │   ├── keycloak.conf.j2
│   │   │   └── keycloak.service.j2
│   │   └── tasks/
│   │       ├── main.yml
│   │       ├── platform_openshift.yml   # Delegates to openshift_install role
│   │       └── platform_baremetal.yml   # Java + PG + systemd
│   │
│   ├── keycloak_configure/        # Global settings (themes, SMTP, events)
│   │   ├── defaults/main.yml
│   │   ├── meta/main.yml
│   │   └── tasks/main.yml
│   │
│   ├── keycloak_realm/            # Realm management (redhat.rhbk)
│   │   ├── defaults/main.yml
│   │   ├── meta/main.yml
│   │   └── tasks/main.yml
│   │
│   ├── keycloak_clients/          # Client + client-role management (redhat.rhbk)
│   │   ├── defaults/main.yml
│   │   ├── meta/main.yml
│   │   └── tasks/
│   │       ├── main.yml
│   │       └── client.yml
│   │
│   ├── keycloak_users/            # User creation + role assignment
│   │   ├── defaults/main.yml
│   │   ├── meta/main.yml
│   │   └── tasks/
│   │       ├── main.yml
│   │       ├── user.yml
│   │       └── assign_client_roles.yml
│   │
│   └── integration/               # OpenShift ↔ Keycloak glue
│       ├── defaults/main.yml
│       ├── meta/main.yml
│       └── tasks/
│           ├── main.yml
│           ├── discover_keycloak.yml    # Fetch Route → build URL
│           ├── discover_cluster.yml     # Fetch cluster domain
│           ├── create_oauth_client.yml  # Create OIDC client in Keycloak
│           └── configure_oauth.yml      # Patch OCP OAuth CR
│
├── plugins/
│   ├── modules/
│   ├── module_utils/
│   └── filter/
└── docs/
```

---

## Roles

| Role | Scope | Uses | Purpose |
|:-----|:------|:-----|:--------|
| **auth** | Cross-cutting | `kubernetes.core`, `uri` | Validates OpenShift and Keycloak credentials; publishes `identity_auth` fact |
| **openshift_install** | OpenShift | `kubernetes.core` | Deploys PostgreSQL, Keycloak Deployment/Service/Route on OpenShift |
| **openshift_rbac** | OpenShift | `kubernetes.core` | Creates Namespaces, ServiceAccounts, RoleBindings, ClusterRoleBindings |
| **keycloak_install** | Platform-aware | Delegates | Routes to `openshift_install` or bare-metal path based on `keycloak_platform` |
| **keycloak_configure** | Keycloak | `uri` | Configures global settings: themes, SMTP, events |
| **keycloak_realm** | Keycloak | `redhat.rhbk` | Creates/updates realms with password policies, session settings |
| **keycloak_clients** | Keycloak | `redhat.rhbk` | Creates/updates clients and client roles |
| **keycloak_users** | Keycloak | `uri` | Creates users, sets passwords, assigns client roles |
| **integration** | Cross-cutting | `kubernetes.core`, `uri` | Discovers Keycloak route, creates OAuth client, patches OCP OAuth CR |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    identity.platform                         │
│                                                              │
│  ┌──────────┐                                                │
│  │   auth   │  ← validates credentials for both systems      │
│  └────┬─────┘                                                │
│       │                                                      │
│  ┌────▼──────────────┐    ┌───────────────────────────┐      │
│  │  OpenShift layer  │    │     Keycloak layer        │      │
│  │                   │    │                           │      │
│  │  openshift_install│    │  keycloak_install         │      │
│  │  openshift_rbac   │    │  keycloak_configure       │      │
│  │                   │    │  keycloak_realm            │      │
│  │  kubernetes.core  │    │  keycloak_clients          │      │
│  │  ────────────────│    │  keycloak_users            │      │
│  └────────┬──────────┘    │  redhat.rhbk              │      │
│           │               │  ─────────────────────────│      │
│           │               └──────────┬────────────────┘      │
│           │                          │                       │
│           └──────────┐  ┌────────────┘                       │
│                 ┌────▼──▼────┐                               │
│                 │ integration│  ← discovers route, wires     │
│                 │            │    OAuth/OIDC trust            │
│                 └────────────┘                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Variable Structure

The collection is designed around a single top-level structure that drives all roles:

```yaml
identity_platform:
  keycloak:
    admin_user: admin
    admin_password: changeme
    realm:
      name: AppRealm
      display_name: Application Realm
      enabled: true
      password_policy: "length(8) and digits(1) and upperCase(1)"
    clients:
      - client_id: frontend-spa
        realm: AppRealm
        public_client: true
        redirect_uris: ["https://app.example.com/*"]
        roles:
          - name: app-admin
          - name: app-user
      - client_id: backend-api
        realm: AppRealm
        public_client: false
        service_accounts_enabled: true
    users:
      - realm: AppRealm
        username: platform-admin
        email: admin@example.com
        password: changeme
        client_roles:
          - client_id: frontend-spa
            roles: [app-admin]
  openshift:
    namespace: keycloak
    teams:
      - name: team-alpha
        display_name: Team Alpha
    apps: []
```

---

## Installation

### Dependencies

```bash
ansible-galaxy collection install kubernetes.core
ansible-galaxy collection install redhat.rhbk
```

### Build from source

```bash
cd identity/platform
ansible-galaxy collection build
ansible-galaxy collection install identity-platform-1.0.0.tar.gz
```

---

## Quick Start

### Deploy everything (OpenShift + Keycloak + OAuth integration)

```bash
ansible-playbook identity/platform/playbooks/full-platform.yml \
  -e '{"identity_platform": {"keycloak": {"admin_password": "supersecret"}, "openshift": {"namespace": "my-keycloak"}}}'
```

### Deploy OpenShift infrastructure only

```bash
ansible-playbook identity/platform/playbooks/openshift-only.yml
```

### Configure Keycloak only (already running)

```bash
ansible-playbook identity/platform/playbooks/keycloak-only.yml \
  -e '{"identity_platform": {"keycloak": {"url": "https://keycloak.apps.mycluster.com"}}}'
```

### Wire OpenShift OAuth to existing Keycloak

```bash
ansible-playbook identity/platform/playbooks/integration.yml
```

---

## Platform Abstraction

The `keycloak_install` role supports:

```yaml
keycloak_platform: openshift   # → uses kubernetes.core (Deployment, Service, Route)
keycloak_platform: baremetal    # → uses dnf, systemd, templates
```

Set `keycloak_platform` at playbook level or via `-e keycloak_platform=baremetal`.

---

## Key Design Principles

1. **Separation of concerns** — OpenShift resources are managed exclusively through `kubernetes.core`; Keycloak configuration goes through `redhat.rhbk` or the Keycloak Admin REST API.
2. **No reimplementation** — The collection orchestrates existing modules; it never duplicates logic from `kubernetes.core` or `redhat.rhbk`.
3. **Fact-based integration** — The `auth` role publishes `identity_auth`, the `openshift_install` role publishes `keycloak_route_url`, and downstream roles consume these facts automatically.
4. **Variable-driven** — Every value is configurable; nothing is hardcoded. A single `identity_platform` dict drives the entire stack.
5. **Idempotent** — All tasks use `state: present` and accept 409 (conflict) responses gracefully.

---

## License

Apache-2.0
