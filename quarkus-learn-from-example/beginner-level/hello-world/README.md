# Hello World REST API (Quarkus)

## Overview

This example shows how to expose your first HTTP endpoints with Quarkus using **RESTEasy Reactive** (Jakarta REST on a reactive stack). You get two GET routes: a fixed greeting and a personalized greeting with a path parameter.

## Create a similar project with the Quarkus CLI

```bash
quarkus create app com.example:hello-world --extension='resteasy-reactive'
```

## Run in development mode

From this directory:

```bash
./mvnw quarkus:dev
```

If you do not use the Maven Wrapper, use `mvn quarkus:dev` instead.

## Try it with curl

```bash
curl http://localhost:8080/hello
curl http://localhost:8080/hello/World
```

## Run tests

```bash
./mvnw test
```

## Key concepts

- **JAX-RS annotations** (`@Path`, `@GET`, `@Produces`, path templates like `{name}`) declare the URL shape and HTTP method. Quarkus registers the resource and wires it to the server.
- **Dev Mode** (`quarkus:dev`) keeps the app running and reloads changes to Java and resources so you can iterate without restarting the JVM for every edit.
