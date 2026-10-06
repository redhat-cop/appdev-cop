# 01-poem-cli

Quarkus LangChain4j "Getting Started" quickstart: a CLI application that generates poems using an AI model.

Source: https://docs.quarkiverse.io/quarkus-langchain4j/dev/quickstart.html

## What it does

- Declares an `MyAiService` AI service (`@RegisterAiService`) with a system message ("You are a professional poet") and a `writeAPoem(topic, lines)` method.
- Exposes it through a Picocli command (`PoemCommand`) so you can ask for a poem from the command line.

## Configuration

Set your OpenAI API key before running, either in `src/main/resources/application.properties` or via an environment variable:

```shell
export OPENAI_API_KEY=sk-...
```

## Running in dev mode

```shell
./mvnw quarkus:dev
```

Then, in another terminal, run the packaged command (dev mode continues to serve the CLI through the Quarkus dev process, but once packaged you can invoke it directly):

```shell
./mvnw package -DskipTests
java -jar target/quarkus-app/quarkus-run.jar --lines=5 "AI with Quarkus"
```

Example output:

```
In the realm of code and light,
Quarkus dances, swift and bright,
AI whispers in the breeze,
Crafting dreams with agile ease,
Future's song in bytes takes flight.
```

## Native executable

```shell
./mvnw package -Dnative
./target/*-runner --lines=5 "Quarkus poetry"
```
