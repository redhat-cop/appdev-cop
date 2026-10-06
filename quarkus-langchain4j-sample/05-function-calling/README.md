# 05-function-calling

Quarkus LangChain4j function calling quickstart: an AI travel planner that calls application-defined tools (functions) to decide what to recommend.

Source: https://docs.quarkiverse.io/quarkus-langchain4j/dev/quickstart-function-calling.html

## What it does

- `TripTools` is a toolbox: a CDI bean exposing two `@Tool`-annotated methods (`weather(location)` and `activity(weather)`) that the LLM may call.
- `TravelPlanner` is an AI service whose `plan(destination)` method is annotated with `@ToolBox(TripTools.class)`, allowing the model to call `weather` and `activity` while reasoning about the user's request.
- `TripCommand` is a Picocli command that injects `TravelPlanner` and prints its answer.

The model will typically:
1. Analyze the destination.
2. Call `weather(destination)`.
3. Use the result to call `activity(weather)`.
4. Combine both results into a natural-language reply.

## Configuration

Set your OpenAI API key:

```shell
export OPENAI_API_KEY=sk-...
```

## Running in dev mode

```shell
./mvnw quarkus:dev
```

## Running the packaged jar

```shell
./mvnw package -DskipTests
java -jar target/quarkus-app/quarkus-run.jar Barcelona
java -jar target/quarkus-app/quarkus-run.jar Paris
```
