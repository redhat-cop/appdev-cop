# Ansible Collections

This folder contains Ansible collections for identity platform automation.

## identity.platform

Enterprise orchestration layer that deploys Keycloak on OpenShift (or bare-metal), configures realms / clients / users through `redhat.rhbk`, and integrates OpenShift OAuth with Keycloak as an OIDC identity provider.

| Role | What it does |
|:-----|:-------------|
| `auth` | Validates OpenShift and Keycloak credentials |
| `openshift_install` | Deploys Keycloak + PostgreSQL on OpenShift via `kubernetes.core` |
| `openshift_rbac` | Manages namespaces, service accounts, role bindings |
| `keycloak_install` | Platform-aware install (OpenShift or bare-metal) |
| `keycloak_configure` | Global Keycloak settings (themes, SMTP, events) |
| `keycloak_realm` | Realm management via `redhat.rhbk` |
| `keycloak_clients` | Client + client-role management via `redhat.rhbk` |
| `keycloak_users` | User creation + role assignment |
| `integration` | Discovers Keycloak route, wires OpenShift OAuth/OIDC trust |

See the full documentation: [identity/platform/README.md](identity/platform/README.md)
