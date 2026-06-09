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
