# Panache ORM (Active Record)

## Overview

This example shows Hibernate ORM with the **Panache Active Record** programming model. Entities extend `PanacheEntity` and inherit convenient static methods for persistence (`listAll`, `findById`, `persist`, and so on), so you write less boilerplate than with plain JPA.

An in-memory H2 database backs the `Fruit` entity. Seed data is loaded from `import.sql`.

## Prerequisites

- JDK 17
- Apache Maven 3.8+

## Run the application

```bash
cd panache-orm
./mvnw quarkus:dev
```

The HTTP server listens on port **8090**.

## Try it with curl

List all fruits (includes three seed rows):

```bash
curl -s http://localhost:8090/fruits
```

Get one fruit by id:

```bash
curl -s http://localhost:8090/fruits/1
```

Create a fruit:

```bash
curl -s -X POST http://localhost:8090/fruits \
  -H 'Content-Type: application/json' \
  -d '{"name":"Pear","season":"Late Summer"}'
```

Update a fruit:

```bash
curl -s -X PUT http://localhost:8090/fruits/1 \
  -H 'Content-Type: application/json' \
  -d '{"name":"Honeycrisp Apple","season":"Fall"}'
```

Delete a fruit:

```bash
curl -s -X DELETE http://localhost:8090/fruits/1
```

## Key concepts

- **Panache Active Record**: put persistence operations on the entity type (`Fruit.listAll()`, `Fruit.findById(id)`, `fruit.persist()`).
- **`@Transactional` on resources**: mutating endpoints run inside a transaction.
- **`import.sql`**: loaded after schema generation when `quarkus.hibernate-orm.sql-load-script` is set.

## Tests

```bash
./mvnw test
```
