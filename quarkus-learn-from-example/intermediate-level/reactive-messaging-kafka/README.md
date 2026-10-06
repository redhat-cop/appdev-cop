# Reactive Messaging with Kafka

## Overview

This example shows **SmallRye Reactive Messaging** with Kafka. A REST endpoint publishes `Quote` messages to a Kafka topic; a consumer bean logs each message as it arrives.

In Dev Mode, Quarkus **Dev Services** starts a Kafka broker automatically (requires Podman or Docker).

## Prerequisites

- JDK 17
- Podman or Docker (for Kafka Dev Service)

```bash
podman machine start
```

## Run the application

```bash
cd reactive-messaging-kafka
./mvnw quarkus:dev
```

## Try it with curl

Publish a quote to Kafka:

```bash
curl -s -X POST http://localhost:8080/quotes \
  -H 'Content-Type: application/json' \
  -d '{"author":"Kafka","text":"Publish early, publish often."}'
```

Watch the application logs for the consumer output:

```
Received quote from Kafka: "Publish early, publish often."
```

## Key concepts

- **`@Channel` + `Emitter`**: send messages to an outgoing channel from imperative code (e.g. a REST resource).
- **`@Incoming`**: subscribe to a channel and process messages reactively.
- **Kafka connector**: `smallrye-kafka` maps channels to topics via `application.properties`.
- **Dev Services**: zero-config Kafka broker in development and tests.

## Tests

```bash
./mvnw test
```
