# Advanced Level Examples

This folder contains advanced Quarkus examples covering reactive programming, event-driven architecture, distributed patterns, GraphQL, gRPC, native builds, multi-tenancy, fault tolerance, observability, and custom extension development.

## Examples

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

## Prerequisites

- **GraalVM 17+** — required for the `native-build/` example
- **Podman** — Dev Services for Kafka, PostgreSQL, Jaeger, Grafana
- **protoc** *(optional)* — only if modifying `.proto` files in `grpc-service/`

```bash
# Install GraalVM via SDKMan
sdk install java 17.0.11-graal

# Verify native-image is available
native-image --version
```

## How to Run

Each subfolder is a self-contained Quarkus project. Navigate into any folder, read its README, and run:

```bash
cd advanced-level/reactive-rest-api
./mvnw quarkus:dev
```

For native builds:

```bash
cd advanced-level/native-build
./mvnw package -Dnative
./target/*-runner
```
