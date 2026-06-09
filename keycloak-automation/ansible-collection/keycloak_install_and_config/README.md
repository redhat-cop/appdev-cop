# Ansible Collection: appdev_cop.keycloak_install_and_config

An Ansible collection for installing and configuring Red Hat Build of Keycloak (RHBK) on **OpenShift** and **virtual machines** (RHEL/Fedora).

---

## Roles

| Role | Target Platform | Description |
|:-----|:----------------|:------------|
| `openshift` | OpenShift 4.12+ | Deploys Keycloak with PostgreSQL, Route, Secrets, and optional realm configuration |
| `vms` | RHEL 8/9, Fedora 39+ | Installs Keycloak from archive, configures systemd, PostgreSQL, firewall, and optional realm |

---

## Installation

### From source (local)

```bash
cd keycloak-automation/ansible-collection/keycloak_install_and_config
ansible-galaxy collection build
ansible-galaxy collection install appdev_cop-keycloak_install_and_config-1.0.0.tar.gz
```

### Dependencies

```bash
# For the openshift role
ansible-galaxy collection install kubernetes.core

# For the vms role
ansible-galaxy collection install community.general
```

---

## Quick Start

### Deploy on OpenShift

```bash
ansible-playbook playbooks/deploy_openshift.yml
```

This will:
1. Create a `keycloak` project
2. Deploy PostgreSQL with a PVC
3. Deploy Keycloak with health probes and resource limits
4. Create a TLS Route
5. Create a realm with example clients

### Deploy on a VM

```bash
ansible-playbook -i playbooks/inventory.ini playbooks/deploy_vms.yml
```

This will:
1. Install Java 21 and PostgreSQL
2. Download and configure Keycloak
3. Create a systemd service
4. Open firewall ports
5. Create a realm with example clients

---

## Collection Structure

```
keycloak_install_and_config/
├── galaxy.yml                      # Collection metadata
├── README.md
├── playbooks/
│   ├── deploy_openshift.yml        # Example: deploy on OpenShift
│   ├── deploy_vms.yml              # Example: deploy on VMs
│   └── inventory.ini               # Example inventory
├── roles/
│   ├── openshift/
│   │   ├── defaults/main.yml       # Default variables
│   │   ├── meta/main.yml           # Role metadata
│   │   ├── tasks/
│   │   │   ├── main.yml            # Orchestrates the full deployment
│   │   │   ├── postgres.yml        # PostgreSQL deployment
│   │   │   ├── deploy.yml          # Keycloak Deployment + Service
│   │   │   ├── route.yml           # TLS Route creation
│   │   │   ├── wait.yml            # Readiness check
│   │   │   └── configure_realm.yml # Realm, clients, scopes
│   │   ├── handlers/main.yml
│   │   └── README.md
│   └── vms/
│       ├── defaults/main.yml
│       ├── meta/main.yml
│       ├── tasks/
│       │   ├── main.yml            # Orchestrates the full installation
│       │   ├── java.yml            # Java installation
│       │   ├── postgres.yml        # PostgreSQL installation
│       │   ├── user.yml            # System user creation
│       │   ├── install.yml         # Download and extract Keycloak
│       │   ├── configure.yml       # Generate keycloak.conf, run build
│       │   ├── systemd.yml         # Systemd service setup
│       │   ├── firewall.yml        # Firewalld rules
│       │   ├── wait.yml            # Health check
│       │   └── configure_realm.yml # Realm and client creation
│       ├── templates/
│       │   ├── keycloak.conf.j2    # Keycloak configuration
│       │   └── keycloak.service.j2 # Systemd unit
│       ├── handlers/main.yml
│       └── README.md
└── plugins/
    ├── modules/
    └── module_utils/
```

---

## Configuration

Both roles share common variables for admin credentials, database, and realm configuration. Role-specific variables are prefixed:

- `keycloak_ocp_*` — OpenShift role
- `keycloak_vm_*` — VMs role

See each role's README for the full variable reference:

- [roles/openshift/README.md](roles/openshift/README.md)
- [roles/vms/README.md](roles/vms/README.md)

---

## License

Apache-2.0
