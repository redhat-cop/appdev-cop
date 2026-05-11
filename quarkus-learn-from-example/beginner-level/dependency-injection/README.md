# Dependency injection with Quarkus ArC

This example shows **dependency injection** in Quarkus using **ArC**, the build-time CDI container. Managed beans are plain classes annotated with CDI scopes; resources and other beans declare dependencies with `@Inject`, and ArC wires them when the application starts.

In this workspace the project lives at `quarkus-learn-from-example/beginner-level/dependency-injection/`. To match a layout such as `appdev-cop/quarkus-learn-from-example/beginner-level/`, copy that directory to the path you want, for example:

```bash
cp -R quarkus-learn-from-example/beginner-level/dependency-injection \
  /path/to/appdev-cop/quarkus-learn-from-example/beginner-level/
```

## Create a similar app with the Quarkus CLI

```bash
quarkus create app com.example:dependency-injection --extension='resteasy-reactive'
```

## Run

If this directory does not yet include the Maven Wrapper, generate it once (Maven 3.9+):

```bash
mvn -N wrapper:wrapper -DwrapperVersion=3.3.2
```

Then:

```bash
./mvnw quarkus:dev
```

If you prefer not to use the wrapper, run:

```bash
mvn quarkus:dev
```

The app listens on port **8082** (see `src/main/resources/application.properties`).

## Try it with curl

```bash
curl -s http://localhost:8082/greet/World
curl -s http://localhost:8082/greet/farewell/World
curl -s http://localhost:8082/greet/count
```

## Key concepts

- **`@ApplicationScoped`**: One shared bean instance for the application; lazy creation on first use; typical for stateless services.
- **`@Inject`**: Declares a dependency; ArC injects a managed instance (constructor, field, or method injection).
- **Other scopes (overview)**:
  - **Request**: One instance per HTTP request (common for per-request state).
  - **Application**: Same idea as `@ApplicationScoped` in typical Quarkus usage (single shared instance for the app).
  - **Singleton**: In CDI, `@Singleton` is similar to application scope but with eager initialization semantics; in Quarkus you usually prefer `@ApplicationScoped`.
- **ArC build-time DI**: Quarkus resolves many injection points and bean graphs at build time, which catches wiring errors early and reduces runtime overhead.

## Test

```bash
./mvnw test
```

or `mvn test` without the wrapper.
