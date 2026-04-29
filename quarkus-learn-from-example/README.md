# Quarkus — Learn from Example

A structured collection of **Quarkus** examples organized by difficulty level — from first REST endpoint to production-grade patterns. Each example is self-contained with its own source code, configuration, and README explaining how to build, run, and test it.

> Inspired by [python-simple-example](https://github.com/paulomenon/python-simple-example) — same idea, different stack.

## Prerequisites

| Tool | Minimum Version | Notes |
|---|---|---|
| **JDK** | 17+ | GraalVM recommended for native builds |
| **Maven** | 3.9+ | Wrapper (`mvnw`) included in each example |
| **Quarkus CLI** *(optional)* | 3.x | `quarkus dev`, `quarkus build` shortcuts |
| **Podman** or **Docker** | latest | For container builds and dev services |
| **curl / httpie** | any | For testing endpoints |

### Install Quarkus CLI (optional)

```bash
# macOS
brew install quarkusio/tap/quarkus

# Linux (SDKMan)
sdk install quarkus

# Verify
quarkus --version
```

## Project Structure

```
quarkus-learn-from-example/
├── README.md                        ← you are here
├── beginner-level/
│   ├── README.md
│   ├── hello-world/                 # Minimal REST endpoint
│   ├── config-profiles/             # application.properties & profiles
│   ├── json-rest-api/               # JSON serialization with Jackson
│   ├── path-query-params/           # Path params, query params, defaults
│   ├── request-validation/          # Bean Validation (Hibernate Validator)
│   ├── simple-crud/                 # In-memory CRUD REST service
│   ├── logging-and-health/          # Health checks & structured logging
│   ├── error-handling/              # Exception mappers & problem details
│   ├── static-content/              # Serving static files and Qute templates
│   └── dev-services-intro/          # Quarkus Dev Services with PostgreSQL
│
├── intermediate-level/
│   ├── README.md
│   ├── panache-orm/                 # Hibernate ORM with Panache (Active Record)
│   ├── panache-repository/          # Panache Repository pattern
│   ├── rest-client/                 # MicroProfile REST Client (type-safe)
│   ├── lifecycle-events/            # Application startup/shutdown hooks
│   ├── scheduled-tasks/             # @Scheduled cron and interval jobs
│   ├── reactive-messaging-kafka/    # SmallRye Reactive Messaging + Kafka
│   ├── security-jwt/                # JWT RBAC authentication
│   ├── security-oidc-keycloak/      # OIDC with Keycloak Dev Service
│   ├── caching/                     # Application-level caching
│   └── testing-strategies/          # @QuarkusTest, REST Assured, mocking
│
└── advanced-level/
    ├── README.md
    ├── reactive-rest-api/           # RESTEasy Reactive + Mutiny
    ├── event-driven-microservice/   # Kafka consumers/producers, dead-letter
    ├── saga-pattern/                # Microservice saga with compensations
    ├── graphql-api/                 # SmallRye GraphQL (queries, mutations, subs)
    ├── grpc-service/                # gRPC server and client
    ├── native-build/                # GraalVM native image build & tuning
    ├── multi-tenancy/               # Per-tenant DB routing with Hibernate
    ├── fault-tolerance/             # @Retry, @CircuitBreaker, @Bulkhead, @Timeout
    ├── observability-stack/         # Metrics, Tracing (OpenTelemetry), Logging
    └── custom-extension/            # Building a Quarkus extension
```

## Levels at a Glance

### Beginner Level

Covers Quarkus fundamentals — creating endpoints, configuration, JSON, validation, and Dev Services.

| Folder | Example | Key Concepts |
|---|---|---|
| `hello-world/` | Hello World REST | JAX-RS `@Path`, `@GET`, Dev Mode |
| `config-profiles/` | Configuration & Profiles | `application.properties`, `%dev` / `%prod` profiles |
| `json-rest-api/` | JSON REST API | Jackson serialization, `@Produces(APPLICATION_JSON)` |
| `path-query-params/` | Path & Query Parameters | `@PathParam`, `@QueryParam`, `@DefaultValue` |
| `request-validation/` | Request Validation | `@Valid`, Bean Validation constraints |
| `simple-crud/` | In-Memory CRUD | `HashMap`-backed REST CRUD, HTTP methods |
| `logging-and-health/` | Logging & Health Checks | `jboss-logging`, MicroProfile Health, liveness/readiness |
| `error-handling/` | Error Handling | `ExceptionMapper`, RFC 7807 Problem Details |
| `static-content/` | Static Content & Templates | `META-INF/resources`, Qute templates |
| `dev-services-intro/` | Dev Services | Zero-config PostgreSQL via Testcontainers/Podman |

### Intermediate Level

Database persistence, REST clients, security (JWT/OIDC), Kafka messaging, scheduling, and testing.

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

### Advanced Level

Reactive, event-driven architecture, native builds, multi-tenancy, fault tolerance, and observability.

| Folder | Example | Key Concepts |
|---|---|---|
| `reactive-rest-api/` | Reactive REST | RESTEasy Reactive, `Uni<T>`, `Multi<T>`, Mutiny |
| `event-driven-microservice/` | Event-Driven Service | Kafka consumers/producers, dead-letter queues |
| `saga-pattern/` | Saga Pattern | Distributed transactions, compensation logic |
| `graphql-api/` | GraphQL API | SmallRye GraphQL, queries, mutations, subscriptions |
| `grpc-service/` | gRPC | Protobuf, gRPC server/client, streaming |
| `native-build/` | Native Image | GraalVM native build, reflection config, tuning |
| `multi-tenancy/` | Multi-Tenancy | Per-tenant datasource routing, tenant resolver |
| `fault-tolerance/` | Fault Tolerance | `@Retry`, `@CircuitBreaker`, `@Bulkhead`, `@Timeout` |
| `observability-stack/` | Observability | OpenTelemetry traces, Micrometer metrics, Grafana |
| `custom-extension/` | Custom Extension | Build-time augmentation, runtime config, recorder |

## How to Run Any Example

Every example follows the same convention:

```bash
cd quarkus-learn-from-example/<level>/<example>/

# Dev Mode (live reload)
./mvnw quarkus:dev

# Run tests
./mvnw test

# Package as JAR
./mvnw package
java -jar target/quarkus-app/quarkus-run.jar

# Container build (Podman)
podman build -f src/main/docker/Containerfile.jvm -t <example-name> .
podman run -p 8080:8080 <example-name>
```

## How to Run Tests Across Levels

```bash
# Run all tests in a specific level
cd quarkus-learn-from-example/beginner-level
for d in */; do (cd "$d" && ./mvnw -q test); done

# Run all tests across the entire project
for level in beginner-level intermediate-level advanced-level; do
  echo "=== $level ==="
  cd "quarkus-learn-from-example/$level"
  for d in */; do
    [ -f "$d/pom.xml" ] && (cd "$d" && echo "  Testing $d..." && ./mvnw -q test && echo "  ✓ PASS" || echo "  ✗ FAIL")
  done
  cd ../..
done
```

## References

- [Quarkus Guides](https://quarkus.io/guides/)
- [Quarkus Quickstarts (GitHub)](https://github.com/quarkusio/quarkus-quickstarts)
- [SmallRye Projects](https://smallrye.io/)
- [MicroProfile Specifications](https://microprofile.io/)
- [GraalVM Native Image](https://www.graalvm.org/latest/reference-manual/native-image/)
