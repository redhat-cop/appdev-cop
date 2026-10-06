# Reactive REST API

## Overview

This example shows a **fully reactive** REST stack with Quarkus:

- **RESTEasy Reactive** for non-blocking HTTP
- **Hibernate Reactive Panache** for database access
- **Mutiny** (`Uni<T>`, `Multi<T>`) as the reactive type throughout

An in-memory PostgreSQL instance (via Dev Services) backs the `Movie` entity. Seed data is loaded from `import.sql`.

## Prerequisites

- JDK 17
- Podman or Docker (for PostgreSQL Dev Service)

```bash
podman machine start
```

## Run the application

```bash
cd reactive-rest-api
./mvnw quarkus:dev
```

The HTTP server listens on port **8091**.

## Try it with curl

List all movies (includes three seed rows):

```bash
curl -s http://localhost:8091/movies
```

Get one movie by id:

```bash
curl -s http://localhost:8091/movies/1
```

Create a movie:

```bash
curl -s -X POST http://localhost:8091/movies \
  -H 'Content-Type: application/json' \
  -d '{"title":"Dune","director":"Denis Villeneuve","year":2021}'
```

## Key concepts

- **`Uni<T>`**: a single asynchronous result (e.g. one entity lookup).
- **`Multi<T>`**: a stream of items (e.g. listing all movies as a reactive stream).
- **`@WithTransaction`**: opens a reactive transaction for write operations (replaces `@Transactional` in the reactive stack).
- **End-to-end reactive**: the request thread is not blocked while waiting on I/O.

## Tests

```bash
./mvnw test
```
