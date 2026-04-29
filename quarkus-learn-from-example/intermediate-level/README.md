# Intermediate Level Examples

This folder contains intermediate Quarkus examples covering database persistence, REST clients, security (JWT and OIDC), messaging with Kafka, scheduling, caching, and testing strategies.

## Examples

| Folder | Example | Key Concepts |
|---|---|---|
| `panache-orm/` | Panache Active Record | `PanacheEntity`, `@Entity`, database CRUD |
| `panache-repository/` | Panache Repository | `PanacheRepository<T>`, separation of concerns |
| `rest-client/` | MicroProfile REST Client | `@RegisterRestClient`, type-safe HTTP calls |
| `lifecycle-events/` | Lifecycle Events | `@Observes StartupEvent`, `ShutdownEvent` |
| `scheduled-tasks/` | Scheduled Tasks | `@Scheduled(cron=...)`, interval-based jobs |
| `reactive-messaging-kafka/` | Kafka Messaging | `@Incoming`, `@Outgoing`, Kafka Dev Service |
| `security-jwt/` | JWT Security | MicroProfile JWT, `@RolesAllowed`, token generation |
| `security-oidc-keycloak/` | OIDC with Keycloak | `quarkus-oidc`, Keycloak Dev Service, token flow |
| `caching/` | Caching | `@CacheResult`, `@CacheInvalidate`, cache config |
| `testing-strategies/` | Testing | `@QuarkusTest`, REST Assured, `@InjectMock`, profiles |

## Prerequisites

Several examples use **Dev Services** which automatically start backing services (PostgreSQL, Kafka, Keycloak) via Podman/Docker when running in Dev Mode. Make sure Podman is running:

```bash
podman machine start
```

## How to Run

Each subfolder is a self-contained Quarkus project. Navigate into any folder, read its README, and run:

```bash
cd intermediate-level/panache-orm
./mvnw quarkus:dev
```

Then test with:

```bash
curl http://localhost:8080/fruits
```
