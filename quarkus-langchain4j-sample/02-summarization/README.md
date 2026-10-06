# 02-summarization

Quarkus LangChain4j summarization quickstart: a CLI application that reads a plain text file and returns a structured Markdown summary (one-sentence summary, main points, takeaways).

Source: https://docs.quarkiverse.io/quarkus-langchain4j/dev/quickstart-summarization.html

## What it does

- `SummarizationService` is an AI service with a detailed `@SystemMessage` instructing the model to produce a Markdown summary with three sections.
- `Main` (`@QuarkusMain`) reads the file path passed as a program argument and prints the summary.

## Configuration

Set your OpenAI API key before running:

```shell
export OPENAI_API_KEY=sk-...
```

## Running in dev mode

A sample `article.txt` (about Quarkus) is included at the project root.

```shell
./mvnw quarkus:dev -Dquarkus.args="article.txt"
```

## Running the packaged jar

```shell
./mvnw package -DskipTests
java -jar target/quarkus-app/quarkus-run.jar article.txt
```
