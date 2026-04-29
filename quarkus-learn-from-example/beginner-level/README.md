# Beginner Level Examples

This folder contains introductory Quarkus examples covering the fundamentals: REST endpoints, configuration, JSON handling, validation, health checks, error handling, templates, and Dev Services.

## Examples

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

## How to Run

Each subfolder is a self-contained Quarkus project. Navigate into any folder, read its README, and run:

```bash
cd beginner-level/hello-world
./mvnw quarkus:dev
```

Then test with:

```bash
curl http://localhost:8080/hello
```
