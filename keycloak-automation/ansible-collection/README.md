# Ansible Collection — Keycloak Install and Config

This folder contains the `appdev_cop.keycloak_install_and_config` Ansible collection for deploying and configuring Red Hat Build of Keycloak (RHBK).

## Roles

| Role | Target | What it does |
|:-----|:-------|:-------------|
| `openshift` | OpenShift 4.12+ | Deploy Keycloak with PostgreSQL, Route, Secrets, and realm configuration |
| `vms` | RHEL 8/9 / Fedora | Install Keycloak from archive, systemd service, PostgreSQL, firewall, realm |

## Getting started

See the full documentation inside the collection:

- [Collection README](keycloak_install_and_config/README.md)
- [OpenShift role README](keycloak_install_and_config/roles/openshift/README.md)
- [VMs role README](keycloak_install_and_config/roles/vms/README.md)

## Build and install

```bash
cd keycloak_install_and_config
ansible-galaxy collection build
ansible-galaxy collection install appdev_cop-keycloak_install_and_config-1.0.0.tar.gz
```
# Ansible Collections

This folder contains Ansible collections for identity platform automation.

## cop_custom.keycloak_ops

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

See the full documentation: [cop_custom/keycloak_ops/README.md](cop_custom/keycloak_ops/README.md)
