# Role: vms

Installs and configures Red Hat Build of Keycloak (RHBK) on RHEL/Fedora virtual machines.

## What it does

1. Installs Java 21 (OpenJDK)
2. Installs and initializes PostgreSQL (optional — can use an external DB)
3. Creates a dedicated `keycloak` system user
4. Downloads and extracts the Keycloak distribution
5. Generates `keycloak.conf` from a Jinja2 template
6. Runs `kc.sh build` for optimized startup
7. Creates a systemd service unit
8. Opens firewall ports (firewalld)
9. Waits for Keycloak to respond on its health endpoint
10. Optionally configures a realm with clients

## Requirements

- RHEL 8/9 or Fedora 39+
- Root/sudo access on the target VM
- `community.general` Ansible collection (for PostgreSQL modules)

```bash
ansible-galaxy collection install community.general
```

## Role Variables

| Variable | Description | Default |
|:---------|:------------|:--------|
| `keycloak_vm_version` | Keycloak version to install | `24.0.4` |
| `keycloak_vm_install_dir` | Base install directory | `/opt/keycloak` |
| `keycloak_vm_use_rhbk` | Use RHBK archive instead of upstream | `false` |
| `keycloak_vm_rhbk_archive_url` | RHBK archive URL (when `use_rhbk: true`) | `""` |
| `keycloak_vm_install_java` | Install Java runtime | `true` |
| `keycloak_vm_java_package` | Java package name | `java-21-openjdk-headless` |
| `keycloak_admin_user` | Admin username | `admin` |
| `keycloak_admin_password` | Admin password | `changeme` |
| `keycloak_db_vendor` | Database type | `postgres` |
| `keycloak_db_host` | Database hostname | `localhost` |
| `keycloak_db_port` | Database port | `5432` |
| `keycloak_db_name` | Database name | `keycloak` |
| `keycloak_db_user` | Database username | `keycloak` |
| `keycloak_db_password` | Database password | `keycloak` |
| `keycloak_vm_install_postgres` | Install PostgreSQL locally | `true` |
| `keycloak_vm_http_port` | HTTP listen port | `8080` |
| `keycloak_vm_https_port` | HTTPS listen port | `8443` |
| `keycloak_vm_hostname` | Hostname for Keycloak (strict mode off if empty) | `""` |
| `keycloak_vm_tls_enabled` | Enable TLS | `false` |
| `keycloak_vm_tls_cert_file` | Path to TLS certificate | `""` |
| `keycloak_vm_tls_key_file` | Path to TLS private key | `""` |
| `keycloak_vm_service_name` | Systemd service name | `keycloak` |
| `keycloak_vm_configure_firewall` | Open ports in firewalld | `true` |
| `keycloak_vm_configure_realm` | Run realm configuration after install | `false` |
| `keycloak_realm_name` | Realm to create | `""` |
| `keycloak_clients` | List of clients to create | `[]` |

## Example

```yaml
- hosts: keycloak_servers
  become: true
  roles:
    - role: appdev_cop.keycloak_install_and_config.vms
      keycloak_admin_password: supersecret
      keycloak_vm_hostname: keycloak.example.com
      keycloak_vm_tls_enabled: true
      keycloak_vm_tls_cert_file: /etc/pki/tls/certs/keycloak.crt
      keycloak_vm_tls_key_file: /etc/pki/tls/private/keycloak.key
      keycloak_vm_configure_realm: true
      keycloak_realm_name: MyRealm
      keycloak_clients:
        - client_id: my-app
          public_client: true
```

## Using an External Database

Set `keycloak_vm_install_postgres: false` and configure the `keycloak_db_*` variables to point to your existing PostgreSQL instance.

## Using RHBK Instead of Upstream

Set `keycloak_vm_use_rhbk: true` and provide `keycloak_vm_rhbk_archive_url` pointing to the RHBK distribution archive. Adjust `keycloak_vm_version` and `keycloak_vm_home` as needed.
