# Beginner Level Examples

This folder contains introductory Quarkus examples covering the fundamentals: REST endpoints, CRUD with a database, dependency injection, configuration management, and testing.

## Examples

| Folder | Example | Key Concepts |
|---|---|---|
| `hello-world/` | Hello World REST API | JAX-RS `@Path`, `@GET`, RESTEasy Reactive, Dev Mode |
| `simple-crud/` | CRUD with Panache | `PanacheEntity`, Active Record pattern, `@Transactional`, H2 |
| `dependency-injection/` | Dependency Injection (CDI) | `@ApplicationScoped`, `@Inject`, ArC build-time DI |
| `config-management/` | Configuration Management | `@ConfigMapping`, `@ConfigProperty`, profiles (`%dev`, `%prod`) |
| `testing-quarkus/` | Testing with @QuarkusTest | REST Assured, `@InjectMock`, unit vs integration tests |

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

> **Note:** If the Maven wrapper (`mvnw`) is not present, generate it with `mvn -N wrapper:wrapper` or use `mvn` directly.
