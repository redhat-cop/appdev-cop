# testing-quarkus

Overview: small Quarkus 3.x app demonstrating **@QuarkusTest** (full application for HTTP and CDI), **REST Assured** (given / when / then), **plain JUnit** unit tests for services, and **@InjectMock** for replacing beans in integration tests.

If you keep course material under another root (for example `~/Projects/paulo/workspace/appdev-cop/quarkus-learn-from-example/beginner-level/`), copy this entire `testing-quarkus` folder there so paths match your notes.

## Run tests

```bash
./mvnw test
```

Run a single test class:

```bash
./mvnw test -Dtest=GreetingResourceTest
```

## Key concepts

- **@QuarkusTest** starts the application for the test suite so endpoints, injection, and configuration behave like runtime (integration-style tests).
- **REST Assured** models HTTP with `given` (request), `when` (verb and path), `then` (assertions).
- **@InjectMock** supplies Mockito mocks in place of CDI beans when you want to control collaborators.
- **Plain unit tests** (no `@QuarkusTest`) are fastest for pure logic; use `@QuarkusTest` when the framework or network boundary must be real.
- **Continuous testing in dev mode**: run `./mvnw quarkus:dev`, then press `r` in the terminal to re-run tests after changes.

Default HTTP port for `quarkus:dev` is set to **8084** in `application.properties`. Tests use Quarkus test HTTP configuration (not necessarily that port).

## Requirements

Java 17 and Maven (or use the included Maven Wrapper after generation).
