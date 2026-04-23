# Keycloak Automation with Ansible

Ansible playbooks and examples for automating [Red Hat Build of Keycloak (RHBK)](https://access.redhat.com/products/red-hat-build-of-keycloak) configuration. RHBK is the enterprise, supported version of the upstream [Keycloak](https://www.keycloak.org/) project.

This folder demonstrates two approaches to Keycloak automation:

1. **Using the `redhat.rhbk` Ansible collection** — for tasks the collection supports natively (realms, clients, user federation)
2. **Using direct REST API calls (`uri` module)** — for tasks not yet covered by the collection (client scopes, authentication flows, protocol mappers)

---

## Folder Structure

```
keycloak-automation/
├── playbooks/                      # Ansible playbooks using REST API (uri module)
│   ├── generate_rhbk_token.yaml          # Generate an admin token for API calls
│   ├── rhbk_create_client_scope.yaml     # Create a client scope in a realm
│   ├── rhbk_add_protocol_mapper.yaml     # Add protocol mappers to a client scope
│   ├── rhbk_add_authentication_flow.yaml # Create a top-level authentication flow
│   ├── rhbk_add_sub_flow.yaml            # Add a sub-flow to an authentication flow
│   ├── rhbk_add_steps_to_flow.yaml       # Add execution steps to a sub-flow
│   ├── rhbk_update_flow_requirement.yaml # Update execution requirement (REQUIRED/ALTERNATIVE/etc.)
│   ├── inventory.ini                     # Inventory file for localhost
│   └── README.md
│
├── rhbk_collection_playbook/       # Ansible playbooks using the redhat.rhbk collection
│   ├── rhbk_realm.yaml                   # Create realm with clients, roles, and users
│   ├── rhbk_federation_ldap.yaml         # Configure LDAP user federation
│   ├── requirements.txt                  # Python dependencies
│   └── README.md
│
└── ansible-collection/             # Placeholder for custom Ansible collection modules
    └── README.md
```

---

## Prerequisites

- Python 3.10+
- Ansible Core 2.16+
- A running RHBK or Keycloak instance
- Access to the admin console credentials

### Install dependencies

```bash
pip install -r rhbk_collection_playbook/requirements.txt
```

### Install the RHBK collection (for collection-based playbooks)

```bash
ansible-galaxy collection install redhat.rhel_system_roles
ansible-galaxy collection install redhat.runtimes_common
ansible-galaxy collection install redhat.rhbk
```

> For upstream Keycloak, use `middleware_automation.keycloak` instead of `redhat.rhbk`.

---

## Playbooks — REST API Approach (`playbooks/`)

These playbooks use the Ansible `uri` module to call the Keycloak Admin REST API directly. This approach is needed for features that the collection does not yet support as native modules, such as client scopes, protocol mappers, and authentication flows.

### Token generation

Most playbooks import `generate_rhbk_token.yaml` to authenticate first. You can also run it standalone:

```bash
ansible-playbook -i playbooks/inventory.ini playbooks/generate_rhbk_token.yaml
```

### Client scope and protocol mappers

Create a client scope, then add token claim mappers (email, firstName, username):

```bash
ansible-playbook -i playbooks/inventory.ini playbooks/rhbk_create_client_scope.yaml
ansible-playbook -i playbooks/inventory.ini playbooks/rhbk_add_protocol_mapper.yaml
```

### Authentication flows

Build a custom authentication flow step by step:

```bash
# 1. Create a top-level flow
ansible-playbook -i playbooks/inventory.ini playbooks/rhbk_add_authentication_flow.yaml

# 2. Add a sub-flow to it
ansible-playbook -i playbooks/inventory.ini playbooks/rhbk_add_sub_flow.yaml

# 3. Add execution steps (e.g. username-password form) to the sub-flow
ansible-playbook -i playbooks/inventory.ini playbooks/rhbk_add_steps_to_flow.yaml

# 4. Update the requirement for a sub-flow or execution (REQUIRED, ALTERNATIVE, etc.)
ansible-playbook -i playbooks/inventory.ini playbooks/rhbk_update_flow_requirement.yaml
```

---

## Playbooks — Collection Approach (`rhbk_collection_playbook/`)

These playbooks use the `redhat.rhbk` collection roles, which handle authentication, idempotency, and error handling internally.

### Create a realm with clients and users

```bash
ansible-playbook -i playbooks/inventory.ini rhbk_collection_playbook/rhbk_realm.yaml
```

### Configure LDAP user federation

```bash
ansible-playbook -i playbooks/inventory.ini rhbk_collection_playbook/rhbk_federation_ldap.yaml
```

> **Note:** The `rhbk_context` variable must be set to an empty string (`""`) for Quarkus-based RHBK/Keycloak. The legacy `/auth` context path is no longer used. A fix for this default has been submitted upstream — see [ansible-middleware/keycloak#325](https://github.com/ansible-middleware/keycloak/pull/325).

---

## Configuration

All playbooks use variables that can be overridden at runtime. Common variables:

| Variable | Description | Default |
|:---------|:------------|:--------|
| `rhbk_url` / `rhbk_server_url` | Keycloak server URL | `http://localhost:8080` |
| `rhbk_admin_user` | Admin username | `keycloak-admin` |
| `rhbk_admin_password` | Admin password | `redhat123` |
| `rhbk_realm` | Target realm name | `TestRealm` |
| `rhbk_context` | Context path (empty for Quarkus) | `""` |
| `no_log` / `rhbk_no_log` | Hide sensitive output | `false` |

Override at runtime:

```bash
ansible-playbook playbooks/rhbk_add_authentication_flow.yaml \
  -e rhbk_url=https://keycloak.example.com \
  -e rhbk_admin_password=mysecretpassword \
  -e rhbk_realm=ProductionRealm
```

---

## When to Use Which Approach

| Task | Collection (`redhat.rhbk`) | REST API (`uri`) |
|:-----|:---------------------------|:-----------------|
| Create realms | Yes | — |
| Create clients with roles and users | Yes | — |
| Configure LDAP/AD federation | Yes | — |
| Create client scopes | — | Yes |
| Add protocol mappers | — | Yes |
| Create authentication flows | — | Yes |
| Add sub-flows and executions | — | Yes |
| Update execution requirements | — | Yes |

> New modules for client scopes and authentication flows have been contributed upstream — see [ansible-middleware/keycloak PR](https://github.com/ansible-middleware/keycloak/pull/325). Once merged, these tasks will also be available natively in the collection.

---

## Related Resources

- [Keycloak Admin REST API documentation](https://www.keycloak.org/docs-api/latest/rest-api/index.html)
- [redhat.rhbk Ansible collection](https://console.redhat.com/ansible/automation-hub/repo/published/redhat/rhbk/)
- [middleware_automation.keycloak (upstream)](https://github.com/ansible-middleware/keycloak)
- [Red Hat Build of Keycloak documentation](https://access.redhat.com/documentation/en-us/red_hat_build_of_keycloak/)
