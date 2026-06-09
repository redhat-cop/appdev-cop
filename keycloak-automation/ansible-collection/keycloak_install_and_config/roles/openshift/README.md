# Role: openshift

Installs and configures Red Hat Build of Keycloak (RHBK) on OpenShift.

## What it does

1. Creates an OpenShift project (namespace)
2. Deploys a PostgreSQL database (optional — can use an external DB)
3. Creates Secrets for admin credentials and database connection
4. Deploys Keycloak with health/readiness probes and resource limits
5. Creates a TLS Route for external access
6. Waits for Keycloak to be ready
7. Optionally configures a realm with clients and client scopes

## Requirements

- OpenShift 4.12+
- `oc` CLI logged in or `kubeconfig` configured
- The `kubernetes.core` Ansible collection installed

```bash
ansible-galaxy collection install kubernetes.core
```

## Role Variables

| Variable | Description | Default |
|:---------|:------------|:--------|
| `keycloak_ocp_project` | OpenShift project/namespace | `keycloak` |
| `keycloak_ocp_app_name` | Application name for all resources | `keycloak` |
| `keycloak_ocp_image` | Container image | `registry.redhat.io/rhbk/keycloak-rhel9:latest` |
| `keycloak_ocp_replicas` | Number of Keycloak pods | `1` |
| `keycloak_admin_user` | Admin username | `admin` |
| `keycloak_admin_password` | Admin password | `changeme` |
| `keycloak_db_vendor` | Database type | `postgres` |
| `keycloak_db_host` | Database hostname | `postgres` |
| `keycloak_db_port` | Database port | `5432` |
| `keycloak_db_name` | Database name | `keycloak` |
| `keycloak_db_user` | Database username | `keycloak` |
| `keycloak_db_password` | Database password | `keycloak` |
| `keycloak_ocp_deploy_postgres` | Deploy PostgreSQL alongside Keycloak | `true` |
| `keycloak_ocp_postgres_storage_size` | PVC size for PostgreSQL | `1Gi` |
| `keycloak_ocp_hostname` | Hostname for the Route (auto-assigned if empty) | `""` |
| `keycloak_ocp_tls_enabled` | Create a TLS Route | `true` |
| `keycloak_ocp_route_tls_termination` | TLS termination type | `edge` |
| `keycloak_ocp_health_enabled` | Enable health endpoints | `true` |
| `keycloak_ocp_metrics_enabled` | Enable metrics endpoint | `true` |
| `keycloak_ocp_resources` | CPU/memory requests and limits | see `defaults/main.yml` |
| `keycloak_ocp_configure_realm` | Run realm configuration after install | `false` |
| `keycloak_realm_name` | Realm to create | `""` |
| `keycloak_clients` | List of clients to create | `[]` |
| `keycloak_client_scopes` | List of client scopes to create | `[]` |

## Example

```yaml
- hosts: localhost
  roles:
    - role: appdev_cop.keycloak_install_and_config.openshift
      keycloak_ocp_project: my-keycloak
      keycloak_admin_password: supersecret
      keycloak_ocp_configure_realm: true
      keycloak_realm_name: MyRealm
      keycloak_clients:
        - client_id: my-app
          public_client: true
          redirect_uris:
            - "https://my-app.example.com/*"
```

## Using an External Database

Set `keycloak_ocp_deploy_postgres: false` and configure the `keycloak_db_*` variables to point to your existing PostgreSQL instance.
