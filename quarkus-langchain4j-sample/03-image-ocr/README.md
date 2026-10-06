# 03-image-ocr

Quarkus LangChain4j image quickstart: extracts text from an image using a vision-capable LLM and translates it to English.

Source: https://docs.quarkiverse.io/quarkus-langchain4j/dev/quickstart-image.html

## What it does

- `OCR` is an AI service whose `process(Image)` method takes a `dev.langchain4j.data.image.Image` and returns the extracted/translated text.
- `OCRApplication` (`@QuarkusMain`) loads `text.jpg` from the project root, base64-encodes it, and sends it to the AI service.

A sample `text.jpg` (containing a few lines of French text) is included so you can run the example out of the box.

## Configuration

Set your OpenAI API key, and make sure a vision-capable model is configured (defaults to `gpt-4o-mini` in `application.properties`):

```shell
export OPENAI_API_KEY=sk-...
```

## Running in dev mode

```shell
./mvnw quarkus:dev
```

You should see the French text extracted from `text.jpg` and translated into English, printed between `----` markers.

## Running the packaged jar

```shell
./mvnw package -DskipTests
java -jar target/quarkus-app/quarkus-run.jar
```

## Try your own image

Replace `text.jpg` in the project root with any `.jpg` containing text, or switch to the `@ImageUrl` annotation to pass a remote image URL instead of base64 data.
