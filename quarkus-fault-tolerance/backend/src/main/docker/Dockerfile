## Stage 1 : build with maven builder image with native capabilities
FROM quay.io/quarkus/ubi9-quarkus-mandrel-builder-image:jdk-21 AS build
COPY --chown=quarkus:quarkus --chmod=0755 mvnw /code/mvnw
COPY --chown=quarkus:quarkus .mvn /code/.mvn
COPY --chown=quarkus:quarkus pom.xml /code/
USER quarkus
WORKDIR /code
RUN ./mvnw -B org.apache.maven.plugins:maven-dependency-plugin:3.8.1:go-offline
COPY src /code/src
RUN ./mvnw package -Dnative -DskipTests=true

## Stage 2 : create the docker final image
FROM quay.io/quarkus/ubi9-quarkus-micro-image:2.0
COPY --from=build --chown=1001:1001 --chmod=777 /code/target/*-runner /work/application
RUN chmod -R 777 /work

USER 1001
WORKDIR /work/
EXPOSE 8080

CMD ["./application", "-Dquarkus.http.host=0.0.0.0"]

