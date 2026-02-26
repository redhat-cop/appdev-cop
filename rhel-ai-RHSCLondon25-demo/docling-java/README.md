
# Docling Java example

Create your blank java project

```bash
mvn archetype:generate \
  -DgroupId=org.appdev.cop.pamenon \
  -DartifactId=docling-java-cli \
  -DarchetypeArtifactId=maven-archetype-quickstart \
  -DarchetypeVersion=1.4 \
  -DinteractiveMode=false
```
## Pre requirements

Add the depenencies to your pom file:


## Run

```bash
java -jar target/docling-java-cli-1.0.0-SNAPSHOT.jar-with-dependencies.jar artifacts Red_Hat_Enterprise_Linux_AI-3.2-Installing-en-US.pdf
```

