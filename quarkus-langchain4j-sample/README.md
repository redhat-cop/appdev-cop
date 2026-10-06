# Quarkus LangChain4j Samples

Five standalone Quarkus projects, each implementing one of the official [Quarkus LangChain4j](https://docs.quarkiverse.io/quarkus-langchain4j/dev/index.html) quickstarts. Every project uses the OpenAI model provider and is runnable independently.

| Project | Quickstart | Description |
| --- | --- | --- |
| [`01-poem-cli`](01-poem-cli) | [Getting Started](https://docs.quarkiverse.io/quarkus-langchain4j/dev/quickstart.html) | CLI app that writes a poem on a given topic using a declarative AI service. |
| [`02-summarization`](02-summarization) | [Summarization](https://docs.quarkiverse.io/quarkus-langchain4j/dev/quickstart-summarization.html) | Reads a text file and outputs a structured Markdown summary. |
| [`03-image-ocr`](03-image-ocr) | [Image / OCR](https://docs.quarkiverse.io/quarkus-langchain4j/dev/quickstart-image.html) | Extracts and translates text from an image using a vision-capable model. |
| [`04-rag`](04-rag) | [RAG](https://docs.quarkiverse.io/quarkus-langchain4j/dev/quickstart-rag.html) | Retrieval-Augmented Generation over a markdown document, using `pgvector`. |
| [`05-function-calling`](05-function-calling) | [Function Calling](https://docs.quarkiverse.io/quarkus-langchain4j/dev/quickstart-function-calling.html) | AI travel planner that calls application-defined `@Tool` methods. |

## Prerequisites

- Java 21+
- An OpenAI API key, exported as an environment variable:

```shell
export OPENAI_API_KEY=sk-...
```

Each project also reads `quarkus.langchain4j.openai.api-key` from its `application.properties`, which defaults to the `OPENAI_API_KEY` environment variable.

- Docker (or Podman), only for `04-rag`, since it relies on Quarkus Dev Services to start a `pgvector`-enabled PostgreSQL container in dev/test mode.

## Running a project

Each folder is a self-contained Maven project with its own wrapper. For example:

```shell
cd 01-poem-cli
./mvnw quarkus:dev
```

See each project's own `README.md` for exact run instructions and sample commands.

## Versions used

- Quarkus platform: `3.40.1`
- Quarkus LangChain4j: `1.15.0.CR1` (via the `quarkus-langchain4j-bom`, matching the version referenced by the quickstart docs at the time of writing)
