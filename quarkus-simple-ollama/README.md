# Simple integration of a Quarkus app with Ollama

In this example a very basic integration between a Quarkus application and Ollama serving the `llama3.1` model is demonstrated.

> NOTE: The integration does not depend on a particular model, `llama3.1` is used here just as an example

Ollama is executed by podman and the Quarkus app poses a question. The answer is displayed in the web page and in the stdout. 
In this basic example modifying the question requires modifying the source code, but the simplicity of the code helps to clarify the bare basics needed for Ollama integration.


## Initialise Ollama in podman

Using the official ollama image from docker [ollama/ollama - Docker Image | Docker Hub](https://hub.docker.com/r/ollama/ollama) a podman container is started, as in:

```
podman run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
```

and the `llama3.1` model is pulled and serve with

```
podman exec -it ollama ollama run llama3.1
```

> NOTE: The combined size of ollama and the LLM model could be in excess of 5GB, which would need to be downloaded, so please keep that in mind if you're serving the LLM for the first time

After everything is downloaded, you should be greeted with a prompt. You can use this prompt to interact directly with the `llama3.1` model or you can use the Quarkus application.


## Running the application

Out of the many ways to run a Quarkus application the simplest one will be used as an example here. Under JDK21 execute the following:

```
mvn clean quarkus:dev
```

and navigate to http://localhost:8080/start or if would like a more personalised respone add the `name` parameter in the URL as in http://localhost:8080/start?name=Daneel+Olivaw

The application will then try to reach out to the LLM model served by Ollama using the `11434` port and display the answer. The answer will also be written to stdout.

That's all there is to it!

Press `q` in the terminal were the application was started to quit the application.


## Stop serving the LLM model

Typing `/bye` in the ollama prompt will terminate the interactive session whilst executing

```
podman stop ollama
```

Will terminate the podman `ollama` container.


## More about Quarkus

This project uses Quarkus, the Supersonic Subatomic Java Framework.

If you want to learn more about Quarkus, please visit its website: https://quarkus.io/ .

### Running the application in dev mode

You can run your application in dev mode that enables live coding using:
```shell script
./mvnw compile quarkus:dev
```

> **_NOTE:_**  Quarkus now ships with a Dev UI, which is available in dev mode only at http://localhost:8080/q/dev/.

### Packaging and running the application

The application can be packaged using:
```shell script
./mvnw package
```
It produces the `quarkus-run.jar` file in the `target/quarkus-app/` directory.
Be aware that it’s not an _über-jar_ as the dependencies are copied into the `target/quarkus-app/lib/` directory.

The application is now runnable using `java -jar target/quarkus-app/quarkus-run.jar`.

If you want to build an _über-jar_, execute the following command:
```shell script
./mvnw package -Dquarkus.package.jar.type=uber-jar
```

The application, packaged as an _über-jar_, is now runnable using `java -jar target/*-runner.jar`.

### Creating a native executable

You can create a native executable using: 
```shell script
./mvnw package -Dnative
```

Or, if you don't have GraalVM installed, you can run the native executable build in a container using: 
```shell script
./mvnw package -Dnative -Dquarkus.native.container-build=true
```

You can then execute your native executable with: `./target/quarkus-simple-ollama-1.0.0-SNAPSHOT-runner`

If you want to learn more about building native executables, please consult https://quarkus.io/guides/maven-tooling.

### Related Guides

- REST Qute ([guide](https://quarkus.io/guides/qute-reference#rest_integration)): Qute integration for Quarkus REST. This extension is not compatible with the quarkus-resteasy extension, or any of the extensions that depend on it.
- Create your web page using Quarkus REST and Qute: [Related guide section...](https://quarkus.io/guides/qute#type-safe-templates)

