# 04-rag

Quarkus LangChain4j Retrieval-Augmented Generation (RAG) quickstart: answers questions using content retrieved from a markdown document, stored as embeddings in `pgvector`.

Source: https://docs.quarkiverse.io/quarkus-langchain4j/dev/quickstart-rag.html

## What it does

- `docs/quarkus-overview.md` is the knowledge source (a short overview of Quarkus).
- `DocumentLoader` (`@Startup`) ingests that document on application startup: it splits it into 500-character segments and stores their embeddings in the `pgvector` embedding store.
- `DocumentRetriever` implements `RetrievalAugmentor`, retrieving the top 3 most relevant segments for a given question at inference time.
- `DocumentationAssistant` is the AI service that answers questions, automatically augmented with the retrieved context.
- `RAGApp` (`@QuarkusMain`) asks a default question ("How does Quarkus achieve fast startup times?") or one supplied on the command line.

## Configuration

Set your OpenAI API key:

```shell
export OPENAI_API_KEY=sk-...
```

In **dev and test mode**, Quarkus Dev Services automatically starts a PostgreSQL container with the `pgvector` extension enabled - nothing else to configure.

In **prod mode**, you must run a PostgreSQL instance with the pgvector extension and set the datasource properties in `application.properties` (see the commented example).

## Running in dev mode

```shell
./mvnw quarkus:dev
```

## Running the packaged jar (prod mode)

Start a PostgreSQL database with pgvector enabled, e.g.:

```shell
docker run -d --name rag-pgvector -p 5432:5432 \
  -e POSTGRES_USER=quarkus -e POSTGRES_PASSWORD=quarkus -e POSTGRES_DB=rag \
  pgvector/pgvector:pg16
```

Then build and run:

```shell
./mvnw clean package -DskipTests
java -jar target/quarkus-app/quarkus-run.jar "How does Quarkus achieve fast startup times?"
```
