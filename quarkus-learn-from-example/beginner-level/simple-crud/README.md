# simple-crud

Overview: a minimal CRUD REST API using Hibernate ORM with Panache (Active Record). `Task` extends `PanacheEntityBase`, which is the same Active Record style as `PanacheEntity`; the `id` field and `Tasks_SEQ` sequence are declared here so `import.sql` can use `nextval('Tasks_SEQ')` as in the H2 documentation (see `NEXTVAL`). With plain `PanacheEntity` you would omit this field and rely on its built-in `id`, then seed rows without referencing the sequence name. HTTP uses RESTEasy Reactive and Jackson.

## Create a similar app with the Quarkus CLI

```bash
quarkus create app com.example:simple-crud --extension='resteasy-reactive-jackson,hibernate-orm-panache,jdbc-h2'
```

## Run

```bash
./mvnw quarkus:dev
```

If your checkout has no Maven Wrapper yet, run `mvn -N io.takari:maven:wrapper` once to create `mvnw`, or use `mvn quarkus:dev`.

The HTTP port is `8081` (see `application.properties`).

## Try it with curl

List all tasks:

```bash
curl -s http://localhost:8081/tasks
```

Get one task by id (replace `1` with an id returned from the list):

```bash
curl -s http://localhost:8081/tasks/1
```

Create a task (HTTP 201 and `Location` header):

```bash
curl -s -w "\n%{http_code}\n" -X POST http://localhost:8081/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title":"Deploy to production","completed":false}'
```

Update a task:

```bash
curl -s -w "\n%{http_code}\n" -X PUT http://localhost:8081/tasks/1 \
  -H 'Content-Type: application/json' \
  -d '{"title":"Learn Quarkus basics","completed":true}'
```

Delete a task:

```bash
curl -s -w "\n%{http_code}\n" -X DELETE http://localhost:8081/tasks/1
```

## Key concepts

- **Active Record:** `Task` extends Panache’s base type so you call `Task.listAll()`, `task.persist()`, etc., instead of wiring a separate DAO/repository for basic operations.
- **`@Transactional`:** mutation endpoints on `TaskResource` run inside a transaction so Hibernate can persist changes reliably.
- **H2 in-memory database:** `jdbc:h2:mem:taskdb` keeps all data in memory; restarting the app clears it.
- **`import.sql`:** runs after schema generation to load seed rows. The sequence `Tasks_SEQ` is created because the entity maps the primary key to that sequence name.
