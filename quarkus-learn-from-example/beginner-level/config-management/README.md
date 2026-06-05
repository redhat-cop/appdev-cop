# Configuration Management with SmallRye Config

Overview: this sample shows configuration in Quarkus using SmallRye Config—grouped settings with `@ConfigMapping`, individual keys with `@ConfigProperty`, and profile-specific overrides (`%dev`, `%test`, `%prod`).

You can keep this folder anywhere; if you use the layout described in the tutorial, the path is `appdev-cop/quarkus-learn-from-example/beginner-level/config-management/`.

## Create a similar app with the Quarkus CLI

```bash
quarkus create app com.example:config-management --extension='resteasy-reactive-jackson'
```

(Add `resteasy-reactive` if your generator does not pull it in transitively.)

## Run in development mode

```bash
./mvnw quarkus:dev
```

The app listens on port **8083** (see `application.properties`).

## Override configuration at runtime

Example: change the greeting message for one launch without editing files:

```bash
./mvnw quarkus:dev -Dgreeting.message="Custom Message"
```

You can also rely on environment variables (MicroProfile Config maps names like `GREETING_MESSAGE` to `greeting.message`).

## Try with curl

```bash
curl -s http://localhost:8083/config
curl -s http://localhost:8083/config/greet
curl -s http://localhost:8083/config/greet/Ada
```

## Run tests

```bash
./mvnw test
```

## Key concepts

| Topic | Notes |
|-------|--------|
| `@ConfigMapping` | Preferred in Quarkus 3.x for a type-safe group of keys under one prefix (e.g. `greeting.*`). |
| `@ConfigProperty` | Still supported; good for a single key (this demo uses it for `app.version`). |
| Profiles | Keys prefixed with `%dev.`, `%test.`, or `%prod.` apply when that profile is active (`test` is active during `@QuarkusTest`). |
| Environment | External config can override `application.properties` without code changes. |

## Maven wrapper

If `./mvnw` is missing, generate it once:

```bash
mvn -N io.takari:maven:wrapper
```

Then use `./mvnw` as above.
